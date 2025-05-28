from typing import Optional

from pydantic import BaseModel
from sqlalchemy import ForeignKey, String, BigInteger, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import BaseNoInit

__all__ = ["MLflowRun", "MLflowMetric", "ApiMLflowMetric"]

# Database Models


class MLflowRun(BaseNoInit):
    """MLflow run model"""

    __tablename__ = "runs"

    run_uuid: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(250))
    source_type: Mapped[Optional[str]] = mapped_column(String(20))
    source_name: Mapped[Optional[str]] = mapped_column(String(500))
    entry_point_name: Mapped[Optional[str]] = mapped_column(String(50))
    user_id: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[Optional[str]] = mapped_column(String(9))
    start_time: Mapped[Optional[int]] = mapped_column(BigInteger)
    end_time: Mapped[Optional[int]] = mapped_column(BigInteger)
    source_version: Mapped[Optional[str]] = mapped_column(String(50))
    lifecycle_stage: Mapped[Optional[str]] = mapped_column(String(20))
    artifact_uri: Mapped[Optional[str]] = mapped_column(String(200))
    experiment_id: Mapped[Optional[int]] = mapped_column()
    deleted_time: Mapped[Optional[int]] = mapped_column(BigInteger)

    # Relationships
    metrics: Mapped[list["MLflowMetric"]] = relationship(back_populates="run")


class MLflowMetric(BaseNoInit):
    """MLflow metric model"""

    __tablename__ = "metrics"

    key: Mapped[str] = mapped_column(String(250), primary_key=True)
    value: Mapped[float] = mapped_column(Float, primary_key=True)
    timestamp: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_uuid: Mapped[str] = mapped_column(
        String(32), ForeignKey("runs.run_uuid"), primary_key=True
    )
    step: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=0)
    is_nan: Mapped[bool] = mapped_column(Boolean, primary_key=True, default=False)

    # Relationships
    run: Mapped["MLflowRun"] = relationship(back_populates="metrics")


# API Models


class ApiMLflowMetric(BaseModel):
    """MLflow metric model for API"""

    key: str
    """Metric key"""
    value: float
    """Metric value"""
    step: int
    """Step number"""
    is_nan: bool
    """Whether the value is NaN"""

    class Config:
        from_attributes = True
