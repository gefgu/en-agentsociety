"""RoutingLLM: wraps a base LLM and dispatches specific prompt identities to dedicated models."""

from typing import Any, List, Optional, Union

from openai import NOT_GIVEN, NotGiven
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)

from .llm import LLM, LLMContext, RoutedLLMEntry

__all__ = ["RoutingLLM"]


class RoutingLLM(LLM):
    """Wraps a base LLM and routes calls for specific prompt identities to dedicated models.

    Does NOT call super().__init__() — it holds a pre-built base_llm as a delegate.
    Each RoutedLLMEntry in routing_entries gets its own LLM instance (full actor pool).

    Usage::

        routing_llm = RoutingLLM(
            base_llm=base_llm,
            routing_entries=config.routing,
            metrics_actor=metrics_actor,
            db_actor=db_actor,
            cache_actor=cache_actor,
            cache_skip_mode=False,
        )
        # Drop-in replacement for LLM — callers see no difference.
    """

    def __init__(
        self,
        base_llm: LLM,
        routing_entries: list[RoutedLLMEntry],
        metrics_actor: Optional[Any] = None,
        db_actor: Optional[Any] = None,
        cache_actor: Optional[Any] = None,
        cache_skip_mode: bool = False,
    ):
        # Do NOT call super().__init__() — we hold a pre-built base_llm.
        self._base_llm = base_llm
        self._routes: dict[str, LLM] = {}

        for entry in routing_entries:
            small_llm = LLM(
                [entry],
                metrics_actor=metrics_actor,
                db_actor=db_actor,
                cache_actor=cache_actor,
                cache_skip_mode=cache_skip_mode,
            )
            for key in entry.prompt_identities:
                self._routes[key] = small_llm

    # ------------------------------------------------------------------
    # Token aggregation properties (base + all routed models)
    # ------------------------------------------------------------------

    @property
    def prompt_tokens_used(self) -> int:
        return self._base_llm.prompt_tokens_used + sum(
            llm.prompt_tokens_used for llm in self._routes.values()
        )

    @property
    def completion_tokens_used(self) -> int:
        return self._base_llm.completion_tokens_used + sum(
            llm.completion_tokens_used for llm in self._routes.values()
        )

    # ------------------------------------------------------------------
    # Delegate helpers that callers may use
    # ------------------------------------------------------------------

    def get_log_list(self):
        logs = list(self._base_llm.get_log_list())
        for llm in self._routes.values():
            logs.extend(llm.get_log_list())
        return logs

    def clear_log_list(self):
        self._base_llm.clear_log_list()
        for llm in self._routes.values():
            llm.clear_log_list()

    # ------------------------------------------------------------------
    # Main dispatch
    # ------------------------------------------------------------------

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
        # Only route non-tool calls with a known prompt identity.
        if (
            isinstance(tools, NotGiven)
            and context is not None
            and "prompt_identity" in context
        ):
            key = context["prompt_identity"][0]
            if key in self._routes:
                # Annotate context so the inner LLM emits "routed" metrics.
                routed_context: LLMContext = dict(context)  # type: ignore[assignment]
                routed_context["model_role"] = "routed"
                return await self._routes[key].atext_request(
                    dialog,
                    response_format=response_format,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    timeout=timeout,
                    retries=retries,
                    tools=tools,
                    tool_choice=tool_choice,
                    context=routed_context,
                )

        return await self._base_llm.atext_request(
            dialog,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            timeout=timeout,
            retries=retries,
            tools=tools,
            tool_choice=tool_choice,
            context=context,
        )
