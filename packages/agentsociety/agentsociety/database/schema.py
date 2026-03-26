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


class StaticAgentAttributesRecord(TypedDict):
    exp_id: str
    simulation_step: int
    timestamp: datetime
    agent_id: int
    type: str
    home_aoi_id: int
    work_aoi_id: int
    name: str
    gender: str
    age: int
    education: str
    household: str
    life_stage: str
    skill: str
    occupation: str
    work_skill: float
    firm_id: int
    government_id: int
    bank_id: int
    nbs_id: int
    preferences_chronotype: str
    preferences_risk_tolerance: float
    preferences_spending_tendency: float
    preferences_social_frequency: float
    preferences_work_ethic: float
    preferences_leisure_preference: str
    hobbies: List[str]
    personality: str
    big5_openness: int
    big5_conscientiousness: int
    big5_extraversion: int
    big5_agreeableness: int
    big5_neuroticism: int
    income: float
    currency: float
    residence: str
    city: str
    race: str
    religion: str
    marriage_status: str
    background_story: str


class ExperimentInfoRecord(TypedDict):
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
