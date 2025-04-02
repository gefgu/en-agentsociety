import math
from typing import Any, Awaitable, Callable, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_serializer
import psutil
from ..environment import MapConfig, SimulatorConfig
from ..llm import LLMConfig
from .agent import AgentClassType, AgentConfig
from .env import EnvConfig
from .exp import (
    EnvironmentConfig,
    ExpConfig,
    MessageInterceptConfig,
    MetricExtractorConfig,
    MetricType,
    WorkflowStepConfig,
    WorkflowType,
)
from .utils import load_config_from_file

__all__ = [
    "EnvConfig",
    "AgentConfig",
    "WorkflowStepConfig",
    "ExpConfig",
    "MetricExtractorConfig",
    "EnvironmentConfig",
    "MessageInterceptConfig",
    "Config",
    "load_config_from_file",
    "AgentClassType",
    "MetricType",
    "WorkflowType",
]


class AgentsConfig(BaseModel):
    """Configuration for different types of agents in the simulation."""

    citizens: list[AgentConfig] = Field(..., min_length=1)
    """Citizen Agent configuration"""

    firms: list[AgentConfig] = Field(
        [
            AgentConfig(
                agent_class=AgentClassType.FIRM,
                number=1,
            ),
        ],
        min_length=1,
    )
    """Firm Agent configuration"""

    banks: list[AgentConfig] = Field(
        [
            AgentConfig(
                agent_class=AgentClassType.BANK,
                number=1,
            ),
        ],
        min_length=1,
    )
    """Bank Agent configuration"""

    nbs: list[AgentConfig] = Field(
        [
            AgentConfig(
                agent_class=AgentClassType.NBS,
                number=1,
            ),
        ],
        min_length=1,
    )
    """NBS Agent configuration"""

    governments: list[AgentConfig] = Field(
        [
            AgentConfig(
                agent_class=AgentClassType.GOVERNMENT,
                number=1,
            ),
        ],
        min_length=1,
    )
    """Government Agent configuration"""

    init_funcs: list[Callable[[Any], Union[None, Awaitable[None]]]] = Field([])
    """Initialization functions for simulation, the only one argument is the AgentSociety object"""

    @field_serializer("init_funcs")
    def serialize_init_funcs(self, init_funcs, info):
        return [func.__name__ for func in init_funcs]


class AdvancedConfig(BaseModel):
    """Advanced configuration for the simulation."""

    simulator: SimulatorConfig = Field(
        default_factory=lambda: SimulatorConfig.model_validate({})
    )
    """Simulator configuration"""

    embedding_model: Optional[str] = Field(None)
    """Embedding model name (e.g. BAAI/bge-m3) in Hugging Face, set it None if you want to use the simplest embedding model (TF-IDF)"""

    group_size: Union[int, Literal["auto"]] = Field("auto")
    """Group size for simulation"""

    logging_level: str = Field("INFO")
    """Logging level"""


class Config(BaseModel):
    """Configuration for the simulation."""

    llm: List[LLMConfig] = Field(..., min_length=1)
    """List of LLM configurations"""

    env: EnvConfig
    """Environment configuration"""

    map: MapConfig
    """Map configuration"""

    agents: AgentsConfig
    """Configuration for different types of agents in the simulation."""

    exp: ExpConfig
    """Experiment configuration"""

    advanced: AdvancedConfig = Field(
        default_factory=lambda: AdvancedConfig.model_validate({})
    )
    """Advanced configuration for the simulation (keep it empty if you don't need it)"""

    def set_auto_workers(self):
        """
        Set the group size and postgresql's num_workers by the number of CPUs and available memory

        The group size is determined by:
        1. Memory: Each group uses 2GB, reserve 5GB for simulator, 1GB for system
        2. CPU: Number of groups should not exceed CPU count
        3. Minimum group size is 100 agents
        """
        if self.advanced.group_size != "auto":
            return

        num_agents = 0
        for agents in [
            self.agents.citizens,
            self.agents.firms,
            self.agents.banks,
            self.agents.nbs,
            self.agents.governments,
        ]:
            num_agents += sum(agent.number for agent in agents)

        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().available / (1024 * 1024 * 1024)
        available_memory_gb = memory_gb - 8  # for simulator
        available_memory_gb -= 1  # for message interceptor
        available_memory_gb -= 1  # for pgsql
        mem_per_group = 2
        if available_memory_gb < mem_per_group:
            raise ValueError(
                f"Not enough memory ({memory_gb:.2f}GB) to run the simulation, at least 12GB available memory is required"
            )
        max_groups_by_memory = int(available_memory_gb / mem_per_group)
        max_groups = min(cpu_count, max_groups_by_memory)
        self.advanced.group_size = max(100, math.ceil(num_agents / max_groups))
        num_groups = math.ceil(num_agents / self.advanced.group_size)
        if self.env.pgsql.enabled:
            if self.env.pgsql.num_workers == "auto":
                # between 1 and 4
                self.env.pgsql.num_workers = max(1, min(4, math.ceil(num_groups / 4)))
