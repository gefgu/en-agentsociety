import datetime
from typing import List, Optional, TypedDict


class AdjustNeedsRecord(TypedDict):
    exp_id: Optional[str]
    timestamp: datetime
    agent_id: int
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


class PromptResponseRecord(TypedDict):
    exp_id: str
    simulation_step: int
    timestamp: datetime
    agent_id: int
    prompt: str
    response: str
    block_name: str
    func_name: str


class AgentLocationTypeRecord(TypedDict):
    exp_id: str
    simulation_step: int
    timestamp: datetime
    agent_id: int
    location_type: str


class AgentTransportTypeRecord(TypedDict):
    exp_id: str
    simulation_step: int
    timestamp: datetime
    agent_id: int
    transport_type: str


class StepAgentStatusRecord(TypedDict):
    exp_id: str
    agent_id: int
    simulation_step: int
    timestamp: datetime
    lat: float
    lng: float
    parent_id: int
    action: str
    status: str


class BlockDispatcherRecord(TypedDict):
    exp_id: str
    agent_id: int
    simulation_step: int
    timestamp: datetime
    target_block: str
    reason: str
    possible_blocks: List[str]
    ctx_time: str
    ctx_need: str
    ctx_intention: str
    ctx_emotion: str
    ctx_thought: str
    ctx_location: str
    ctx_area_info: str
    ctx_weather: str
    ctx_temperature: int
    ctx_other_info: str
    ctx_plan_target: str


class AgentKVSnapshotRecord(TypedDict):
    exp_id: str
    simulation_step: int
    agent_id: int
    key: str
    value_json: str


class AgentStreamSnapshotRecord(TypedDict):
    exp_id: str
    simulation_step: int
    agent_id: int
    memory_id: int
    cognition_id: Optional[int]
    topic: str
    location: str
    description: str
    day: int
    t: float


class AgentSpatialSnapshotRecord(TypedDict):
    exp_id: str
    simulation_step: int
    agent_id: int
    location_id: str
    description: str
    price: float
    atmosphere: float
    satisfaction: float
    convenience: float
    uncertainty: float


class PendingMessageSnapshotRecord(TypedDict):
    exp_id: str
    simulation_step: int
    from_id: Optional[int]
    to_id: Optional[int]
    day: int
    t: float
    kind: str
    payload_json: str
    created_at: datetime.datetime
    extra_json: Optional[str]


class _ExperimentInfoRecordRequired(TypedDict):
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


class ExperimentInfoRecord(_ExperimentInfoRecordRequired, total=False):
    """TypedDict for a row in the experiment_info ClickHouse table.

    The required fields mirror the original 12-column schema. The optional
    fields correspond to checkpoint columns added in migration 0013 and are
    filled with defaults by ``insert_experiment_info_record`` when absent.
    """

    last_mobility_safe_step: int
    prev_mobility_safe_step: int
    economy_checkpoint_path: str
