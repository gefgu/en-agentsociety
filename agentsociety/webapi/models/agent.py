import enum
import uuid
from typing import Any, Optional

from pydantic import BaseModel, AwareDatetime
from sqlalchemy import TIMESTAMP, Column, Float, Integer, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB, UUID

__all__ = [
    "agent_dialog",
    "agent_profile",
    "agent_status",
    "agent_survey",
    "global_prompt",
    "AgentDialogType",
    "ApiAgentDialog",
    "ApiAgentProfile",
    "ApiAgentStatus",
    "ApiAgentSurvey",
    "ApiGlobalPrompt",
]

# Database Models


def agent_profile(table_name: str):
    """Create agent profile table"""
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("id", Integer),
        Column("name", String),
        Column("profile", JSONB),
    ), ["id", "name", "profile"]


def agent_status(table_name: str):
    """Create agent status table"""
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("id", Integer),
        Column("day", Integer),
        Column("t", Float),
        Column("lng", Float, nullable=True),
        Column("lat", Float, nullable=True),
        Column("parent_id", Integer),
        Column("action", String),
        Column("status", JSONB),
        Column("created_at", TIMESTAMP(timezone=True)),
    ), ["id", "day", "t", "lng", "lat", "parent_id", "action", "status", "created_at"]


def agent_survey(table_name: str):
    """Create agent survey table"""
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("id", Integer),
        Column("day", Integer),
        Column("t", Float),
        Column("survey_id", UUID),
        Column("result", JSONB),
        Column("created_at", TIMESTAMP(timezone=True)),
    ), ["id", "day", "t", "survey_id", "result", "created_at"]


def agent_dialog(table_name: str):
    """Create agent dialog table"""
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("id", Integer),
        Column("day", Integer),
        Column("t", Float),
        Column("type", Integer),
        Column("speaker", String),
        Column("content", String),
        Column("created_at", TIMESTAMP(timezone=True)),
    ), ["id", "day", "t", "type", "speaker", "content", "created_at"]


def global_prompt(table_name: str):
    """Create global prompt table"""
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("day", Integer),
        Column("t", Float),
        Column("prompt", String),
        Column("created_at", TIMESTAMP(timezone=True)),
    ), ["day", "t", "prompt", "created_at"]


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
