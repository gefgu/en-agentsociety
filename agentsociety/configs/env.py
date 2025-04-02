from typing import List, Optional

from pydantic import BaseModel

from ..message import RedisConfig
from ..metrics import MlflowConfig
from ..storage import AvroConfig, PostgreSQLConfig

__all__ = [
    "EnvConfig",
]


class EnvConfig(BaseModel):
    """Environment configuration class."""

    redis: RedisConfig
    """Redis configuration"""

    pgsql: PostgreSQLConfig
    """PostgreSQL configuration"""

    avro: AvroConfig
    """Avro configuration"""

    mlflow: MlflowConfig
    """MLflow configuration"""
