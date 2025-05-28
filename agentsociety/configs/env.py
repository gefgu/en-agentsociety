from typing import List, Optional, Union

from pydantic import BaseModel, Field

from ..message import RedisConfig
from ..metrics import MlflowConfig
from ..storage import AvroConfig, PostgreSQLConfig
from ..s3 import S3Config, S3Client
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

    s3: S3Config = Field(default_factory=lambda: S3Config.model_validate({}))
    """S3 configuration, if enabled, the file will be downloaded from S3"""

    webui_home_dir: str = Field(default="./agentsociety_data")
    """Home directory for AgentSociety's webui if s3 is not enabled"""

    @property
    def webui_fs_client(self) -> Union[S3Client, FileSystemClient]:
        if self.s3.enabled:
            return S3Client(self.s3)
        else:
            return FileSystemClient(self.webui_home_dir)
