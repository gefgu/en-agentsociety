from typing import List, Optional, Union

from pydantic import BaseModel, Field

from ..message import RedisConfig
from ..metrics import MlflowConfig
from ..storage import AvroConfig, PostgreSQLConfig
from ..filesystem import FileSystemClient

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

    webui_home_dir: str = Field(default="./agentsociety_data")
    """Home directory for AgentSociety's webui if s3 is not enabled"""

    @property
    def webui_fs_client(self) -> FileSystemClient:
        return FileSystemClient(self.webui_home_dir)
