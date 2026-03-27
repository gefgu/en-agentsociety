import os
import re
import string
import importlib
from typing import Any, Optional

from ..logger import get_logger


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
        return prompt_data.get("inputs", {}).get("required", [])

    def has_prompt(self, prompt_name: str) -> bool:
        return prompt_name in self._loaded_prompts

    async def build_agent_state(
        self, required_fields: list[str], context: dict[str, Any], memory: Any
    ) -> dict[str, Any]:
        """Build a flat state dict using only fields requested by prompt TOML."""
        state: dict[str, Any] = {}

        needs_big5 = any(
            field
            in {
                "openness",
                "conscientiousness",
                "extraversion",
                "agreeableness",
                "neuroticism",
            }
            for field in required_fields
        )
        big5 = (
            await memory.status.get("big5", {})
            if needs_big5 and "big5" not in context
            else context.get("big5", {})
        )

        preference_fields = {
            "work_ethic",
            "chronotype",
            "social_frequency",
            "leisure_preference",
            "risk_tolerance",
            "spending_tendency",
        }
        needs_preferences = any(field in preference_fields for field in required_fields)
        preferences = (
            await memory.status.get("preferences", {})
            if needs_preferences and "preferences" not in context
            else context.get("preferences", {})
        )

        for field in required_fields:
            if field in context:
                value = context[field]
                state[field] = ", ".join(value) if isinstance(value, list) else value
            elif field == "plan":
                state[field] = context.get("plan_context", {}).get("plan", "unknown")
            elif field in {"current_intention", "intention"}:
                state[field] = context.get("current_step", {}).get("intention", "unknown")
            elif field in {"emotion_types", "dominant_emotion"}:
                state[field] = await memory.status.get("emotion_types", "unknown")
            elif field in {"household", "life_stage"}:
                state[field] = await memory.status.get(field, "unknown")
            elif field in {"hobbies", "goals"}:
                value = await memory.status.get(field, [])
                state[field] = ", ".join(value) if isinstance(value, list) else value
            elif field in {
                "openness",
                "conscientiousness",
                "extraversion",
                "agreeableness",
                "neuroticism",
            }:
                state[field] = big5.get(field, 2)
            elif field == "work_ethic":
                state[field] = preferences.get("work_ethic", 0.5)
            elif field == "chronotype":
                state[field] = preferences.get("chronotype", "standard")
            elif field == "social_frequency":
                state[field] = preferences.get("social_frequency", 0.5)
            elif field == "leisure_preference":
                state[field] = preferences.get("leisure_preference", "indoor")
            elif field == "risk_tolerance":
                state[field] = preferences.get("risk_tolerance", 0.5)
            elif field == "spending_tendency":
                state[field] = preferences.get("spending_tendency", 0.5)
            elif field == "current_time":
                state[field] = context.get("current_time", "unknown")
            elif field == "consumption_level":
                state[field] = await memory.status.get("consumption", "unknown")
            else:
                # Generic fallback: resolve arbitrary memory status fields only when requested.
                value = await memory.status.get(field, "unknown")
                state[field] = ", ".join(value) if isinstance(value, list) else value

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

        template = self._loaded_prompts[prompt_name].get("prompt", {}).get("input", "")
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

        return self._loaded_prompts[prompt_name].get("prompt", {}).get("input", "")