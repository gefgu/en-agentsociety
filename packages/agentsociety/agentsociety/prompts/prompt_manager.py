import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Union

import json_repair

from ..logger import get_logger
from .prompt_memory_handler import PromptMemoryHandler
from .base import BasePrompt, PromptContext


def _clean_json_response(response: str) -> str:
    """Strip markdown code fences from LLM responses."""
    return response.replace("```json", "").replace("```", "").strip()


def _extract_json(output_str: str) -> Optional[str]:
    """Extract the first JSON object substring from raw text."""
    start = output_str.find("{")
    end = output_str.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return output_str[start : end + 1]


def _extract_dicts(input_string: str) -> list[dict]:
    """Extract all dict-shaped substrings from text using regex + json_repair."""
    dict_pattern = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"
    matches = re.findall(dict_pattern, input_string, re.DOTALL)
    dicts: list[dict] = []
    for match in matches:
        try:
            parsed = json_repair.loads(match)
            if isinstance(parsed, dict):
                dicts.append(parsed)
        except Exception:
            pass
    return dicts


class ResponseMode(Enum):
    """How an LLM response should be parsed."""

    JSON = "json"
    EXTRACT_JSON = "extract_json"
    EXTRACT_DICT = "extract_dict"
    PLAIN_TEXT = "plain_text"


@dataclass
class PromptResult:
    """Unified return type from execute_prompt."""

    raw_response: str
    parsed: Any
    state_dict: dict[str, Any]
    prompt_context: dict[str, Any]
    success: bool = True
    error: Optional[str] = None


class OutputValidationError(ValueError):
    """Raised when a parsed LLM response does not match a prompt Output model."""


class ResponseParseError(ValueError):
    """Raised when a raw LLM response cannot be parsed in the requested mode."""


def parse_version(version_str: str) -> tuple[int, ...]:
    """Convert semantic version string into a sortable tuple."""
    try:
        return tuple(map(int, str(version_str).replace("v", "").split(".")))
    except ValueError:
        return (0, 0, 0)


class PromptManager:
    def __init__(
        self, prompts_dir: str, active_config: Optional[dict[str, dict[str, str]]] = None
    ):
        self.prompts_dir = prompts_dir
        self.active_config = active_config or {}
        self._loaded_classes: dict[str, type[BasePrompt]] = {}
        self._prompt_memory_handler = PromptMemoryHandler()
        self._resolve_and_load_classes()

    def _resolve_and_load_classes(self) -> None:
        """Load Python prompt classes from the classes package and apply version/origin selection."""
        try:
            from .prompts import _ALL_PROMPT_CLASSES
        except Exception as e:
            get_logger().warning(f"Failed to import prompt classes: {e}")
            return

        # Group classes by name.
        grouped: dict[str, list[type[BasePrompt]]] = {}
        for cls in _ALL_PROMPT_CLASSES:
            grouped.setdefault(cls.name, []).append(cls)

        if not self.active_config:
            # No config: pick highest version per name.
            for name, candidates in grouped.items():
                best = max(candidates, key=lambda c: c.get_version())
                self._loaded_classes[name] = best
            return

        for name, candidates in grouped.items():
            target_meta = self.active_config.get(name)
            if target_meta is None:
                # Not in active config — pick highest version among all origins.
                best = max(candidates, key=lambda c: c.get_version())
                self._loaded_classes[name] = best
                continue

            target_origin = target_meta.get("origin", "")
            target_version = target_meta.get("version", "")

            # 1. Exact match (origin + version).
            exact = next(
                (c for c in candidates if c.origin == target_origin and c.version == target_version),
                None,
            )
            if exact is not None:
                self._loaded_classes[name] = exact
                continue

            # 2. Version-only match (any origin).
            version_match = next(
                (c for c in candidates if c.version == target_version),
                None,
            )
            if version_match is not None:
                self._loaded_classes[name] = version_match
                continue

            # 3. Highest version for the requested origin, then any origin.
            origin_candidates = [c for c in candidates if c.origin == target_origin]
            pool = origin_candidates if origin_candidates else candidates
            self._loaded_classes[name] = max(pool, key=lambda c: c.get_version())

    async def _build_full_context(
        self, context: dict[str, Any], memory: Any
    ) -> dict[str, Any]:
        """Build a complete flat context dict from memory + call-site context.

        Resolves all PromptContext fields from memory, then overlays the
        caller-supplied *context* dict (caller wins on collision).
        """
        full: dict[str, Any] = {}
        for field_name in PromptContext.model_fields:
            if field_name in context:
                value = context[field_name]
                full[field_name] = (
                    ", ".join(str(v) for v in value) if isinstance(value, list) else value
                )
            else:
                full[field_name] = await self._prompt_memory_handler.resolve_field(
                    field_name, memory
                )
        # Overlay any extra caller-supplied keys not in PromptContext.
        for k, v in context.items():
            if k not in full:
                full[k] = v
        return full

    def _build_llm_context_from_class(
        self,
        prompt_cls: type[BasePrompt],
        state_dict: dict[str, Any],
        block_name: str,
        func_name: str,
        agent_id: str,
    ) -> dict[str, Any]:
        """Build the metadata dict for the LLM layer when using a Python prompt class."""
        input_schema = prompt_cls.get_input_schema()
        return {
            "block_name": block_name,
            "func_name": func_name,
            "agent_id": agent_id,
            "prompt_identity": (prompt_cls.name, prompt_cls.origin, prompt_cls.version),
            "prompt_requires_free_text": prompt_cls.requires_free_text_generation(),
            "prompt_inputs": {
                key: state_dict[key]
                for key in input_schema
                if key in state_dict
            },
            "prompt_input_schema": input_schema,
            "prompt_output_schema": prompt_cls.get_output_schema(),
        }

    def get_required_fields(self, prompt_name: str) -> list[str]:
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        return list(cls.get_input_schema().keys())

    def get_prompt_identity(self, prompt_name: str) -> tuple[str, str, str]:
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        return (cls.name, cls.origin, cls.version)

    def get_input_schema(self, prompt_name: str) -> dict[str, dict]:
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            return {}
        return cls.get_input_schema()

    def get_typed_input_fields(self, prompt_name: str) -> list[str]:
        schema = self.get_input_schema(prompt_name)
        allowed_types = {"text", "integer", "float", "categorical"}
        return [
            f
            for f, field_schema in schema.items()
            if str(field_schema.get("type", "")).lower() in allowed_types
        ]

    def get_text_input_fields(self, prompt_name: str) -> list[str]:
        return [
            k
            for k, v in self.get_input_schema(prompt_name).items()
            if isinstance(v, dict) and str(v.get("type", "")).lower() == "text"
        ]

    def get_output_schema(self, prompt_name: str) -> dict[str, dict]:
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            return {}
        return cls.get_output_schema()

    def requires_free_text_generation(self, prompt_name: str) -> bool:
        """Return True when prompt outputs require free-text generation."""
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            return True
        return cls.requires_free_text_generation()

    def is_cache_eligible(self, prompt_name: str) -> bool:
        return not self.requires_free_text_generation(prompt_name)

    def has_prompt(self, prompt_name: str) -> bool:
        return prompt_name in self._loaded_classes

    async def build_agent_state(
        self, required_fields: list[str], context: dict[str, Any], memory: Any
    ) -> dict[str, Any]:
        """Build a flat state dict using only fields requested by prompt TOML."""
        state: dict[str, Any] = {}

        for field in required_fields:
            if field in context:
                value = context[field]
                state[field] = ", ".join(str(v) for v in value) if isinstance(value, list) else value
                continue

            if field == "plan":
                state[field] = context.get("plan_context", {}).get("plan", "unknown")
                continue

            if field in {"current_intention", "intention"}:
                from_step = context.get("current_step", {}).get("intention")
                if from_step:
                    state[field] = from_step
                    continue

            if field in {"current_location", "current_position"}:
                if "current_position" in context:
                    state[field] = context["current_position"]
                    continue
                if "current_location" in context:
                    state[field] = context["current_location"]
                    continue

            if field == "current_emotion" and "current_emotion" in context:
                state[field] = context["current_emotion"]
                continue

            if field == "current_thought" and "current_thought" in context:
                state[field] = context["current_thought"]
                continue

            if field == "current_time" and "current_time" in context:
                state[field] = context["current_time"]
                continue

            state[field] = await self._prompt_memory_handler.resolve_field(field, memory)

        return state

    def format_prompt(self, prompt_name: str, state_dict: dict) -> str:
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        return cls(**state_dict).format_prompt()

    def format_prompt_to_dialog(self, prompt_name: str, state_dict: dict) -> list[dict[str, str]]:
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        return cls(**state_dict).format_prompt_to_dialog()

    # ------------------------------------------------------------------
    # execute_prompt: end-to-end prompt lifecycle
    # ------------------------------------------------------------------

    def coerce_output(
        self,
        prompt_name: str,
        parsed: dict[str, Any],
        *,
        raise_on_error: bool = False,
    ) -> dict[str, Any]:
        """Coerce values in *parsed* to match the output schema types via Pydantic Output model."""
        cls = self._loaded_classes.get(prompt_name)
        if cls is None:
            return parsed
        output_cls = getattr(cls, "Output", None)
        if output_cls is None:
            return parsed
        try:
            return output_cls.model_validate(parsed).model_dump()
        except Exception as e:
            action = "raising for retry" if raise_on_error else "returning parsed as-is"
            get_logger().warning(
                f"coerce_output: Pydantic validation failed for '{prompt_name}': {e}; "
                f"{action}"
            )
            if raise_on_error:
                raise OutputValidationError(
                    f"Output validation failed for '{prompt_name}': {e}"
                ) from e
            return parsed

    @staticmethod
    def _retry_dialog(
        dialog: list[dict[str, str]],
        *,
        prompt_name: str,
        last_error: str,
        raw_response: str,
    ) -> list[dict[str, str]]:
        """Return a retry dialog with concise feedback about the invalid response."""
        raw_preview = raw_response[:500] if raw_response else "(no response)"
        correction = (
            f"The previous response for prompt '{prompt_name}' could not be parsed or "
            f"validated: {last_error}\n"
            f"Previous response: {raw_preview}\n"
            "Return only a JSON object that exactly matches the requested output schema. "
            "Do not use null for required fields."
        )
        return [*dialog, {"role": "user", "content": correction}]

    @staticmethod
    def _parse_response(raw: str, mode: ResponseMode) -> Any:
        """Parse a raw LLM response string according to *mode*."""
        if mode == ResponseMode.PLAIN_TEXT:
            return raw

        if mode == ResponseMode.JSON:
            cleaned = _clean_json_response(raw)
            parsed = json_repair.loads(cleaned)
            if isinstance(parsed, str):
                parsed = json_repair.loads(parsed)
            return parsed

        if mode == ResponseMode.EXTRACT_JSON:
            json_str = _extract_json(raw)
            if json_str is None:
                raise ValueError("No JSON object found in response")
            return json_repair.loads(json_str)

        if mode == ResponseMode.EXTRACT_DICT:
            dicts = _extract_dicts(raw)
            if not dicts:
                raise ValueError("No dict found in response")
            return dicts[0]

        raise ValueError(f"Unknown ResponseMode: {mode}")

    async def execute_prompt(
        self,
        *,
        prompt_name: str,
        llm: Any,
        memory: Any,
        context: dict[str, Any],
        block_name: str,
        func_name: str,
        agent_id: str,
        response_mode: ResponseMode = ResponseMode.JSON,
        max_retries: int = 0,
        validate: Optional[Callable[[Any], bool]] = None,
        timeout: int = 300,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        dialog_override: Optional[list[dict[str, str]]] = None,
    ) -> PromptResult:
        """Execute a prompt end-to-end and return a :class:`PromptResult`.

        1. Build full context from *context* + memory.
        2. Format the prompt dialog (or use *dialog_override*).
        3. Call the LLM.
        4. Parse the response according to *response_mode*.
        5. Coerce output types via Pydantic Output model.
        6. Optionally run *validate*; retry up to *max_retries* times.
        """
        prompt_cls = self._loaded_classes.get(prompt_name)
        if prompt_cls is None:
            raise ValueError(f"Prompt '{prompt_name}' not found")

        full_ctx = await self._build_full_context(context, memory)

        # Use model_construct to bypass Pydantic input validation.
        # Prompt input fields are only used for template string formatting,
        # so type mismatches from memory (e.g. 'unknown' str for a float
        # field, or an int for a str field) must not raise here.
        declared_ctx: dict[str, Any] = {}
        for field_name, field_info in prompt_cls.model_fields.items():
            lookup_key = field_info.alias or field_name
            declared_ctx[field_name] = full_ctx.get(lookup_key, full_ctx.get(field_name))
        prompt_instance = prompt_cls.model_construct(**declared_ctx)

        state_dict = {
            k: getattr(prompt_instance, k)
            for k in prompt_cls.model_fields
        }
        prompt_context = self._build_llm_context_from_class(
            prompt_cls, state_dict, block_name, func_name, agent_id
        )
        if dialog_override is not None:
            dialog = dialog_override
        else:
            dialog = prompt_instance.format_prompt_to_dialog()

        from openai._types import NOT_GIVEN

        response_format = (
            {"type": "json_object"}
            if response_mode == ResponseMode.JSON
            else NOT_GIVEN
        )

        raw_response = ""
        last_error: Optional[str] = None
        min_schema_retries = 3
        effective_max_retries = max_retries
        attempt = 0

        while attempt <= effective_max_retries:
            try:
                attempt_dialog = (
                    dialog
                    if attempt == 0 or last_error is None
                    else self._retry_dialog(
                        dialog,
                        prompt_name=prompt_name,
                        last_error=last_error,
                        raw_response=raw_response,
                    )
                )
                attempt_prompt_context = dict(prompt_context)
                attempt_prompt_context["prompt_attempt"] = attempt + 1
                if attempt > 0:
                    attempt_prompt_context["prompt_bypass_cache"] = True

                raw_response = await llm.atext_request(
                    attempt_dialog,
                    response_format=response_format,
                    temperature=temperature,
                    timeout=timeout,
                    max_tokens=max_tokens,
                    context=attempt_prompt_context,
                )

                try:
                    parsed = self._parse_response(raw_response, response_mode)
                except Exception as parse_error:
                    raise ResponseParseError(
                        f"Response parse failed for '{prompt_name}': {parse_error}"
                    ) from parse_error

                if isinstance(parsed, dict) and response_mode in (
                    ResponseMode.JSON,
                    ResponseMode.EXTRACT_JSON,
                    ResponseMode.EXTRACT_DICT,
                ):
                    parsed = self.coerce_output(
                        prompt_name,
                        parsed,
                        raise_on_error=True,
                    )

                if validate is not None and not validate(parsed):
                    raise ValueError("Custom validation failed")

                return PromptResult(
                    raw_response=raw_response,
                    parsed=parsed,
                    state_dict=state_dict,
                    prompt_context=prompt_context,
                    success=True,
                )

            except Exception as e:
                last_error = str(e)
                if isinstance(e, (OutputValidationError, ResponseParseError)):
                    effective_max_retries = max(
                        effective_max_retries,
                        min_schema_retries,
                    )
                raw_preview = raw_response[:300] if raw_response else "(no response)"
                get_logger().warning(
                    f"execute_prompt '{prompt_name}' attempt "
                    f"{attempt + 1}/{effective_max_retries + 1} failed: {e}\n"
                    f"Raw response: {raw_preview}"
                )
                attempt += 1

        return PromptResult(
            raw_response=raw_response,
            parsed=None,
            state_dict=state_dict,
            prompt_context=prompt_context,
            success=False,
            error=last_error,
        )
