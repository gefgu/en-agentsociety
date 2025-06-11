# Memory System

The memory system in our framework consists of two main components: `StreamMemory` and `StatusMemory`. This dual-memory architecture enables agents to maintain both episodic memories (events and experiences) and semantic memories (status and attributes).

## Core Components

### 1. StreamMemory
StreamMemory manages temporal, event-based memories organized chronologically, similar to human episodic memory. It features:

- **Memory Node Structure**:
  ```python
  class MemoryNode:
      tag: MemoryTag        # Category of memory (MOBILITY/SOCIAL/ECONOMY/etc)
      day: int             # Day of event
      t: int              # Timestamp
      location: str       # Location where event occurred  
      description: str    # Event description
      cognition_id: int   # Optional link to related cognitive memory
  ```

- **Memory Types**:
  - Cognitive memories (`add_cognition`)
  - Social interactions (`add_social`) 
  - Economic activities (`add_economy`)
  - Mobility events (`add_mobility`)
  - General events (`add_event`)

Let's see how to use StreamMemory:

```python
import asyncio
from typing import Any, Literal, Union, cast

import ray

from agentsociety.agent import CitizenAgentBase
from agentsociety.agent.agent_base import AgentToolbox
from agentsociety.agent.distribution import Distribution, DistributionConfig
from agentsociety.agent.memory_config_generator import MemoryT
from agentsociety.cityagent import (
    DEFAULT_DISTRIBUTIONS,
    default,
    memory_config_societyagent,
)
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.configs.agent import AgentClassType, AgentConfig
from agentsociety.configs.exp import WorkflowStepConfig, WorkflowType
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.memory import Memory
from agentsociety.simulation import AgentSociety
from agentsociety.storage import DatabaseConfig


class StreamTestAgent(CitizenAgentBase):

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
        )

    async def forward(self):
        tick = self.environment.get_tick()
        stream = self.memory.stream
        # add stream, type: cognition
        await stream.add_cognition(
            description=f"I am a waiter at this restaurant, the time is {tick}."
        )
        await stream.add_cognition(
            description="My working place names as 'A Restaurant'."
        )
        # relevant search
        await stream.search(query="restaurant")
        # relevant search (within the same day, the time of the Urban Space)
        await stream.search_today(query="restaurant")

    async def reset(self):
        # Do nothing
        pass


config = Config(
    llm=[
        LLMConfig(
            provider=LLMProviderType.Qwen,
            base_url=None,
            api_key="<YOUR-API-KEY>",
            model="<YOUR-MODEL>",
            semaphore=200,
        )
    ],
    env=EnvConfig(
        db=DatabaseConfig(
            enabled=True,
            db_type="postgresql",
            pg_dsn="<PGSQL-DSN>",
        ),
    ),
    map=MapConfig(
        file_path="<MAP-FILE-PATH>",
    ),
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class=StreamTestAgent,
                number=1,
                memory_config_func=memory_config_societyagent,
                memory_distributions=cast(
                    dict[str, Union[Distribution, DistributionConfig]],
                    DEFAULT_DISTRIBUTIONS,
                ),
            ),
        ]
    ),  # type: ignore
    exp=ExpConfig(
        name="stream_test",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.STEP,
                steps=5,
            ),
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
    ),
)
config = default(config)

async def main():
    agentsociety = AgentSociety(config)
    await agentsociety.init()
    await agentsociety.run()
    await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

```

### 2. StatusMemory

`StatusMemory` is designed to unify three different types of memory (status, configuration, dynamic) into a single objective memory.  

The design central is the fusion of semantic richness and adaptability. By integrating embedding models and Faiss-based vector search, StatusMemory transcends static storage, transforming raw data into semantically meaningful representations. 

Fields are dynamically contextualized through user-defined templates, allowing textual descriptions to capture deeper relationships between data points. 

### Usage Example

Below is an example of using `StatusMemory` in an agent.

```python
import asyncio
from typing import Any, Literal, Union, cast

import ray

from agentsociety.agent import CitizenAgentBase
from agentsociety.agent.agent_base import AgentToolbox
from agentsociety.agent.distribution import Distribution, DistributionConfig
from agentsociety.agent.memory_config_generator import MemoryT
from agentsociety.cityagent import (
    DEFAULT_DISTRIBUTIONS,
    default,
    memory_config_societyagent,
)
from agentsociety.cityagent.metrics import mobility_metric
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.configs.agent import AgentClassType, AgentConfig
from agentsociety.configs.exp import WorkflowStepConfig, WorkflowType
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.memory import Memory
from agentsociety.simulation import AgentSociety
from agentsociety.storage import DatabaseConfig


def withCityMemoryConfig(
    distributions: dict[str, Distribution],
) -> tuple[dict[str, MemoryT], dict[str, MemoryT], dict[str, Any]]:
    # self-define status field
    # key: field name
    # value: tuple(field name, default value, Optional[whether use embedding for this filed])
    EXTRA_ATTRIBUTES, PROFILE, BASE = memory_config_societyagent(
        distributions=distributions
    )
    EXTRA_ATTRIBUTES.update(
        {
            "city&time": (str, "None&0", False),
        }
    )
    return EXTRA_ATTRIBUTES, PROFILE, BASE


class StatusTestAgent(CitizenAgentBase):

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
        )

    async def forward(self):
        tick = self.environment.get_tick()
        status = self.memory.status
        # update value, note that you can not add a new field to status once the memory is instantiated
        await status.update("city&time", f"Beijing&{tick}")
        # retrieve value
        print(await status.get("city&time", default_value="None"))

    async def reset(self):
        # Do nothing
        pass


config = Config(
    llm=[
        LLMConfig(
            provider=LLMProviderType.Qwen,
            base_url=None,
            api_key="<YOUR-API-KEY>",
            model="<YOUR-MODEL>",
            semaphore=200,
        )
    ],
    env=EnvConfig(
        db=DatabaseConfig(
            enabled=True,
            db_type="postgresql",
            pg_dsn="<PGSQL-DSN>",
        ),
    ),
    map=MapConfig(
        file_path="<MAP-FILE-PATH>",
    ),
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class=StatusTestAgent,
                number=1,
                memory_config_func=withCityMemoryConfig,
                memory_distributions=cast(
                    dict[str, Union[Distribution, DistributionConfig]],
                    DEFAULT_DISTRIBUTIONS,
                ),
            ),
        ]
    ),  # type: ignore
    exp=ExpConfig(
        name="status_test",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.STEP,
                steps=5,
            ),
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
    ),
)
config = default(config)


async def main():
    agentsociety = AgentSociety(config)
    await agentsociety.init()
    await agentsociety.run()
    await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

## memory.embedding_model: Embedding Model

To change the embedding model within the `Memory`, you simply need to assign it in the AdvancedConfig.

```python
config = Config(
    ...
    advanced=AdvancedConfig(embedding_model=<EMBEDDING-MODEL-NAME>),
)
```

The incoming `embedding` is the name of the embedding model, supports downloading from huggingface.

```{admonition} Attention
:class: attention
It requires very large computational resources to use the embedding model and will slow down the simulation speed.
```
