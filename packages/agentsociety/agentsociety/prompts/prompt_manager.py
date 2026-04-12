import os
import re
import string
import importlib
from typing import Any, Optional

from ..logger import get_logger
from .prompt_memory_handler import PromptMemoryHandler


def _load_toml_module():
    try:
        return importlib.import_module("tomllib")
    except ModuleNotFoundError:
        return importlib.import_module("tomli")


_TOML_MODULE = _load_toml_module()

class SafeDict(dict):
    def __missing__(self, key):
        return "unknown"


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
        self._loaded_prompts: dict[str, dict] = {}
        self._prompt_memory_handler = PromptMemoryHandler()
        self._resolve_and_load_prompts()

    def _load_all_prompts(self) -> list[dict]:
        all_available_prompts: list[dict] = []
        if not os.path.isdir(self.prompts_dir):
            get_logger().warning(
                f"Prompt directory does not exist: {self.prompts_dir}"
            )
            return all_available_prompts

        for root, _, files in os.walk(self.prompts_dir):
            for file in files:
                if not file.endswith(".toml"):
                    continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "rb") as f:
                        data = _TOML_MODULE.load(f)
                    data["_filepath"] = filepath
                    all_available_prompts.append(data)
                except Exception as e:
                    get_logger().warning(
                        f"Failed to parse prompt TOML file {filepath}: {e}"
                    )

        return all_available_prompts

    def _resolve_and_load_prompts(self) -> None:
        """Scan all prompt TOMLs and resolve active prompt definitions using fallback rules."""
        all_available_prompts = self._load_all_prompts()

        # If no active config is provided, load latest version of each prompt name.
        if not self.active_config:
            grouped: dict[str, list[dict]] = {}
            for prompt in all_available_prompts:
                name = prompt.get("metadata", {}).get("name")
                if not name:
                    continue
                grouped.setdefault(name, []).append(prompt)

            for name, candidates in grouped.items():
                candidates.sort(
                    key=lambda x: parse_version(
                        x.get("metadata", {}).get("version", "0.0.0")
                    ),
                    reverse=True,
                )
                self._loaded_prompts[name] = candidates[0]
            return

        for target_name, target_meta in self.active_config.items():
            target_version = target_meta.get("version")
            target_origin = target_meta.get("origin")

            candidates = [
                p
                for p in all_available_prompts
                if p.get("metadata", {}).get("name") == target_name
            ]

            if not candidates:
                get_logger().error(
                    f"No prompt files found for '{target_name}'. Prompt resolution failed."
                )
                continue

            candidates.sort(
                key=lambda x: parse_version(x.get("metadata", {}).get("version", "0.0.0")),
                reverse=True,
            )

            exact_match = next(
                (
                    p
                    for p in candidates
                    if p.get("metadata", {}).get("version") == target_version
                    and p.get("metadata", {}).get("origin") == target_origin
                ),
                None,
            )
            if exact_match is not None:
                self._loaded_prompts[target_name] = exact_match
                get_logger().debug(
                    f"Prompt exact match loaded for '{target_name}' ({target_origin}, v{target_version})"
                )
                continue

            version_match = next(
                (
                    p
                    for p in candidates
                    if p.get("metadata", {}).get("version") == target_version
                ),
                None,
            )
            if version_match is not None:
                found_origin = version_match.get("metadata", {}).get("origin", "unknown")
                get_logger().warning(
                    f"Prompt fallback for '{target_name}': requested origin '{target_origin}' not found; "
                    f"using origin '{found_origin}' at v{target_version}"
                )
                self._loaded_prompts[target_name] = version_match
                continue

            highest_match = candidates[0]
            found_version = highest_match.get("metadata", {}).get("version", "unknown")
            found_origin = highest_match.get("metadata", {}).get("origin", "unknown")
            get_logger().warning(
                f"Prompt fallback for '{target_name}': requested v{target_version} not found; "
                f"using highest available v{found_version} (origin '{found_origin}')"
            )
            self._loaded_prompts[target_name] = highest_match

    def get_required_fields(self, prompt_name: str) -> list[str]:
        prompt_data = self._loaded_prompts.get(prompt_name, {})
        schema = self.get_input_schema(prompt_name)
        if schema:
            return list(schema.keys())
        # Backward compatibility for legacy prompt TOMLs.
        return prompt_data.get("inputs", {}).get("required", [])

    def get_prompt_identity(self, prompt_name: str) -> tuple[str, str, str]:
        if prompt_name not in self._loaded_prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found in loaded configs")
        meta = self._loaded_prompts[prompt_name].get("metadata", {})
        name = str(meta.get("name", prompt_name))
        origin = str(meta.get("origin", "unknown"))
        version = str(meta.get("version", "0.0.0"))
        return (name, origin, version)

    def get_input_schema(self, prompt_name: str) -> dict[str, dict]:
        prompt_data = self._loaded_prompts.get(prompt_name, {})
        inputs = prompt_data.get("inputs", {})
        if not isinstance(inputs, dict):
            return {}
        return {
            k: v
            for k, v in inputs.items()
            if k != "required" and isinstance(v, dict)
        }

    def get_typed_input_fields(self, prompt_name: str) -> list[str]:
        schema = self.get_input_schema(prompt_name)
        allowed_types = {"text", "integer", "float", "categorical"}
        return [
            field
            for field, field_schema in schema.items()
            if str(field_schema.get("type", "")).lower() in allowed_types
        ]

    def get_text_input_fields(self, prompt_name: str) -> list[str]:
        inputs = self.get_input_schema(prompt_name)
        return [
            k
            for k, v in inputs.items()
            if isinstance(v, dict) and str(v.get("type", "")).lower() == "text"
        ]

    def get_output_schema(self, prompt_name: str) -> dict[str, dict]:
        prompt_data = self._loaded_prompts.get(prompt_name, {})
        outputs = prompt_data.get("outputs", {})
        if not isinstance(outputs, dict):
            return {}
        return {k: v for k, v in outputs.items() if isinstance(v, dict)}

    def requires_free_text_generation(self, prompt_name: str) -> bool:
        """Return True when prompt outputs require free-text generation.

        Prompts are considered free-text if output schema is missing/empty or
        any declared output type is not one of integer/float/categorical.
        """
        schema = self.get_output_schema(prompt_name)
        if not schema:
            return True
        structured_types = {"categorical", "float", "integer"}
        return any(
            str(field.get("type", "")).lower() not in structured_types
            for field in schema.values()
        )

    def is_cache_eligible(self, prompt_name: str) -> bool:
        return not self.requires_free_text_generation(prompt_name)

    def has_prompt(self, prompt_name: str) -> bool:
        return prompt_name in self._loaded_prompts

    async def build_agent_state(
        self, required_fields: list[str], context: dict[str, Any], memory: Any
    ) -> dict[str, Any]:
        """Build a flat state dict using only fields requested by prompt TOML."""
        state: dict[str, Any] = {}

        for field in required_fields:
            if field in context:
                value = context[field]
                state[field] = ", ".join(value) if isinstance(value, list) else value
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

    @staticmethod
    def _escape_literal_braces_keep_fields(template: str) -> str:
        """Escape literal braces while preserving simple {field} placeholders.

        This protects prompt templates that contain JSON examples with single braces.
        """
        # Protect already escaped braces first.
        sanitized = template.replace("{{", "__LBRACE_ESC__").replace(
            "}}", "__RBRACE_ESC__"
        )

        # Protect valid simple placeholders so we can escape all other braces.
        placeholder_map: dict[str, str] = {}

        def _protect(match: re.Match[str]) -> str:
            token = f"__FIELD_{len(placeholder_map)}__"
            placeholder_map[token] = match.group(0)
            return token

        sanitized = re.sub(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", _protect, sanitized)

        # Escape remaining braces (literal JSON/object examples, etc.).
        sanitized = sanitized.replace("{", "{{").replace("}", "}}")

        # Restore placeholders and pre-escaped braces.
        for token, field in placeholder_map.items():
            sanitized = sanitized.replace(token, field)
        sanitized = sanitized.replace("__LBRACE_ESC__", "{{").replace(
            "__RBRACE_ESC__", "}}"
        )
        return sanitized

    def format_prompt(self, prompt_name: str, state_dict: dict) -> str:
        if prompt_name not in self._loaded_prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found in loaded configs")

        prompt_block = self._loaded_prompts[prompt_name].get("prompt", {})
        prompt_input = str(prompt_block.get("input", ""))
        output_guidance = str(prompt_block.get("output_guidance", "")).strip()
        template = prompt_input
        if output_guidance:
            template = f"{prompt_input}\n\n{output_guidance}"
        formatter = string.Formatter()
        try:
            return formatter.vformat(template, (), SafeDict(state_dict))
        except ValueError as e:
            # Fallback inspired by legacy FormatPrompt behavior: tolerate literal braces.
            get_logger().warning(
                f"Prompt formatting fallback for '{prompt_name}' due to ValueError: {e}"
            )
            safe_template = self._escape_literal_braces_keep_fields(template)
            return formatter.vformat(safe_template, (), SafeDict(state_dict))

    def format_prompt_to_dialog(self, prompt_name: str, state_dict: dict) -> list[dict[str, str]]:
        return [{"role": "user", "content": self.format_prompt(prompt_name, state_dict)}]

    def get_prompt_template(self, prompt_name: str) -> str:
        if prompt_name not in self._loaded_prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found in loaded configs")
        prompt_block = self._loaded_prompts[prompt_name].get("prompt", {})
        prompt_input = str(prompt_block.get("input", ""))
        output_guidance = str(prompt_block.get("output_guidance", "")).strip()
        if not output_guidance:
            return prompt_input
        return f"{prompt_input}\n\n{output_guidance}"