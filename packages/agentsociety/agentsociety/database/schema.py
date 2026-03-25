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
