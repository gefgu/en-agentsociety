"""
A clear version of the simulation.
"""

from typing import Union


from ..configs import (
    Config,
    IndividualConfig,
)
from .simulationengine import SimulationEngine
from .individualengine import IndividualEngine

__all__ = ["AgentSociety"]


class AgentSociety:
    """
    Factory class for creating simulation engines based on configuration type.
    
    - **Description**:
        - A factory class that creates and returns the appropriate engine instance
        based on the configuration type provided.
        - Returns SimulationEngine for Config type
        - Returns TaskSolverEngine for SolverConfig type
    """
    
    @staticmethod
    def create(
        config: Union[Config, IndividualConfig],
        tenant_id: str = "",
    ) -> Union[SimulationEngine, IndividualEngine]:
        """
        Create and return the appropriate engine instance based on configuration type.
        
        - **Description**:
            - Factory method that creates the appropriate engine instance based on the
            configuration type provided.
            - For Config type: returns SimulationEngine instance
            - For IndividualConfig type: returns IndividualEngine instance
            
        - **Args**:
            - `config` (Union[Config, IndividualConfig]): The configuration object that determines
            which engine to create.
            - `tenant_id` (str, optional): The tenant ID for the engine. Defaults to "".
            
        - **Returns**:
            - `Union[SimulationEngine, IndividualEngine]`: The appropriate engine instance
            based on the configuration type.
            
        - **Raises**:
            - `ValueError`: If the configuration type is not supported.
        """
        if isinstance(config, Config):
            return SimulationEngine(config, tenant_id)
        elif isinstance(config, IndividualConfig):
            return IndividualEngine(config, tenant_id)
        else:
            raise ValueError(f"Invalid config type: {type(config)}. Expected Config or IndividualConfig.")

