import asyncio
import inspect
import logging
import os
import random
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, List, Optional, Tuple, Union, overload
from uuid import uuid4

import jsonc
from openai import NOT_GIVEN, APIConnectionError, AsyncOpenAI, NotGiven, OpenAIError
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)
from pydantic import BaseModel, Field, field_serializer

from ..logger import get_logger
from .utils import *

os.environ["GRPC_VERBOSITY"] = "ERROR"

__all__ = [
    "LLM",
    "LLMConfig",
    "monitor_requests",
]


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

    semaphore: int = Field(200, ge=1)
    """Semaphore value for LLM operations to avoid rate limit"""

    @field_serializer("provider")
    def serialize_provider(self, provider: LLMProviderType, info):
        return provider.value


def record_active_request(func: Callable):
    """
    Decorator to record active requests.
    """

    async def wrapper(self, *args, **kwargs):
        uuid = str(uuid4())
        cur_frame = inspect.currentframe()
        assert cur_frame is not None
        frame = cur_frame.f_back
        assert frame is not None
        line_number = frame.f_lineno
        file_path = frame.f_code.co_filename
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        async with self.active_requests_lock:
            self._active_requests[uuid] = {
                "start_time": time.time(),
                "file_path": f'"{file_path}", line {line_number}',
                "func": func.__name__,
                "signature": signature,
            }
        try:
            res = await func(self, *args, **kwargs)
        finally:
            async with self.active_requests_lock:
                del self._active_requests[uuid]
        return res

    return wrapper


class LLM:
    """
    Main class for the Large Language Model (LLM) object used by Agent(Soul).

    - **Description**:
        - This class manages configurations and interactions with different large language model APIs.
        - It initializes clients based on the specified request type and handles token usage and consumption reporting.
    """

    def __init__(self, configs: List[LLMConfig]):
        """
        Initializes the LLM instance.

        - **Parameters**:
            - `configs`: An instance of `LLMConfig` containing configuration settings for the LLM.
        """
        if len(configs) == 0:
            raise ValueError(
                "No LLM config is provided, please check your configuration"
            )

        self.configs = configs
        self.prompt_tokens_used = 0
        self.completion_tokens_used = 0
        self.request_number = 0
        self._current_client_index = 0
        self._log_list = []
        # statistics about errors
        self._total_calls = 0
        self._total_errors = 0
        self._error_types = {
            "connection_error": 0,
            "openai_error": 0,
            "timeout_error": 0,
            "other_error": 0,
        }
        self._aclients: List[Tuple[AsyncOpenAI, asyncio.Semaphore]] = []
        self._client_usage = []
        # uuid -> {
        #     "request": str,
        #     "start_time": float,
        # }
        self._active_requests = {}  # if completed, remove from this dict
        self.active_requests_lock = asyncio.Lock()

        for config in self.configs:
            api_key = config.api_key
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
            else:
                raise ValueError(f"Unsupported `provider` {config.provider}!")

            client = AsyncOpenAI(api_key=api_key, timeout=300, base_url=base_url)
            self._aclients.append((client, asyncio.Semaphore(config.semaphore)))
            self._client_usage.append(
                {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "request_number": 0,
                }
            )

    def check_active_requests(self, timeout_threshold: float = 300):
        """
        Check all active requests and print those that have exceeded the timeout threshold.

        - **Parameters**:
            - `timeout_threshold`: Maximum allowed time (in seconds) for a request before it is considered "stuck".
        """
        current_time = time.time()
        stuck_requests = []

        for uuid, request_info in self._active_requests.items():
            elapsed_time = current_time - request_info["start_time"]
            if elapsed_time > timeout_threshold:
                stuck_requests.append(
                    {
                        "uuid": uuid,
                        "elapsed_time": elapsed_time,
                        "func": request_info["func"],
                        "file_path": request_info["file_path"],
                        "signature": request_info["signature"],
                    }
                )
        if stuck_requests:
            for req in stuck_requests:
                warning_msg = f"""WARNING: The following request may be stuck: Request UUID: {req['uuid']} Elapsed Time: {req['elapsed_time']:.2f} seconds Function: {req['func']} File Path: {req['file_path']} Signature: {req['signature']}"""
                get_logger().debug(warning_msg)
        else:
            get_logger().debug("All LLM requests are running normally.")

    async def close(self):
        """Close the LLM instance."""
        for client, _ in self._aclients:
            await client.close()

    def get_log_list(self):
        return self._log_list

    def clear_log_list(self):
        self._log_list = []

    def clear_used(self):
        """
        clear the storage of used tokens to start a new log message
        Only support OpenAI category API right now, including OpenAI, Deepseek
        """
        for usage in self._client_usage:
            usage["prompt_tokens"] = 0
            usage["completion_tokens"] = 0
            usage["request_number"] = 0

    def get_consumption(self):
        consumption = {}
        for i, usage in enumerate(self._client_usage):
            consumption[f"api-key-{i+1}"] = {
                "total_tokens": usage["prompt_tokens"] + usage["completion_tokens"],
                "request_number": usage["request_number"],
            }
        return consumption

    def show_consumption(
        self, input_price: Optional[float] = None, output_price: Optional[float] = None
    ):
        """
        Displays token usage and optionally calculates the estimated cost based on provided prices.

        - **Parameters**:
            - `input_price`: Price per million prompt tokens. Default is None.
            - `output_price`: Price per million completion tokens. Default is None.

        - **Returns**:
            - A dictionary summarizing the token usage and, if applicable, the estimated cost.
        """
        total_stats = {"total": 0, "prompt": 0, "completion": 0, "requests": 0}

        for i, usage in enumerate(self._client_usage):
            prompt_tokens = usage["prompt_tokens"]
            completion_tokens = usage["completion_tokens"]
            requests = usage["request_number"]
            total_tokens = prompt_tokens + completion_tokens

            total_stats["total"] += total_tokens
            total_stats["prompt"] += prompt_tokens
            total_stats["completion"] += completion_tokens
            total_stats["requests"] += requests

            rate = (
                prompt_tokens / completion_tokens if completion_tokens != 0 else "nan"
            )
            tokens_per_request = total_tokens / requests if requests != 0 else "nan"

            print(f"\nAPI Key #{i+1}:")
            print(f"Request Number: {requests}")
            print("Token Usage:")
            print(f"    - Total tokens: {total_tokens}")
            print(f"    - Prompt tokens: {prompt_tokens}")
            print(f"    - Completion tokens: {completion_tokens}")
            print(f"    - Token per request: {tokens_per_request}")
            print(f"    - Prompt:Completion ratio: {rate}:1")

            if input_price is not None and output_price is not None:
                consumption = (
                    prompt_tokens / 1000000 * input_price
                    + completion_tokens / 1000000 * output_price
                )
                print(f"    - Cost Estimation: {consumption}")

        return total_stats

    def _get_next_client(self):
        """
        Retrieves the next client to be used for making requests.

        - **Description**:
            - This method cycles through the available clients in a round-robin fashion.

        - **Returns**:
            - The next client instance to be used for making requests.
        """
        if self._current_client_index >= min(len(self._aclients), len(self.configs)):
            raise ValueError(
                f"Invalid client index: {self._current_client_index} vs {len(self._aclients)} & {len(self.configs)}"
            )
        config = self.configs[self._current_client_index]
        client = self._aclients[self._current_client_index]
        self._current_client_index = (self._current_client_index + 1) % len(
            self._aclients
        )
        return config, client

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
    ) -> Any: ...

    @record_active_request
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
    ):
        """
        Sends an asynchronous text request to the configured LLM API.

        - **Description**:
            - Attempts to send a text request up to `retries` times with exponential backoff on failure.
            - Handles different request types and manages token usage statistics.

        - **Parameters**:
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
            - Raises exceptions if the request fails after all retry attempts.
        """
        start_time = time.time()
        log = {"request_time": start_time}
        for attempt in range(retries):
            self._total_calls += 1
            config, (client, semaphore) = self._get_next_client()
            response = None
            async with semaphore:
                try:
                    response = await asyncio.wait_for(
                        fut=client.chat.completions.create(
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
                        ),
                        timeout=timeout,
                    )
                    if response.usage is not None:
                        self._client_usage[self._current_client_index][
                            "prompt_tokens"
                        ] += response.usage.prompt_tokens
                        self._client_usage[self._current_client_index][
                            "completion_tokens"
                        ] += response.usage.completion_tokens
                        self._client_usage[self._current_client_index][
                            "request_number"
                        ] += 1
                        log["input_tokens"] = response.usage.prompt_tokens
                        log["output_tokens"] = response.usage.completion_tokens
                    end_time = time.time()
                    log["consumption"] = end_time - start_time
                    self._log_list.append(log)
                    if tools and response.choices[0].message.tool_calls:
                        return jsonc.loads(
                            response.choices[0].message.tool_calls[0].function.arguments
                        )
                    else:
                        content = response.choices[0].message.content
                        if content is None:
                            raise ValueError("No content in response")
                        return content
                except APIConnectionError as e:
                    get_logger().warning(
                        f"API connection error: `{e}` for request {dialog} {tools} {tool_choice}. original response: `{response}`. Retry {attempt+1} of {retries}"
                    )
                    self._total_errors += 1
                    self._error_types["connection_error"] += 1
                    if attempt < retries - 1:
                        await asyncio.sleep(random.random() * 2**attempt)
                    else:
                        raise e
                except OpenAIError as e:
                    error_message = str(e)
                    get_logger().warning(
                        f"OpenAIError: {error_message} for request {dialog} {tools} {tool_choice}. original response: `{response}`. Retry {attempt+1} of {retries}"
                    )
                    self._total_errors += 1
                    self._error_types["openai_error"] += 1
                    if attempt < retries - 1:
                        await asyncio.sleep(random.random() * 2**attempt)
                    else:
                        raise e
                except asyncio.TimeoutError as e:
                    get_logger().warning(
                        f"TimeoutError: `{e}` for request {dialog} {tools} {tool_choice}. original response: `{response}`. Retry {attempt+1} of {retries}"
                    )
                    self._total_errors += 1
                    self._error_types["timeout_error"] += 1
                    if attempt < retries - 1:
                        await asyncio.sleep(random.random() * 2**attempt)
                    else:
                        raise e
                except Exception as e:
                    get_logger().warning(
                        f"LLM Error: `{e}` for request {dialog} {tools} {tool_choice}. original response: `{response}`. Retry {attempt+1} of {retries}"
                    )
                    self._total_errors += 1
                    self._error_types["other_error"] += 1
                    if attempt < retries - 1:
                        await asyncio.sleep(random.random() * 2**attempt)
                    else:
                        raise e
        raise RuntimeError("Failed to get response from LLM")

    def get_error_statistics(self):
        """
        Returns statistics about LLM API calls and errors.

        - **Description**:
            - This method provides statistics on the total number of API calls,
              the total number of errors, and counts for specific error types.

        - **Returns**:
            - A dictionary containing the call and error statistics.
        """
        stats = {
            "total": self._total_calls,
            "error": self._total_errors,
        }
        # add statistics about different error types
        for error_type, count in self._error_types.items():
            stats[f"{error_type}"] = count

        return stats


async def monitor_requests(
    llm_instance: LLM, interval: float = 60, timeout_threshold: float = 300
):
    """
    Periodically monitor active requests to detect potential timeouts.

    - **Parameters**:
        - `llm_instance`: An instance of the LLM class.
        - `interval`: Interval (in seconds) between checks.
        - `timeout_threshold`: Maximum allowed time (in seconds) for a request.
    """
    while True:
        await asyncio.sleep(interval)
        llm_instance.check_active_requests(timeout_threshold=timeout_threshold)


if __name__ == "__main__":

    import asyncio

    async def main():
        configs = [
            LLMConfig(
                provider=LLMProviderType.DeepSeek,
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                model="deepseek-chat",
                base_url=None,
                semaphore=1,
            )
        ]
        llm = LLM(configs)

        resp = await llm.atext_request([{"role": "user", "content": "Hello, world!"}])
        print(resp)

    asyncio.run(main())
