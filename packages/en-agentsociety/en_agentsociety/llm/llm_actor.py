import asyncio
import random
import time
from typing import Any, List, Optional, Union

import httpx
import ray
from openai import NOT_GIVEN, APIConnectionError, AsyncOpenAI, NotGiven, OpenAIError
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)

from ..logger import get_logger

MAX_TIMEOUT = 300


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

        if msg.get("role") == "system":
            system_content = msg.get("content", "")

            if i + 1 < len(dialog) and dialog[i + 1].get("role") == "user":
                user_content = dialog[i + 1].get("content", "")
                merged_content = f"{system_content}\n\n{user_content}"
                converted.append({"role": "user", "content": merged_content})
                i += 2
            else:
                converted.append({"role": "user", "content": system_content})
                i += 1
        else:
            converted.append(msg)
            i += 1

    return converted


@ray.remote(concurrency_groups={"default": 500})
class LLMActor:
    """Ray actor that executes chat completion calls and retry policy."""

    def __init__(self, provider: Optional[str] = None):
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=min(30.0, MAX_TIMEOUT / 4),
                read=MAX_TIMEOUT,
                write=MAX_TIMEOUT,
                pool=MAX_TIMEOUT,
            ),
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0
            ),
        )

        self.support_system_role = provider not in ["vllm", "deepseek"] if provider else False

    async def call(
        self,
        config: Any,
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
        """Execute one completion request with retries and normalized result logging."""

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
            "should_cooldown": False,
        }

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

                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("No content in response")

                if not content or content.strip() in ["{}", "{", ""]:
                    raise ValueError(f"Empty or invalid response from vLLM: {content}")

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
                    continue

                if "json" in error_message.lower() or "format" in error_message.lower():
                    get_logger().error(
                        f"JSON parsing error from LLM: {error_message}. Response content: {response.choices[0].message.content if response and response.choices else 'N/A'}. Retry {attempt+1} of {retries}"
                    )

                is_critical = any(
                    keyword in error_message.lower()
                    for keyword in ["connection", "404", "503", "502", "timeout"]
                )
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
                    consecutive_critical_errors = 0
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
                is_critical = any(
                    keyword in error_str
                    for keyword in ["connection", "failed to get response", "404", "503", "502"]
                )

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

        log["should_cooldown"] = True
        error_msg = f"GPU {client_index} - Failed to get response from LLM after {retries} attempts"
        get_logger().error(error_msg)
        return (False, error_msg, log)
