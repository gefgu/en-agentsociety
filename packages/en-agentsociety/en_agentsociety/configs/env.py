from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from ..filesystem import FileSystemClient
from ..llm.cache.config import QdrantCacheConfig
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

    resume_config_mismatch_action: Literal["error", "warn"] = "error"

    clickhouse: ClickHouseConfig = Field(
        default_factory=lambda: ClickHouseConfig.model_validate({})
    )
    """ClickHouse telemetry configuration"""

    monitoring_enabled: bool = Field(default=True)
    """Whether to start the Docker-based monitoring stack (Prometheus/Grafana).
    Set to false to skip starting the stack, e.g. in e2e tests or when a monitoring
    stack is already running."""

    database_enabled: bool = Field(default=True)
    """Whether to initialize the database actor. Set to false to skip database
    initialization, e.g. in e2e tests that don't require telemetry."""

    llm_response_storage: Literal["lightview", "detailed"] = Field(default="detailed")
    """Storage mode for LLM prompt/response telemetry. Use 'lightview' to store
    metadata only, or 'detailed' to store full prompt and response payloads."""

    resume_rollback_depth: int = Field(default=10, ge=0)
    """Maximum number of older checkpoints to try when the latest checkpoint is
    invalid during resume. 0 means fail immediately on the first bad step."""

    qdrant_cache: QdrantCacheConfig = Field(default_factory=QdrantCacheConfig)
    """Qdrant-backed LLM semantic cache configuration."""

    sim_bin_name: Optional[str] = Field(default=None)
    """Custom simulator binary name inside home_dir. When set, this filename is used
    instead of downloading the default agentsociety-sim-oss binary. The file must
    already exist at home_dir/<sim_bin_name>. Leave None to use the default
    download behavior. Example: 'agentsociety-sim-oss_mine'."""


    @property
    def fs_client(self) -> Union[S3Client, FileSystemClient]:
        if self.s3.enabled:
            return S3Client(self.s3)
        else:
            return FileSystemClient(self.home_dir)
