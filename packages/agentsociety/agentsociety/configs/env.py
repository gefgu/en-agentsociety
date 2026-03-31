from typing import Optional, Union

from pydantic import BaseModel, Field

from ..filesystem import FileSystemClient
from ..s3 import S3Client, S3Config
from ..storage import DatabaseConfig

__all__ = [
    "EnvConfig",
    "ClickHouseConfig",
]


class ClickHouseConfig(BaseModel):
    """ClickHouse connection configuration for telemetry storage."""

    host: str = Field(default="localhost")
    """ClickHouse host"""

    port: int = Field(default=8123)
    """ClickHouse HTTP port"""

    username: str = Field(default="default")
    """ClickHouse username"""

    password: str = Field(default="clickhouse")
    """ClickHouse password"""

    database: str = Field(default="fastsociety")
    """ClickHouse database name"""

    batch_size: int = Field(default=128)
    """Batch size for batched inserts"""

    batch_timeout: float = Field(default=30.0)
    """Flush timeout in seconds for batched inserts"""

    auto_create_database: bool = Field(default=True)
    """Whether to create the database automatically if missing"""


class EnvConfig(BaseModel):
    """Environment configuration class."""

    db: DatabaseConfig
    """Database configuration"""

    s3: S3Config = Field(default_factory=lambda: S3Config.model_validate({}))
    """S3 configuration, if enabled, the file will be downloaded from S3"""

    home_dir: str = Field(default="./agentsociety_data")
    """Home directory for AgentSociety's webui if s3 is not enabled"""
    
    data_dir: str = Field(default="./agentsociety_data/data")
    """Directory for storing data files"""

    exp_id: Optional[str] = Field(default=None)

    clickhouse: ClickHouseConfig = Field(
        default_factory=lambda: ClickHouseConfig.model_validate({})
    )
    """ClickHouse telemetry configuration"""

    monitoring_enabled: bool = Field(default=True)
    """Whether to start the Docker-based monitoring stack (Prometheus/Grafana/ClickHouse).
    Set to false to skip starting the stack, e.g. in e2e tests or when a monitoring
    stack is already running."""


    @property
    def fs_client(self) -> Union[S3Client, FileSystemClient]:
        if self.s3.enabled:
            return S3Client(self.s3)
        else:
            return FileSystemClient(self.home_dir)
