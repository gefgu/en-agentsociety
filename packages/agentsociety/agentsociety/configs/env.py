from typing import Optional, Union

from pydantic import BaseModel, Field

from ..filesystem import FileSystemClient
from ..s3 import S3Client, S3Config
from ..storage import DatabaseConfig

__all__ = [
    "EnvConfig",
]


class EnvConfig(BaseModel):
    """Environment configuration class."""

    db: DatabaseConfig
    """Database configuration"""

    s3: S3Config = Field(default_factory=lambda: S3Config.model_validate({}))
    """S3 configuration, if enabled, the file will be downloaded from S3"""

    home_dir: str = Field(default="./agentsociety_data")
    """Home directory for AgentSociety's webui if s3 is not enabled"""

    finetune_data_dir: Optional[str] = Field(default=None)
    """Directory for finetune data, if not set, use home_dir/finetune_data"""

    modernbert_model_path: Optional[str] = Field(default=None)
    """Path to the ModernBERT model, if not set, ModernBERT features will be disabled"""

    catboost_model_path: Optional[str] = Field(default=None)
    """Path to the CatBoost model, if not set, CatBoost features will be disabled"""

    @property
    def fs_client(self) -> Union[S3Client, FileSystemClient]:
        if self.s3.enabled:
            return S3Client(self.s3)
        else:
            return FileSystemClient(self.home_dir)
