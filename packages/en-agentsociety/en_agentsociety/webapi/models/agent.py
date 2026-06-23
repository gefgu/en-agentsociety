import enum
import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, AwareDatetime

from ...storage import (
    agent_dialog,
    agent_survey,
    global_prompt,
    pending_dialog,
    pending_survey,
)

__all__ = [
    "agent_dialog",
    "agent_survey",
    "global_prompt",
    "pending_dialog",
    "pending_survey",
    "AgentDialogType",
    "ApiAgentDialog",
    "ApiAgentProfile",
    "ApiAgentStatus",
    "ApiAgentSurvey",
    "ApiGlobalPrompt",
    "ApiBlockExecution",
    "ApiTimelineStep",
    "ApiDailyScheduleBlock",
    "ApiDailySchedule",
]

# Database Models


class AgentDialogType(enum.IntEnum):
    """Agent dialog type"""

    Thought = 0  # Dialog in agent self
    Talk = 1  # Dialog with other agents
    User = 2  # Dialog with user


class ApiAgentProfile(BaseModel):
    """Agent profile model for API"""

    id: int
    """Agent ID"""
    name: str
    """Agent name"""
    profile: Any
    """Agent profile (any JSON object)"""

    class Config:
        from_attributes = True


class ApiAgentStatus(BaseModel):
    """Agent status model for API"""

    id: int
    """Agent ID"""
    day: int
    """Day"""
    t: float
    """Time (second)"""
    lng: Optional[float]
    """Longitude"""
    lat: Optional[float]
    """Latitude"""
    parent_id: Optional[int]
    """Parent agent ID"""
    action: str
    """Action"""
    status: Any
    """Status (any JSON object)"""
    created_at: AwareDatetime
    """Created time"""

    class Config:
        from_attributes = True


class ApiAgentSurvey(BaseModel):
    """Agent survey model for API"""

    id: int
    """Agent ID"""
    day: int
    """Day"""
    t: float
    """Time (second)"""
    survey_id: uuid.UUID
    """Survey ID"""
    result: Any
    """Survey result (any JSON object)"""
    created_at: AwareDatetime
    """Created time"""

    class Config:
        from_attributes = True


class ApiAgentDialog(BaseModel):
    """Agent dialog model for API"""

    id: int
    """Agent ID"""
    day: int
    """Day"""
    t: float
    """Time (second)"""
    type: AgentDialogType
    """Dialog type"""
    speaker: str
    """Speaker"""
    content: str
    """Content"""
    created_at: AwareDatetime
    """Created time"""

    class Config:
        from_attributes = True


class ApiGlobalPrompt(BaseModel):
    """Global prompt model for API"""

    day: int
    """Day"""
    t: float
    """Time (second)"""
    prompt: str
    """Prompt"""
    created_at: AwareDatetime
    """Created time"""

    class Config:
        from_attributes = True


class ApiBlockExecution(BaseModel):
    """A single LLM call within a simulation step"""

    block_name: str
    func_name: str = ""
    prompt: str = ""
    response: str = ""
    detail_available: int = 1


class ApiTimelineStep(BaseModel):
    """All block executions at one simulation step"""

    simulation_step: int
    block_executions: List[ApiBlockExecution]


class ApiDailyScheduleBlock(BaseModel):
    """One time-block in a CitySim daily schedule"""

    start_time: str
    duration: int
    activity: str
    description: str = ""


class ApiDailySchedule(BaseModel):
    """LLM-generated daily schedule for a CitySim agent"""

    day: int
    blocks: List[ApiDailyScheduleBlock]
    generated_at: str = ""
