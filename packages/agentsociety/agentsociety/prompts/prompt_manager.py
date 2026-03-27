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

        current_plan_cache: Optional[dict[str, Any]] = None

        needs_location = any(
            field in {"current_location", "current_position"}
            for field in required_fields
        )
        position_now = None
        home_location = None
        work_location = None
        location_knowledge = None
        if needs_location:
            position_now = await memory.status.get("position", {})
            home_location = await memory.status.get("home", {})
            work_location = await memory.status.get("work", {})
            location_knowledge = await memory.status.get("location_knowledge", {})

        needs_persona = "persona" in required_fields
        persona_parts: Optional[dict[str, Any]] = None
        if needs_persona:
            persona_parts = {
                "name": await memory.status.get("name", "unknown"),
                "age": await memory.status.get("age", "unknown"),
                "gender": await memory.status.get("gender", "unknown"),
                "occupation": await memory.status.get("occupation", "unknown"),
                "personality": await memory.status.get("personality", "unknown"),
            }

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
                from_step = context.get("current_step", {}).get("intention")
                if from_step:
                    state[field] = from_step
                elif field == "current_intention":
                    if current_plan_cache is None:
                        current_plan_cache = await memory.status.get("current_plan", {})
                    if current_plan_cache and current_plan_cache.get("steps"):
                        idx = current_plan_cache.get("index", 0)
                        try:
                            state[field] = current_plan_cache["steps"][idx].get(
                                "intention", "unknown"
                            )
                        except Exception:
                            state[field] = "unknown"
                    else:
                        state[field] = "unknown"
                else:
                    state[field] = "unknown"
            elif field in {"emotion_types", "dominant_emotion"}:
                state[field] = await memory.status.get("emotion_types", "unknown")
            elif field == "current_emotion":
                state[field] = context.get(
                    "current_emotion",
                    await memory.status.get("emotion_types", "unknown"),
                )
            elif field == "current_thought":
                state[field] = context.get(
                    "current_thought", await memory.status.get("thought", "unknown")
                )
            elif field in {"household", "life_stage"}:
                state[field] = await memory.status.get(field, "unknown")
            elif field in {"hobbies", "goals"}:
                value = await memory.status.get(field, [])
                state[field] = ", ".join(value) if isinstance(value, list) else value
            elif field in {"current_plan_target", "plan_target"}:
                if field in context:
                    state[field] = context[field]
                else:
                    if current_plan_cache is None:
                        current_plan_cache = await memory.status.get("current_plan", {})
                    state[field] = (
                        current_plan_cache.get("target", "unknown")
                        if isinstance(current_plan_cache, dict)
                        else "unknown"
                    )
            elif field in {"current_location", "current_position"}:
                if field in context:
                    state[field] = context[field]
                elif "current_position" in context:
                    state[field] = context["current_position"]
                elif "current_location" in context:
                    state[field] = context["current_location"]
                else:
                    current_location = "Outside"
                    if (
                        isinstance(position_now, dict)
                        and isinstance(home_location, dict)
                        and "aoi_position" in position_now
                        and position_now["aoi_position"] == home_location.get("aoi_position")
                    ):
                        current_location = "At home"
                    elif (
                        isinstance(position_now, dict)
                        and isinstance(work_location, dict)
                        and "aoi_position" in position_now
                        and position_now["aoi_position"] == work_location.get("aoi_position")
                    ):
                        current_location = "At workplace"
                    elif (
                        isinstance(position_now, dict)
                        and isinstance(location_knowledge, dict)
                        and "aoi_position" in position_now
                    ):
                        known_locations = {
                            info.get("id")
                            for info in location_knowledge.values()
                            if isinstance(info, dict)
                        }
                        if position_now["aoi_position"] in known_locations:
                            current_location = str(position_now["aoi_position"])
                    state[field] = current_location
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
            elif field == "persona":
                if field in context:
                    state[field] = context[field]
                else:
                    assert persona_parts is not None
                    state[field] = (
                        f"Name: {persona_parts['name']}, "
                        f"Age: {persona_parts['age']}, "
                        f"Gender: {persona_parts['gender']}, "
                        f"Occupation: {persona_parts['occupation']}, "
                        f"Personality: {persona_parts['personality']}"
                    )
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