from typing import Optional, Union

from ..environment.sim.person_service import VehicleConfigurableAttributes
from pydantic import BaseModel, Field

from ..filesystem import FileSystemClient
from ..s3 import S3Client, S3Config
from ..storage import DatabaseConfig

__all__ = [
    "EnvConfig",
]


# default_car_attribute = VehicleConfigurableAttributes(
#   max_speed=60 / 3.6, # 60 km/h to m/s
# )

# default_taxi_attribute = VehicleConfigurableAttributes(
#   max_speed=60 / 3.6, # 60 km/h to m/s
# )

# default_bus_attribute = VehicleConfigurableAttributes(
#   max_speed=50 / 3.6, # 50 km/h to m/s
# )

# default_subway_attribute = VehicleConfigurableAttributes(
#   max_speed=80 / 3.6, # 60 km/h to m/s
# )

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

    finetune_data_dir: Optional[str] = Field(default=None)
    """Directory for finetune data, if not set, use home_dir/finetune_data"""

    modernbert_model_path: Optional[str] = Field(default=None)
    """Path to the ModernBERT model, if not set, ModernBERT features will be disabled"""

    catboost_model_path: Optional[str] = Field(default=None)
    """Path to the CatBoost model, if not set, CatBoost features will be disabled"""

    needs_pca_path: Optional[str] = Field(default=None)
    """Path to the NEEDS PCA model, if not set, NEEDS PCA features will be disabled"""

    needs_mahalanobis_params_path: Optional[str] = Field(default=None)
    """Path to the Mahalanobis parameters, if not set, Mahalanobis features will be disabled"""

    enforce_place_selection: bool = Field(default=False) # TODO
    """Whether to enforce place selection in the environment"""

    dispatcher_catboost_path: Optional[str] = Field(default=None)
    """Path to the CatBoost dispatcher model, if not set, speed up dispatcher features will be disabled"""

    use_transportation_mode_choice: bool = Field(default=False) # TODO
    """Whether to use transportation mode choice model"""

    car_attributes: VehicleConfigurableAttributes = Field(default=default_car_attribute)
    """Default car attributes for vehicles in the environment"""

    taxi_attributes: VehicleConfigurableAttributes = Field(default=default_taxi_attribute)
    """Default taxi attributes for vehicles in the environment"""

    bus_attributes: VehicleConfigurableAttributes = Field(default=default_bus_attribute)
    """Default bus attributes for vehicles in the environment"""

    subway_attributes: VehicleConfigurableAttributes = Field(default=default_subway_attribute)
    """Default subway attributes for vehicles in the environment"""


    @property
    def fs_client(self) -> Union[S3Client, FileSystemClient]:
        if self.s3.enabled:
            return S3Client(self.s3)
        else:
            return FileSystemClient(self.home_dir)
