import os
import json
import time
from enum import Enum
from multiprocessing import cpu_count
from typing import Any, List, Optional, Union, overload, TypedDict

from ..database.database_actor import DatabaseActor
from ..performance.prometheusActor import PrometheusActor
from openai import NOT_GIVEN, NotGiven
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)
from pydantic import BaseModel, Field, field_serializer, model_validator

from ..logger import get_logger
from .llm_actor import LLMActor
from .load_balancer import LLMLoadBalancer

os.environ["GRPC_VERBOSITY"] = "ERROR"

__all__ = [
    "LLM",
    "LLMConfig",
    "LLMProviderType",
    "RoutedLLMEntry",
]

MAX_TIMEOUT = 300


class LLMContext(TypedDict, total=False):
    block_name: str
    func_name: str
    agent_id: str
    prompt_identity: tuple[str, str, str]
    prompt_requires_free_text: bool
    prompt_inputs: dict[str, Any]
    prompt_input_schema: dict[str, dict[str, Any]]
    prompt_output_schema: dict[str, dict[str, Any]]
    model_role: str  # "base" or "routed"; set by RoutingLLM before delegating


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


class RoutedLLMEntry(LLMConfig):
    """LLM config entry that also declares which prompt identities it handles.

    Subclasses LLMConfig so it inherits all provider/model/key validation.
    Each entry in Config.routing is one of these.

    @usedBy agentsociety/configs/__init__.py (Config.routing field)
    @usedBy agentsociety/llm/routing_llm.py (RoutingLLM.__init__)
    """

    prompt_identities: list[str] = Field(..., min_length=1)
    """Prompt identity names (prompt_identity[0]) that this LLM handles.

    If two entries share the same key, the last one in the list wins
    (plain dict assignment semantics in RoutingLLM).
    """


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
        num_actors: int = min(cpu_count(), 32),
        metrics_actor: Optional[PrometheusActor] = None,
        db_actor: Optional[DatabaseActor] = None,
        cache_actor: Optional[Any] = None,
        cache_skip_mode: bool = False,
    ):
        """
        Initializes the LLM instance.

        - **Parameters**:
            - `configs`: An instance of `LLMConfig` containing configuration settings for the LLM.
            - `num_actors` (`int`): Number of actor instances to create for parallel processing.
              Defaults to min(cpu_count(), 32) to support high-concurrency workloads.
              For 1000+ agents, consider increasing to 64+ actors.
        """

        if len(configs) == 0:
            raise ValueError(
                "No LLM config is provided, please check your configuration"
            )

        self.configs = configs

        self._log_list = []
        self.prompt_tokens_used = 0
        self.completion_tokens_used = 0
        self._next_index = 0
        self._metrics_actor = metrics_actor
        self._db_actor = db_actor
        self._cache_actor = cache_actor
        self._cache_skip_mode = cache_skip_mode

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
        self._load_balancer = LLMLoadBalancer(self.configs)

    def get_log_list(self):
        return self._log_list

    def clear_log_list(self):
        self._log_list = []

    def _get_index(self):
        self._next_index += 1
        return self._next_index

    async def _run_health_check_request(self, client_i: int) -> tuple[bool, str]:
        """Execute a minimal request used by the load balancer health check."""
        test_dialog = [{"role": "user", "content": "Hi"}]
        actor_i = self._get_index() % len(self._actors)

        success, result, _ = await self._actors[actor_i].call.remote(
            self.configs[client_i],
            test_dialog,
            temperature=0.1,
            max_tokens=10,
            timeout=30,
            retries=1,
            client_index=client_i,
        )
        return success, str(result)

    def _should_probe_cache(
        self,
        context: Optional[LLMContext],
        tools: Union[List[ChatCompletionToolParam], NotGiven],
    ) -> bool:
        if not self._is_context_cache_eligible(context):
            return False
        return (
            self._cache_actor is not None
            and context is not None
            and "prompt_identity" in context
            and isinstance(tools, NotGiven)
        )

    def _is_cache_eligible_output_schema(
        self,
        output_schema: dict[str, dict[str, Any]],
    ) -> bool:
        if not output_schema:
            return False
        allowed = {"categorical", "float", "integer"}
        return all(
            str(field.get("type", "")).lower() in allowed
            for field in output_schema.values()
        )

    def _is_context_cache_eligible(self, context: Optional[LLMContext]) -> bool:
        if context is None:
            return False
        if context.get("prompt_requires_free_text", False):
            return False
        return self._is_cache_eligible_output_schema(
            context.get("prompt_output_schema", {})
        )

    async def _probe_semantic_cache(
        self,
        context: LLMContext,
    ) -> tuple[Optional[Any], tuple[str, str, str], bool]:
        prompt_identity = context["prompt_identity"]
        t_probe = time.perf_counter()
        probe_result: Optional[Any]

        try:
            probe_result = await self._cache_actor.query_and_maybe_serve.remote(  # type: ignore
                context["prompt_identity"],
                context.get("prompt_inputs", {}),
                context.get("prompt_input_schema", {}),
                context.get("prompt_output_schema", {}),
            )
        except Exception as e:
            get_logger().debug(f"Cache probe failed: {e}")
            probe_result = None

        probe_latency = time.perf_counter() - t_probe
        get_logger().debug(
            f"Cache probe latency={probe_latency * 1000:.1f}ms "
            f"hit={probe_result is not None} prompt_identity={prompt_identity}"
        )

        cache_hit_probe = probe_result is not None
        if self._metrics_actor is not None:
            prompt_name = str(context["prompt_identity"][0])
            # Cache hit/miss recording is now handled by QdrantCacheActor
            # to avoid double-counting. Only record latency here.
            self._metrics_actor.record_cache_latency.remote(
                cache_type="qdrant",
                prompt_name=prompt_name,
                duration=probe_latency,
            )

        return probe_result, prompt_identity, cache_hit_probe

    def _record_request_log(self, log: dict[str, Any]) -> None:
        self._log_list.append(log)
        self.prompt_tokens_used += log["input_tokens"]
        self.completion_tokens_used += log["output_tokens"]

    async def _handle_failed_request(
        self,
        client_i: int,
        result: Any,
        log: dict[str, Any],
    ) -> None:
        await self._load_balancer.mark_request_failure(
            client_i=client_i,
            should_cooldown=log.get("should_cooldown", False),
            error_message=str(result),
        )
        get_logger().debug(
            f"Request failed on GPU {client_i}, will retry on another server..."
        )

    def _record_success_metrics_and_db(
        self,
        start_time: float,
        context: Optional[LLMContext],
        dialog: list[ChatCompletionMessageParam],
        result: Any,
        log: dict[str, Any],
    ) -> None:
        if self._metrics_actor is None:
            return

        end_time = time.perf_counter()
        metric_context = context or {}
        model_role = metric_context.get("model_role", "base")
        self._metrics_actor.record_block_performance.remote(
            duration=end_time - start_time,
            actor="llm",
            model_role=model_role,
            token_input=log["input_tokens"],
            token_output=log["output_tokens"],
            block_name=metric_context.get("block_name", "unknown"),
            func_name=metric_context.get("func_name", "unknown"),
            agent_id=metric_context.get("agent_id", "unknown"),
        )

        prompt_name = (
            str(metric_context["prompt_identity"][0])
            if "prompt_identity" in metric_context
            else "unknown"
        )
        self._metrics_actor.record_llm_tokens_by_prompt.remote(
            prompt_name=prompt_name,
            token_input=log["input_tokens"],
            token_output=log["output_tokens"],
            model_role=model_role,
        )

        if self._db_actor is not None:
            self._db_actor.insert_prompt_response_record.remote(
                timestamp=time.time(),
                agent_id=metric_context.get("agent_id", "unknown"),
                prompt=dialog[-1]["content"] if dialog else "",
                response=result,
                block_name=metric_context.get("block_name", "unknown"),
                func_name=metric_context.get("func_name", "unknown"),
            )

    def _maybe_serve_probe_result(
        self,
        context: Optional[LLMContext],
        cache_hit_probe: bool,
        probe_result: Optional[Any],
        result: Any,
    ) -> Optional[Any]:
        if not (cache_hit_probe and probe_result is not None and context is not None):
            return None

        output_schema = context.get("prompt_output_schema", {})
        cached_norm = self._normalize_for_compare(probe_result, output_schema)
        live_norm = self._normalize_for_compare(result, output_schema)
        right = cached_norm == live_norm

        if self._metrics_actor is not None:
            self._metrics_actor.record_cache_hit_validation.remote(
                prompt_name=str(context["prompt_identity"][0]),
                right=right,
            )

        if not self._cache_skip_mode and self._cache_actor is not None:
            try:
                self._cache_actor.record_shadow_hit_validation.remote(
                    context["prompt_identity"],
                    right,
                )
            except Exception as e:
                get_logger().debug(f"Shadow validation record failed: {e}")

        if isinstance(probe_result, str):
            return probe_result
        return json.dumps(probe_result, ensure_ascii=True)

    def _record_cache_miss(
        self,
        context: LLMContext,
        prompt_identity: Optional[tuple[str, str, str]],
        result: Any,
    ) -> None:
        if (
            self._cache_actor is None
            or prompt_identity is None
            or not self._is_context_cache_eligible(context)
        ):
            return

        self._cache_actor.record.remote(
            context["prompt_identity"],
            context.get("prompt_inputs", {}),
            context.get("prompt_input_schema", {}),
            result,
            context.get("prompt_output_schema", {}),
        )

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
        tools: List[ChatCompletionToolParam] = ...,
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

        # Probe semantic cache before contacting live providers.
        probe_result = None
        prompt_identity = None
        cache_hit_probe = False
        if self._should_probe_cache(context, tools):
            assert context is not None
            (
                probe_result,
                prompt_identity,
                cache_hit_probe,
            ) = await self._probe_semantic_cache(context)

        # Skip mode: if probe hit, return immediately without calling the live LLM.
        if self._cache_skip_mode and cache_hit_probe and probe_result is not None:
            if isinstance(probe_result, str):
                return probe_result
            return json.dumps(probe_result, ensure_ascii=True)

        # Infinite retry loop - never give up on the request
        while True:
            client_i = await self._load_balancer.acquire_client(
                self._run_health_check_request
            )

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

                self._record_request_log(log)

                # Check if request failed and should trigger cooldown
                if not success:
                    await self._handle_failed_request(client_i, result, log)

                    # Request failed - try another server (continue outer while loop)
                    continue  # Go back to server selection and try again

                # Request succeeded - reset consecutive failures
                await self._load_balancer.mark_request_success(client_i)

                self._record_success_metrics_and_db(
                    start_time,
                    context,
                    dialog,
                    result,
                    log,
                )

                # If probe hit, validate cache correctness using this live model result.
                cached_response = self._maybe_serve_probe_result(
                    context,
                    cache_hit_probe,
                    probe_result,
                    result,
                )
                if cached_response is not None:
                    return cached_response

                # Cache miss path: record sample and miss metric.
                if context is not None:
                    self._record_cache_miss(context, prompt_identity, result)

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
                await self._load_balancer.release_client(client_i)

    def _normalize_for_compare(self, result: Any, schema: dict[str, dict[str, Any]]) -> Any:
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                return result.strip()

        if not isinstance(result, dict) or not schema:
            return result

        normalized: dict[str, Any] = {}
        for key, field in schema.items():
            if key not in result:
                continue
            value = result[key]
            field_type = str(field.get("type", "")).lower()
            if field_type == "float":
                try:
                    normalized[key] = round(float(value), 4)
                except Exception:
                    normalized[key] = value
            elif field_type == "integer":
                try:
                    normalized[key] = int(float(value))
                except Exception:
                    normalized[key] = value
            else:
                normalized[key] = value
        return normalized
