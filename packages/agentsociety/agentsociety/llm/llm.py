import asyncio
import datetime
import os
import random
import time
from enum import Enum
from multiprocessing import cpu_count
from typing import Any, List, Optional, Union, overload, TypedDict

import httpx
from ..database.database_actor import DatabaseActor
from ..performance.prometheusActor import PrometheusActor
import ray
from openai import NOT_GIVEN, APIConnectionError, AsyncOpenAI, NotGiven, OpenAIError
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)
from pydantic import BaseModel, Field, field_serializer, model_validator

from ..logger import get_logger

os.environ["GRPC_VERBOSITY"] = "ERROR"

__all__ = [
    "LLM",
    "LLMConfig",
    "LLMProviderType",
]

MAX_TIMEOUT = 300


class LLMContext(TypedDict, total=False):
    block_name: str
    func_name: str
    agent_id: str


class LLMProviderType(str, Enum):
    """
    Defines the types of LLM providers.
    - **Description**:
        - Enumerates different types of LLM providers.

    - **Types**:
        - `OPENAI`: OpenAI and compatible providers (based on base_url).
        - `DEEPSEEK`: DeepSeek.
        - `QWEN`: Qwen.
        - `ZHIPU`: Zhipu.
        - `SILICONFLOW`: SiliconFlow.
        - `VLLM`: VLLM.
    """

    OpenAI = "openai"
    DeepSeek = "deepseek"
    Qwen = "qwen"
    ZhipuAI = "zhipuai"
    SiliconFlow = "siliconflow"
    VolcEngine = "volcengine"
    VLLM = "vllm"


class LLMConfig(BaseModel):
    """LLM configuration class."""

    provider: LLMProviderType = Field(...)
    """The type of the LLM provider"""

    base_url: Optional[str] = Field(None)
    """The base URL for the LLM provider"""

    api_key: str = Field(...)
    """API key for accessing the LLM provider"""

    model: str = Field(...)
    """The model to use"""

    concurrency: int = Field(200, ge=1)
    """Concurrency value for LLM operations to avoid rate limit"""

    timeout: float = Field(120, ge=1, le=MAX_TIMEOUT)
    """Timeout for LLM operations in seconds"""

    @field_serializer("provider")
    def serialize_provider(self, provider: LLMProviderType, info):
        return provider.value

    @model_validator(mode="after")
    def validate_configuration(self):
        if self.provider != LLMProviderType.VLLM and self.base_url is not None:
            raise ValueError("base_url is not supported for this provider")
        return self


def _convert_system_role_to_user(
    dialog: list[ChatCompletionMessageParam],
) -> list[ChatCompletionMessageParam]:
    """
    Convert system role messages to user messages for providers that don't support system role.
    Merges consecutive system and user messages.

    Args:
        dialog: Original dialog with potential system role messages

    Returns:
        Modified dialog with system messages converted to user messages
    """
    if not dialog:
        return dialog

    converted = []
    i = 0

    while i < len(dialog):
        msg = dialog[i]

        # If it's a system message
        if msg.get("role") == "system":
            system_content = msg.get("content", "")

            # Check if next message is a user message
            if i + 1 < len(dialog) and dialog[i + 1].get("role") == "user":
                # Merge system message into user message
                user_content = dialog[i + 1].get("content", "")
                merged_content = f"{system_content}\n\n{user_content}"
                converted.append({"role": "user", "content": merged_content})
                i += 2  # Skip both messages
            else:
                # Convert system message to user message
                converted.append({"role": "user", "content": system_content})
                i += 1
        else:
            # Keep non-system messages as is
            converted.append(msg)
            i += 1

    return converted


@ray.remote(concurrency_groups={"default": 500})
class LLMActor:
    """
    Actor class for LLM operations.
    """

    def __init__(self, provider: Optional[str] = None):
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=min(30.0, MAX_TIMEOUT / 4),  # 连接超时时间
                read=MAX_TIMEOUT,  # 读取超时时间
                write=MAX_TIMEOUT,  # 写入超时时间
                pool=MAX_TIMEOUT,  # 连接池超时时间
            ),
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0
            ),
        )

        # VLLM and some models don't support system roles well
        self.support_system_role = (
            provider
            not in [
                LLMProviderType.VLLM.value,
                LLMProviderType.DeepSeek.value,
            ]
            if provider
            else False
        )

    

    async def call(
        self,
        config: LLMConfig,
        dialog: list[ChatCompletionMessageParam],
        response_format: Union[
            completion_create_params.ResponseFormat, NotGiven
        ] = NOT_GIVEN,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        timeout: int = 300,
        retries: int = 10,
        tools: Union[List[ChatCompletionToolParam], NotGiven] = NOT_GIVEN,
        tool_choice: Union[ChatCompletionToolChoiceOptionParam, NotGiven] = NOT_GIVEN,
        client_index: int = 0,
    ):
        """
        Sends an asynchronous text request to the configured LLM API.

        - **Description**:
            - Attempts to send a text request up to `retries` times with exponential backoff on failure.
            - Handles different request types and manages token usage statistics.

        - **Args**:
            - `config`: LLM configuration.
            - `dialog`: Messages to send as part of the chat completion request.
            - `response_format`: JSON schema for the response. Default is NOT_GIVEN.
            - `temperature`: Controls randomness in the model's output. Default is 1.
            - `max_tokens`: Maximum number of tokens to generate in the response. Default is None.
            - `top_p`: Limits the next token selection to a subset of tokens with a cumulative probability above this value. Default is None.
            - `frequency_penalty`: Penalizes new tokens based on their existing frequency in the text so far. Default is None.
            - `presence_penalty`: Penalizes new tokens based on whether they appear in the text so far. Default is None.
            - `timeout`: Request timeout in seconds. Default is 300 seconds.
            - `retries`: Number of retry attempts in case of failure. Default is 10.
            - `tools`: List of dictionaries describing the tools that can be called by the model. Default is NOT_GIVEN.
            - `tool_choice`: Dictionary specifying how the model should choose from the provided tools. Default is NOT_GIVEN.
            - `client_index`: Index of the client configuration being used (for logging).

        - **Returns**:
            - A tuple of (success: bool, result: Any, log: dict)
            - If success=True: result is the response content/object
            - If success=False: result is the error message string
            - log always contains metadata including should_cooldown flag
        """

        start_time = time.time()

        log = {
            "request_time": start_time,
            "total_errors": 0,
            "error_types": {
                "connection_error": 0,
                "openai_error": 0,
                "timeout_error": 0,
                "other_error": 0,
            },
            "input_tokens": 0,
            "output_tokens": 0,
            "should_cooldown": False,  # Flag to indicate server should be put on cooldown
        }

        # Track consecutive critical errors during retries
        consecutive_critical_errors = 0
        max_consecutive_before_failfast = 3

        client = AsyncOpenAI(
            api_key=config.api_key,
            timeout=config.timeout,
            base_url=config.base_url,
            http_client=self._http_client,
        )

        for attempt in range(retries):
            response = None
            try:
                if not self.support_system_role:
                    dialog = _convert_system_role_to_user(dialog)

                response = await client.chat.completions.create(
                    model=config.model,
                    messages=dialog,
                    response_format=response_format,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stream=False,
                    timeout=timeout,
                    tools=tools,
                    tool_choice=tool_choice,
                )

                if response.usage is not None:
                    log["input_tokens"] += response.usage.prompt_tokens
                    log["output_tokens"] += response.usage.completion_tokens
                else:
                    get_logger().warning(f"No usage in response: {response}")

                end_time = time.time()
                log["consumption"] = end_time - start_time

                if tools:
                    return (True, response, log)
                else:
                    content = response.choices[0].message.content
                    if content is None:
                        raise ValueError("No content in response")

                    # Validate non-empty response
                    if not content or content.strip() in ["{}", "{", ""]:
                        raise ValueError(
                            f"Empty or invalid response from vLLM: {content}"
                        )

                    return (True, content, log)

            except ValueError as e:
                error_msg = str(e)
                if "vLLM" in error_msg or "Empty" in error_msg:
                    get_logger().warning(
                        f"vLLM response error: {error_msg}. Retry {attempt+1} of {retries}"
                    )
                    log["total_errors"] += 1
                    log["error_types"]["other_error"] += 1
                    if attempt < retries - 1:
                        await asyncio.sleep(random.random() * 2**attempt)
                    else:
                        raise e
                else:
                    raise e
            except APIConnectionError as e:
                consecutive_critical_errors += 1
                get_logger().warning(
                    f"GPU {client_index} - API connection error {consecutive_critical_errors}/{max_consecutive_before_failfast}: `{e}`. Retry {attempt+1} of {retries}"
                )
                log["total_errors"] += 1
                log["error_types"]["connection_error"] += 1
                
                # Fail-fast if too many consecutive critical errors
                if consecutive_critical_errors >= max_consecutive_before_failfast:
                    log["should_cooldown"] = True
                    get_logger().error(
                        f"GPU {client_index} ({config.base_url}) - {consecutive_critical_errors} consecutive connection errors. Triggering fail-fast."
                    )
                    return (False, str(e), log)
                
                if attempt < retries - 1:
                    await asyncio.sleep(random.random() * 2**attempt)
                else:
                    log["should_cooldown"] = True
                    return (False, str(e), log)
            except OpenAIError as e:
                error_message = str(e)

                if "System role not supported".lower() in error_message.lower():
                    get_logger().warning(
                        f"LLM provider does not support system role. Converting system messages to user messages and retrying. Original error: `{e}` for request {dialog} {tools} {tool_choice}. Retry {attempt+1} of {retries}"
                    )
                    dialog = _convert_system_role_to_user(dialog)
                    self.support_system_role = False
                    continue  # Retry immediately with modified dialog

                # Check for JSON-related errors
                if "json" in error_message.lower() or "format" in error_message.lower():
                    get_logger().error(
                        f"JSON parsing error from LLM: {error_message}. Response content: {response.choices[0].message.content if response and response.choices else 'N/A'}. Retry {attempt+1} of {retries}"
                    )

                # Check for critical errors that should trigger cooldown
                is_critical = any(keyword in error_message.lower() for keyword in ["connection", "404", "503", "502", "timeout"])
                if is_critical:
                    consecutive_critical_errors += 1
                    get_logger().warning(
                        f"GPU {client_index} - Critical OpenAI error {consecutive_critical_errors}/{max_consecutive_before_failfast}: {error_message}. Retry {attempt+1} of {retries}"
                    )
                    
                    if consecutive_critical_errors >= max_consecutive_before_failfast:
                        log["should_cooldown"] = True
                        get_logger().error(
                            f"GPU {client_index} ({config.base_url}) - {consecutive_critical_errors} consecutive critical errors. Triggering fail-fast."
                        )
                        return (False, str(e), log)
                else:
                    consecutive_critical_errors = 0  # Reset on non-critical error
                    get_logger().warning(
                        f"OpenAIError: {error_message} for request {dialog} {tools} {tool_choice}. original response: `{response}`. Retry {attempt+1} of {retries}"
                    )

                log["total_errors"] += 1
                log["error_types"]["openai_error"] += 1
                if attempt < retries - 1:
                    await asyncio.sleep(random.random() * 2**attempt)
                else:
                    if is_critical:
                        log["should_cooldown"] = True
                    return (False, str(e), log)
            except asyncio.TimeoutError as e:
                consecutive_critical_errors += 1
                get_logger().warning(
                    f"GPU {client_index} - Timeout error {consecutive_critical_errors}/{max_consecutive_before_failfast}: `{e}`. Retry {attempt+1} of {retries}"
                )
                log["total_errors"] += 1
                log["error_types"]["timeout_error"] += 1
                
                if consecutive_critical_errors >= max_consecutive_before_failfast:
                    log["should_cooldown"] = True
                    get_logger().error(
                        f"GPU {client_index} ({config.base_url}) - {consecutive_critical_errors} consecutive timeouts. Triggering fail-fast."
                    )
                    return (False, str(e), log)
                
                if attempt < retries - 1:
                    await asyncio.sleep(random.random() * 2**attempt)
                else:
                    log["should_cooldown"] = True
                    return (False, str(e), log)
            except Exception as e:
                error_str = str(e).lower()
                is_critical = any(keyword in error_str for keyword in ["connection", "failed to get response", "404", "503", "502"])
                
                if is_critical:
                    consecutive_critical_errors += 1
                    get_logger().warning(
                        f"GPU {client_index} - Critical error {consecutive_critical_errors}/{max_consecutive_before_failfast}: `{e}`. Retry {attempt+1} of {retries}"
                    )
                    
                    if consecutive_critical_errors >= max_consecutive_before_failfast:
                        log["should_cooldown"] = True
                        get_logger().error(
                            f"GPU {client_index} ({config.base_url}) - {consecutive_critical_errors} consecutive critical errors. Triggering fail-fast."
                        )
                        return (False, str(e), log)
                else:
                    consecutive_critical_errors = 0
                    get_logger().warning(
                        f"LLM Error: `{e}` for request {dialog} {tools} {tool_choice}. original response: `{response}`. Retry {attempt+1} of {retries}"
                    )
                
                log["total_errors"] += 1
                log["error_types"]["other_error"] += 1
                if attempt < retries - 1:
                    await asyncio.sleep(random.random() * 2**attempt)
                else:
                    if is_critical:
                        log["should_cooldown"] = True
                    return (False, str(e), log)
        
        # All retries exhausted
        log["should_cooldown"] = True
        error_msg = f"GPU {client_index} - Failed to get response from LLM after {retries} attempts"
        get_logger().error(error_msg)
        return (False, error_msg, log)


class LLM:
    """
    Main class for the Large Language Model (LLM) object used by Agent(Soul).

    - **Description**:
        - This class manages configurations and interactions with different large language model APIs.
        - It initializes clients based on the specified request type and handles token usage and consumption reporting.
    """

    def __init__(
        self,
        configs: List[LLMConfig],
        num_actors: int = max(cpu_count() * 2, 32),
        metrics_actor: Optional[PrometheusActor] = None,
        db_actor: Optional[DatabaseActor] = None,
    ):
        """
        Initializes the LLM instance.

        - **Parameters**:
            - `configs`: An instance of `LLMConfig` containing configuration settings for the LLM.
            - `num_actors` (`int`): Number of actor instances to create for parallel processing.
              Defaults to max(cpu_count() * 2, 32) to support high-concurrency workloads.
              For 1000+ agents, consider increasing to 64+ actors.
        """

        if len(configs) == 0:
            raise ValueError(
                "No LLM config is provided, please check your configuration"
            )

        self.configs = configs

        # LOAD BALANCING LOGIC
        self._active_requests = [0] * len(
            configs
        )  # Track active requests per config for load balancing
        self._cooldown_until = [0.0] * len(configs)  # Track cooldown for server that are not working properly
        self._consecutive_failures = [0] * len(configs)  # Track consecutive failures per server
        self.cooldown_duration = 300  # 5 minutes
        self.max_consecutive_failures = 3  # Trigger cooldown after 3 consecutive failures
        self._routing_condition = (
            asyncio.Condition()
        )  # Condition variable to manage routing and load balancing
        self._last_all_servers_down_warning = 0.0  # Track last warning time when all servers are down
        self._all_servers_down_log_interval = 300.0  # Log every 5 minutes when all servers are down

        self._semaphores = [
            asyncio.Semaphore(config.concurrency) for config in self.configs
        ]
        self._log_list = []
        self.prompt_tokens_used = 0
        self.completion_tokens_used = 0
        self._next_index = 0
        self._last_show_time = time.time()
        self._metrics_actor = metrics_actor
        self._db_actor = db_actor

        for config in self.configs:
            base_url = config.base_url
            if base_url is not None:
                base_url = base_url.rstrip("/")

            if config.provider == LLMProviderType.OpenAI:
                ...
            elif config.provider == LLMProviderType.DeepSeek:
                base_url = "https://api.deepseek.com/v1"
            elif config.provider == LLMProviderType.Qwen:
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            elif config.provider == LLMProviderType.SiliconFlow:
                base_url = "https://api.siliconflow.cn/v1"
            elif config.provider == LLMProviderType.VLLM:
                ...
            elif config.provider == LLMProviderType.ZhipuAI:
                base_url = "https://open.bigmodel.cn/api/paas/v4/"
            elif config.provider == LLMProviderType.VolcEngine:
                base_url = "https://ark.cn-beijing.volces.com/api/v3/"
            else:
                raise ValueError(f"Unsupported `provider` {config.provider}!")
            config.base_url = base_url

        # Pass provider info to actors so they can configure system role support
        # Use first config's provider for all actors (assumes homogeneous setup)
        provider = self.configs[0].provider.value if self.configs else None
        self._actors = [LLMActor.remote(provider=provider) for _ in range(num_actors)]
        self._lock = asyncio.Lock()

    async def _health_check(self, client_i: int) -> bool:
        """
        Perform a health check on a server after it comes out of cooldown.
        
        Args:
            client_i: Index of the server to check
            
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            # Simple health check with minimal dialog
            test_dialog = [{"role": "user", "content": "Hi"}]
            actor_i = self._get_index() % len(self._actors)
            
            success, result, log = await self._actors[actor_i].call.remote(
                self.configs[client_i],
                test_dialog,
                temperature=0.1,
                max_tokens=10,
                timeout=30,
                retries=1,
                client_index=client_i,
            )
            
            if success:
                get_logger().info(
                    f"✅ GPU {client_i} ({self.configs[client_i].base_url}) - Health check PASSED"
                )
                return True
            else:
                get_logger().warning(
                    f"❌ GPU {client_i} ({self.configs[client_i].base_url}) - Health check FAILED: {result[:100]}"
                )
                return False
        except Exception as e:
            get_logger().warning(
                f"❌ GPU {client_i} ({self.configs[client_i].base_url}) - Health check ERROR: {str(e)[:100]}"
            )
            return False

    def get_log_list(self):
        return self._log_list

    def clear_log_list(self):
        self._log_list = []

    def _get_index(self):
        self._next_index += 1
        return self._next_index

    @overload
    async def atext_request(
        self,
        dialog: list[ChatCompletionMessageParam],
        response_format: Union[
            completion_create_params.ResponseFormat, NotGiven
        ] = NOT_GIVEN,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        timeout: int = 300,
        retries: int = 10,
        tools: NotGiven = NOT_GIVEN,
        tool_choice: NotGiven = NOT_GIVEN,
        context: Optional[LLMContext] = None,
    ) -> str: ...

    @overload
    async def atext_request(
        self,
        dialog: list[ChatCompletionMessageParam],
        response_format: Union[
            completion_create_params.ResponseFormat, NotGiven
        ] = NOT_GIVEN,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        timeout: int = 300,
        retries: int = 10,
        tools: List[ChatCompletionToolParam] = [],
        tool_choice: ChatCompletionToolChoiceOptionParam = "auto",
        context: Optional[LLMContext] = None,
    ) -> Any: ...

    async def atext_request(
        self,
        dialog: list[ChatCompletionMessageParam],
        response_format: Union[
            completion_create_params.ResponseFormat, NotGiven
        ] = NOT_GIVEN,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        timeout: int = 300,
        retries: int = 10,
        tools: Union[List[ChatCompletionToolParam], NotGiven] = NOT_GIVEN,
        tool_choice: Union[ChatCompletionToolChoiceOptionParam, NotGiven] = NOT_GIVEN,
        context: Optional[LLMContext] = None,
    ):
        """
        Sends an asynchronous text request to the configured LLM API.

        - **Description**:
            - Attempts to send a text request, retrying across different servers on failure.
            - If all servers are down, waits indefinitely with periodic logging.
            - Handles different request types and manages token usage statistics.

        - **Args**:
            - `dialog`: Messages to send as part of the chat completion request.
            - `response_format`: JSON schema for the response. Default is NOT_GIVEN.
            - `temperature`: Controls randomness in the model's output. Default is 1.
            - `max_tokens`: Maximum number of tokens to generate in the response. Default is None.
            - `top_p`: Limits the next token selection to a subset of tokens with a cumulative probability above this value. Default is None.
            - `frequency_penalty`: Penalizes new tokens based on their existing frequency in the text so far. Default is None.
            - `presence_penalty`: Penalizes new tokens based on whether they appear in the text so far. Default is None.
            - `timeout`: Request timeout in seconds. Default is 300 seconds.
            - `retries`: Number of retry attempts in case of failure. Default is 10.
            - `tools`: List of dictionaries describing the tools that can be called by the model. Default is NOT_GIVEN.
            - `tool_choice`: Dictionary specifying how the model should choose from the provided tools. Default is NOT_GIVEN.

        - **Returns**:
            - A string containing the message content or a dictionary with tool call arguments if tools are used.
            - Never raises exceptions - waits indefinitely until a successful response is obtained.
        """

        # Infinite retry loop - never give up on the request
        while True:
            client_i = None
            
            # Server Selection with infinite wait
            async with self._routing_condition:
                while True:
                    current_time = time.time()

                    # Find servers not in cooldown with available capacity
                    available_indices = [
                        i for i in range(len(self.configs)) 
                        if self._active_requests[i] < self.configs[i].concurrency 
                        and current_time >= self._cooldown_until[i]
                    ]
                    
                    # Perform health checks on servers that just came out of cooldown
                    if available_indices:
                        healthy_indices = []
                        for i in available_indices:
                            # If server was in cooldown and just became available, check health
                            if self._cooldown_until[i] > 0 and current_time >= self._cooldown_until[i]:
                                # Server just came out of cooldown - perform health check
                                if await self._health_check(i):
                                    healthy_indices.append(i)
                                    # Reset cooldown marker after successful health check
                                    self._cooldown_until[i] = 0.0
                                else:
                                    # Health check failed - put back in cooldown
                                    self._cooldown_until[i] = current_time + self.cooldown_duration
                                    get_logger().warning(
                                        f"GPU {i} ({self.configs[i].base_url}) - Health check failed, extending cooldown for {self.cooldown_duration}s"
                                    )
                            else:
                                # Server was never in cooldown or already passed health check
                                healthy_indices.append(i)
                        
                        if healthy_indices:
                            # Choose server with lowest utilization from healthy servers
                            client_i = min(
                                healthy_indices,
                                key=lambda i: self._active_requests[i] / self.configs[i].concurrency,
                            )
                            break

                    servers_in_cooldown = [
                        i for i in range(len(self.configs))
                        if current_time < self._cooldown_until[i]
                    ]

                    # All servers are down - log warning and wait
                    if servers_in_cooldown and current_time - self._last_all_servers_down_warning >= self._all_servers_down_log_interval:
                        cooldown_info = [
                            f"GPU {i} ({self.configs[i].base_url}): cooldown until {datetime.datetime.fromtimestamp(self._cooldown_until[i]).strftime('%H:%M:%S') if self._cooldown_until[i] > current_time else 'available'}, active: {self._active_requests[i]}/{self.configs[i].concurrency}"
                            for i in servers_in_cooldown
                        ]
                        get_logger().warning(
                            f"⚠️  ALL SERVERS DOWN - Waiting for manual intervention. Status:\n" + "\n".join(cooldown_info)
                        )
                        self._last_all_servers_down_warning = current_time
                    
                    # Wait up to 5 seconds before checking again (allows notify_all to wake us up sooner)
                    try:
                        await asyncio.wait_for(self._routing_condition.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        # Timeout is expected - just loop again to check status
                        pass

                # Got a server - increment active request count
                self._active_requests[client_i] += 1

            # Make the request
            actor_i = self._get_index() % len(self._actors)
            start_time = time.perf_counter()

            try:
                success, result, log = await self._actors[actor_i].call.remote(  # type: ignore
                    self.configs[client_i],
                    dialog,
                    response_format,
                    temperature,
                    max_tokens,
                    top_p,
                    frequency_penalty,
                    presence_penalty,
                    timeout,
                    retries,
                    tools,
                    tool_choice,
                    client_index=client_i,
                )
                
                self._log_list.append(log)
                self.prompt_tokens_used += log["input_tokens"]
                self.completion_tokens_used += log["output_tokens"]

                # Check if request failed and should trigger cooldown
                if not success:
                    should_cooldown = log.get("should_cooldown", False)
                    
                    async with self._routing_condition:
                        current_time = time.time()
                        
                        # Check if server is already in cooldown (from a previous request)
                        already_in_cooldown = current_time < self._cooldown_until[client_i]
                        
                        if should_cooldown and not already_in_cooldown:
                            self._consecutive_failures[client_i] += 1
                            
                            if self._consecutive_failures[client_i] >= self.max_consecutive_failures:
                                cooldown_end = time.time() + self.cooldown_duration
                                self._cooldown_until[client_i] = cooldown_end
                                get_logger().warning(
                                    f"🔴 GPU {client_i} ({self.configs[client_i].base_url}) - CIRCUIT BREAKER TRIGGERED after {self._consecutive_failures[client_i]} failed requests. "
                                    f"Cooldown {self.cooldown_duration}s until {datetime.datetime.fromtimestamp(cooldown_end).strftime('%H:%M:%S')}. Error: {result[:100]}"
                                )
                                # Reset counter so it starts fresh after cooldown
                                self._consecutive_failures[client_i] = 0
                                # Wake up all waiting requests so they can try other servers
                                self._routing_condition.notify_all()
                            else:
                                get_logger().warning(
                                    f"⚠️  GPU {client_i} ({self.configs[client_i].base_url}) - Request failure {self._consecutive_failures[client_i]}/{self.max_consecutive_failures}. "
                                    f"Error: {result[:100]}"
                                )
                        elif already_in_cooldown:
                            # Server already in cooldown - this request was in-flight when cooldown was set
                            get_logger().debug(
                                f"GPU {client_i} request failed but server already in cooldown (expires at {datetime.datetime.fromtimestamp(self._cooldown_until[client_i]).strftime('%H:%M:%S')})"
                            )
                    
                    # Request failed - try another server (continue outer while loop)
                    get_logger().debug(
                        f"Request failed on GPU {client_i}, will retry on another server..."
                    )
                    continue  # Go back to server selection and try again

                # Request succeeded - reset consecutive failures
                async with self._routing_condition:
                    self._consecutive_failures[client_i] = 0

                end_time = time.perf_counter()
                if self._metrics_actor is not None:
                    if not context:
                        context = {}
                    self._metrics_actor.record_block_performance.remote(
                        duration=end_time - start_time,
                        actor="llm",
                        token_input=log["input_tokens"],
                        token_output=log["output_tokens"],
                        block_name=context.get("block_name", "unknown"),
                        func_name=context.get("func_name", "unknown"),
                        agent_id=context.get("agent_id", "unknown"),
                    )

                    self._db_actor.insert_prompt_response_record.remote(
                        timestamp=time.time(),
                        agent_id=context.get("agent_id", "unknown"),
                        prompt=dialog[-1]["content"] if dialog else "",
                        response=result,
                        block_name=context.get("block_name", "unknown"),
                        func_name=context.get("func_name", "unknown"),
                    )
                
                # Success - return result
                return result
                
            except Exception as e:
                # Unexpected error (e.g., Ray error) - log and retry on another server
                get_logger().error(
                    f"Unexpected error on GPU {client_i}: {str(e)[:200]}. Will retry on another server..."
                )
                # Continue to try another server
                continue
            finally:
                # Always release the slot back to the pool
                if client_i is not None:
                    async with self._routing_condition:
                        self._active_requests[client_i] -= 1
                        self._routing_condition.notify_all()
