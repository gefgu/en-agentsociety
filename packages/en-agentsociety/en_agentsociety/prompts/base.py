"""
Pure-Python prompt infrastructure for the Code-as-Config migration.

Replaces TOML prompt files with typed Pydantic models that provide:
- IDE autocompletion for prompt fields
- Static type checking
- Native Pydantic-validated LLM structured outputs
"""
from __future__ import annotations

from typing import Any, ClassVar, Optional, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _python_type_to_schema_type(annotation: Any) -> str:
    """Map a Python type annotation to the legacy TOML schema type string."""
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Unwrap Optional[X] == Union[X, None]
    if origin is Union and len(args) == 2 and type(None) in args:
        inner = next(a for a in args if a is not type(None))
        return _python_type_to_schema_type(inner)

    if annotation is int:
        return "integer"
    if annotation is float:
        return "float"
    if annotation is str:
        return "text"
    if annotation is bool:
        return "categorical"

    return "text"  # default: Any, list, dict, etc.


# ---------------------------------------------------------------------------
# PromptContext — flat union of all fields injectable into prompts
# ---------------------------------------------------------------------------

class PromptContext(BaseModel):
    """Flat context model holding every field that any prompt may consume.

    Pass the full memory dump as kwargs; Pydantic's ``extra="ignore"`` silently
    drops any key not declared here.  Individual prompt classes declare only
    the subset of fields they actually use, so passing a ``PromptContext``
    (or its ``model_dump()``) to a prompt class is safe and efficient.
    """

    model_config = ConfigDict(extra="ignore")

    # -- Persona --------------------------------------------------------------
    name: Optional[str] = None
    age: Optional[Any] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    religion: Optional[str] = None
    marriage_status: Optional[str] = None
    residence: Optional[str] = None
    occupation: Optional[str] = None
    education: Optional[str] = None
    personality: Optional[str] = None
    background_story: Optional[str] = None
    persona: Optional[str] = None

    # -- Big Five -------------------------------------------------------------
    openness: Optional[Any] = None
    conscientiousness: Optional[Any] = None
    extraversion: Optional[Any] = None
    agreeableness: Optional[Any] = None
    neuroticism: Optional[Any] = None

    # -- Needs ----------------------------------------------------------------
    hunger_satisfaction: Optional[float] = None
    energy_satisfaction: Optional[float] = None
    safety_satisfaction: Optional[float] = None
    social_satisfaction: Optional[float] = None
    current_need: Optional[str] = None

    # -- Emotion --------------------------------------------------------------
    sadness: Optional[Any] = None
    joy: Optional[Any] = None
    fear: Optional[Any] = None
    disgust: Optional[Any] = None
    anger: Optional[Any] = None
    surprise: Optional[Any] = None
    emotion_types: Optional[str] = None
    dominant_emotion: Optional[str] = None
    current_emotion: Optional[str] = None

    # -- Behavioral preferences -----------------------------------------------
    work_ethic: Optional[float] = None
    chronotype: Optional[str] = None
    social_frequency: Optional[float] = None
    leisure_preference: Optional[str] = None
    risk_tolerance: Optional[float] = None
    spending_tendency: Optional[float] = None

    # -- State / planning -----------------------------------------------------
    thought: Optional[str] = None
    current_thought: Optional[str] = None
    plan: Optional[Any] = None
    current_intention: Optional[str] = None
    intention: Optional[str] = None
    current_plan_target: Optional[str] = None
    plan_target: Optional[str] = None
    current_time: Optional[str] = None
    current_location: Optional[str] = None
    current_position: Optional[str] = None

    # -- Household / social ---------------------------------------------------
    household: Optional[str] = None
    life_stage: Optional[str] = None
    hobbies: Optional[Any] = None
    goals: Optional[Any] = None
    social_network: Optional[Any] = None

    # -- Economy --------------------------------------------------------------
    income: Optional[str] = None
    consumption: Optional[Any] = None
    family_consumption: Optional[str] = None
    skill: Optional[str] = None
    consumption_level: Optional[str] = None

    # -- Context-specific (only some prompts) ---------------------------------
    topic: Optional[str] = None
    previous_attitude: Optional[str] = None
    incident_text: Optional[str] = None
    plan_context: Optional[Any] = None
    poi_category: Optional[str] = None
    poi_name: Optional[str] = None
    observation: Optional[str] = None
    evaluation_results: Optional[str] = None
    intervention_message: Optional[str] = None
    current_action: Optional[str] = None
    day: Optional[str] = None
    block_start_time: Optional[str] = None
    block_duration: Optional[Any] = None
    block_description: Optional[str] = None
    ranked_areas: Optional[str] = None
    visit_history: Optional[str] = None
    aoi_list: Optional[str] = None
    area_type: Optional[str] = None
    second_types: Optional[str] = None
    weather: Optional[str] = None
    temperature: Optional[Any] = None
    other_information: Optional[Any] = None
    area_information: Optional[str] = None
    status_summary: Optional[str] = None
    other_info: Optional[str] = None


# ---------------------------------------------------------------------------
# BasePrompt — abstract base for all prompt classes
# ---------------------------------------------------------------------------

class BasePrompt(BaseModel):
    """Abstract base class for all prompt definitions.

    Subclasses must:
    1. Set ``name``, ``version``, and ``origin`` as ClassVar strings.
    2. Declare the prompt's input fields as Pydantic instance fields.
    3. Optionally define a nested ``class Output(BaseModel)`` for structured outputs.
    4. Implement ``format_prompt(self) -> str``.

    Because ``extra="ignore"`` is set, passing a complete flat context dict
    (e.g. from ``PromptManager._build_full_context``) is safe — fields not
    declared in the subclass are silently discarded.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # Metadata — ClassVar so Pydantic does NOT treat these as instance fields.
    name: ClassVar[str]
    version: ClassVar[str]
    origin: ClassVar[str]
    description: ClassVar[str] = ""

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------

    @classmethod
    def get_version(cls) -> tuple[int, ...]:
        """Return the version as a comparable tuple, e.g. (1, 0, 0)."""
        try:
            return tuple(map(int, cls.version.replace("v", "").split(".")))
        except (ValueError, AttributeError):
            return (0, 0, 0)

    @classmethod
    def get_input_schema(cls) -> dict[str, dict]:
        """Return ``{field_name: {"type": ..., "description": ...}}`` for all declared fields."""
        result: dict[str, dict] = {}
        for field_name, field_info in cls.model_fields.items():
            annotation = field_info.annotation
            type_str = _python_type_to_schema_type(annotation)
            result[field_name] = {
                "type": type_str,
                "description": field_info.description or "",
            }
        return result

    @classmethod
    def get_output_schema(cls) -> dict[str, dict]:
        """Return output schema derived from the nested ``Output`` model, if defined."""
        output_cls = getattr(cls, "Output", None)
        if output_cls is None or not (isinstance(output_cls, type) and issubclass(output_cls, BaseModel)):
            return {}
        result: dict[str, dict] = {}
        for field_name, field_info in output_cls.model_fields.items():
            annotation = field_info.annotation
            type_str = _python_type_to_schema_type(annotation)
            result[field_name] = {
                "type": type_str,
                "description": field_info.description or "",
            }
        return result

    @classmethod
    def requires_free_text_generation(cls) -> bool:
        """Return True when the prompt produces free-text (not purely structured) output."""
        schema = cls.get_output_schema()
        if not schema:
            return True
        structured_types = {"categorical", "float", "integer"}
        return any(
            str(f.get("type", "")).lower() not in structured_types
            for f in schema.values()
        )

    @classmethod
    def is_cache_eligible(cls) -> bool:
        """Return True when all outputs are structured (no free-text generation needed)."""
        return not cls.requires_free_text_generation()

    # ------------------------------------------------------------------
    # Instance methods — implemented by concrete subclasses
    # ------------------------------------------------------------------

    def format_prompt(self) -> str:
        """Return the fully-formatted prompt string using instance field values."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement format_prompt()"
        )

    def format_prompt_to_dialog(self) -> list[dict[str, str]]:
        """Return the prompt as an OpenAI-compatible dialog list."""
        return [{"role": "user", "content": self.format_prompt()}]
