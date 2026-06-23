import uuid
from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    JSON,
    UUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from ._base import TABLE_PREFIX, Base

__all__ = [
    "agent_survey",
    "agent_dialog",
    "global_prompt",
    "pending_dialog",
    "pending_survey",
]


def agent_survey(table_name: str):
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("experiment_id", String, nullable=True),
        Column("id", Integer),
        Column("day", Integer),
        Column("t", Float),
        Column("survey_id", UUID),
        Column("result", JSON),
        Column("created_at", TIMESTAMP(timezone=True)),
    ), ["experiment_id", "id", "day", "t", "survey_id", "result", "created_at"]


def agent_dialog(table_name: str):
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("experiment_id", String, nullable=True),
        Column("id", Integer),
        Column("day", Integer),
        Column("t", Float),
        Column("type", Integer),
        Column("speaker", String),
        Column("content", String),
        Column("created_at", TIMESTAMP(timezone=True)),
    ), ["experiment_id", "id", "day", "t", "type", "speaker", "content", "created_at"]


def global_prompt(table_name: str):
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("experiment_id", String, nullable=True),
        Column("day", Integer),
        Column("t", Float),
        Column("prompt", String),
        Column("created_at", TIMESTAMP(timezone=True)),
    ), ["experiment_id", "day", "t", "prompt", "created_at"]


def pending_dialog(table_name: str):
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("experiment_id", String, nullable=True),
        Column("agent_id", Integer),
        Column("day", Integer),
        Column("t", Float),
        Column("content", String),
        Column("created_at", TIMESTAMP(timezone=True)),
        Column("processed", Boolean, default=False),
    ), ["id", "experiment_id", "agent_id", "day", "t", "content", "created_at", "processed"]


def pending_survey(table_name: str):
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("experiment_id", String, nullable=True),
        Column("agent_id", Integer),
        Column("day", Integer),
        Column("t", Float),
        Column("survey_id", UUID),
        Column("data", JSON),
        Column("created_at", TIMESTAMP(timezone=True)),
        Column("processed", Boolean, default=False),
    ), ["id", "experiment_id", "agent_id", "day", "t", "survey_id", "data", "created_at", "processed"]


def experiment_info(table_name: str):
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        Column("experiment_id", String, primary_key=True),
        Column("tenant_id", String),
        Column("name", String),
        Column("num_day", Integer),
        Column("status", Integer),
        Column("cur_day", Integer),
        Column("cur_t", Float),
        Column("config", String),
        Column("error", String),
        Column("input_tokens", Integer, default=0),
        Column("output_tokens", Integer, default=0),
        Column("created_at", TIMESTAMP(timezone=True)),
        Column("updated_at", TIMESTAMP(timezone=True)),
    ), ["experiment_id", "tenant_id", "name", "num_day", "status", "cur_day", "cur_t", "config", "error", "input_tokens", "output_tokens", "created_at", "updated_at"]


class Experiment(Base):
    """Experiment model (kept for web API management tables backward compatibility)"""

    __tablename__ = f"{TABLE_PREFIX}experiment"

    tenant_id: Mapped[str] = mapped_column(primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    num_day: Mapped[int] = mapped_column()
    status: Mapped[int] = mapped_column()
    cur_day: Mapped[int] = mapped_column()
    cur_t: Mapped[float] = mapped_column()
    config: Mapped[str] = mapped_column()
    error: Mapped[str] = mapped_column()
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    @property
    def agent_dialog_tablename(self):
        return "dialog"

    @property
    def agent_survey_tablename(self):
        return "survey"

    @property
    def global_prompt_tablename(self):
        return "global_prompt"

    @property
    def pending_dialog_tablename(self):
        return "pending_dialog"

    @property
    def pending_survey_tablename(self):
        return "pending_survey"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "num_day": self.num_day,
            "status": self.status,
            "cur_day": self.cur_day,
            "cur_t": self.cur_t,
            "config": self.config,
            "error": self.error,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
