import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import AwareDatetime, BaseModel
from sqlalchemy.orm import Mapped, mapped_column

from ._base import TABLE_PREFIX, Base

__all__ = [
    "AgentProfile",
]


class AgentProfile(Base):
    """Agent profile data model for storing metadata about agent data files"""

    __tablename__ = f"{TABLE_PREFIX}agent_profile_data"

    tenant_id: Mapped[str] = mapped_column(primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column()
    agent_type: Mapped[str] = mapped_column()
    file_path: Mapped[str] = mapped_column()  # Path to the S3 file
    record_count: Mapped[int] = mapped_column()  # Number of records in the file
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )
