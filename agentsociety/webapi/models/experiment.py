import enum
import uuid
from datetime import datetime

from pydantic import AwareDatetime, BaseModel
from sqlalchemy.orm import Mapped, mapped_column

from ._base import TABLE_PREFIX, Base

__all__ = ["Experiment", "ExperimentStatus", "ApiExperiment", "ApiTime"]

# Database Models


class ExperimentStatus(enum.IntEnum):
    """Experiment status"""

    NOT_STARTED = 0  # The experiment is not started
    RUNNING = 1  # The experiment is running
    FINISHED = 2  #  The experiment is finished
    ERROR = 3  # The experiment has error and stopped


class Experiment(Base):
    """Experiment model"""

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
    def agent_profile_tablename(self):
        """Get agent profile table name"""
        return f"{TABLE_PREFIX}{str(self.id).replace('-', '_')}_agent_profile"

    @property
    def agent_status_tablename(self):
        """Get agent status table name"""
        return f"{TABLE_PREFIX}{str(self.id).replace('-', '_')}_agent_status"

    @property
    def agent_dialog_tablename(self):
        """Get agent dialog table name"""
        return f"{TABLE_PREFIX}{str(self.id).replace('-', '_')}_agent_dialog"

    @property
    def agent_survey_tablename(self):
        """Get agent survey table name"""
        return f"{TABLE_PREFIX}{str(self.id).replace('-', '_')}_agent_survey"

    @property
    def global_prompt_tablename(self):
        """Get global prompt table name"""
        return f"{TABLE_PREFIX}{str(self.id).replace('-', '_')}_global_prompt"

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


# API Request & Response Models
# class ExperimentBase(BaseModel):
#     """TODO"""

#     name: str
#     num_day: int
#     config: Optional[str] = None


# class ExperimentCreate(ExperimentBase):
#     """TODO"""

#     pass


class ApiExperiment(BaseModel):
    """Experiment model for API"""

    tenant_id: str
    """Tenant ID"""
    id: uuid.UUID
    """Experiment ID"""
    name: str
    """Experiment name"""
    num_day: int
    """Number of days"""
    status: ExperimentStatus
    """Experiment status"""
    cur_day: int
    """Current day"""
    cur_t: float
    """Current time (second)"""
    config: str
    """Experiment configuration"""
    error: str
    """Error message"""
    input_tokens: int
    """Input tokens"""
    output_tokens: int
    """Output tokens"""
    created_at: AwareDatetime
    """Created time"""
    updated_at: AwareDatetime
    """Updated time"""

    class Config:
        from_attributes = True


class ApiTime(BaseModel):
    """Time model for API"""

    day: int
    t: float
