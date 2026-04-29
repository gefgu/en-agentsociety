from datetime import datetime
import json
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatabaseRecordModel(BaseModel):
    """Base schema model for DB records with shared coercion rules."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @classmethod
    def column_names(cls) -> list[str]:
        return list(cls.model_fields.keys())

    def as_record(self) -> dict[str, Any]:
        return self.model_dump(mode="python")

    @field_validator(
        "simulation_step",
        "agent_id",
        "parent_id",
        "memory_id",
        "day",
        "num_day",
        "cur_day",
        "input_tokens",
        "output_tokens",
        "last_mobility_safe_step",
        "prev_mobility_safe_step",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def _coerce_int(cls, value: Any) -> int:
        if value is None:
            return -1
        try:
            return int(value)
        except (TypeError, ValueError):
            return -1

    @field_validator(
        "lat",
        "lng",
        "price",
        "atmosphere",
        "satisfaction",
        "convenience",
        "uncertainty",
        "cur_t",
        "t",
        "current_hunger",
        "current_energy",
        "current_safety",
        "current_social",
        "new_hunger",
        "new_energy",
        "new_safety",
        "new_social",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def _coerce_float(cls, value: Any) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @field_validator(
        "timestamp",
        "created_at",
        "updated_at",
        "created_at",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def _coerce_datetime(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.now()
        return datetime.now()

    @field_validator(
        "exp_id",
        "tenant_id",
        "name",
        "config",
        "error",
        "key",
        "value_json",
        "location_type",
        "transport_type",
        "action",
        "status",
        "status_text",
        "target_block",
        "reason",
        "ctx_time",
        "ctx_need",
        "ctx_intention",
        "ctx_emotion",
        "ctx_thought",
        "ctx_location",
        "ctx_area_info",
        "ctx_weather",
        "ctx_other_info",
        "ctx_plan_target",
        "topic",
        "location",
        "description",
        "location_id",
        "kind",
        "payload_json",
        "extra_json",
        "prompt",
        "response",
        "block_name",
        "func_name",
        "actor",
        "current_need",
        "economy_checkpoint_path",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def _coerce_string(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    @field_validator("id", mode="before", check_fields=False)
    @classmethod
    def _coerce_uuid_string(cls, value: Any) -> str:
        return str(uuid.UUID(str(value)))

    @field_validator("possible_blocks", mode="before", check_fields=False)
    @classmethod
    def _coerce_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        if isinstance(value, tuple) or isinstance(value, set):
            return [str(v) for v in value]
        if isinstance(value, str):
            try:
                loaded = json.loads(value)
                if isinstance(loaded, list):
                    return [str(v) for v in loaded]
            except json.JSONDecodeError:
                pass
            return [value]
        return []


class AdjustNeedsRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: int = -1
    prompt: str
    actor: str
    current_need: str
    current_hunger: float
    current_energy: float
    current_safety: float
    current_social: float
    new_hunger: float
    new_energy: float
    new_safety: float
    new_social: float


class PromptResponseRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: int = -1
    prompt: str
    response: str
    block_name: str
    func_name: str


class AgentLocationTypeRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: int = -1
    location_type: str


class AgentTransportTypeRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: int = -1
    transport_type: str


class StepAgentStatusRecord(DatabaseRecordModel):
    exp_id: str = ""
    agent_id: int = -1
    simulation_step: int = -1
    timestamp: datetime = Field(default_factory=datetime.now)
    lat: float
    lng: float
    parent_id: int = -1
    action: str
    status: str


class BlockDispatcherRecord(DatabaseRecordModel):
    exp_id: str = ""
    agent_id: int = -1
    simulation_step: int = -1
    timestamp: datetime = Field(default_factory=datetime.now)
    target_block: str = ""
    reason: str = ""
    possible_blocks: list[str] = Field(default_factory=list)
    ctx_time: str = ""
    ctx_need: str = ""
    ctx_intention: str = ""
    ctx_emotion: str = ""
    ctx_thought: str = ""
    ctx_location: str = ""
    ctx_area_info: str = ""
    ctx_weather: str = ""
    ctx_temperature: int = 0
    ctx_other_info: str = ""
    ctx_plan_target: str = ""


class AgentKVSnapshotRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    agent_id: int = -1
    key: str
    value_json: str


class AgentStreamSnapshotRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    agent_id: int = -1
    memory_id: int
    cognition_id: int | None = None
    topic: str = ""
    location: str = ""
    description: str = ""
    day: int = 0
    t: float = 0.0


class AgentSpatialSnapshotRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    agent_id: int = -1
    location_id: str
    description: str = ""
    price: float = 0.0
    atmosphere: float = 0.0
    satisfaction: float = 0.0
    convenience: float = 0.0
    uncertainty: float = 0.0


class PendingMessageSnapshotRecord(DatabaseRecordModel):
    exp_id: str = ""
    simulation_step: int = -1
    from_id: int | None = None
    to_id: int | None = None
    day: int = 0
    t: float = 0.0
    kind: str = ""
    payload_json: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    extra_json: str | None = None


class ExperimentInfoRecord(DatabaseRecordModel):
    """Schema for a row in experiment_info with checkpoint fields."""

    tenant_id: str
    id: str
    name: str
    num_day: int
    status: int
    cur_day: int
    cur_t: float
    config: str
    error: str
    input_tokens: int
    output_tokens: int
    created_at: datetime
    updated_at: datetime
    last_mobility_safe_step: int = -1
    prev_mobility_safe_step: int = -1
    economy_checkpoint_path: str = ""
