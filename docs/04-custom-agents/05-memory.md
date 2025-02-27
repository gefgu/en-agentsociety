# Memory System

```{admonition} Caution
:class: caution
This document is currently under active development. The complete version will be available soon. Stay tuned!
```

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

from agentsociety import Agent, AgentType
from agentsociety.cityagent import memory_config_societyagent
from agentsociety.memory import Memory


class CustomAgent(Agent):
    def __init__(self, name: str,memory:Memory, **kwargs):
        super().__init__(name=name, memory=memory,type=AgentType.Citizen, **kwargs)

    async def forward(
        self,
    ):
        stream = self.memory.stream
        # add stream, type: cognition
        await stream.add_cognition(description="I am a waiter at this restaurant.")
        await stream.add_cognition(description="My working place names as 'A Restaurant'.")
        # relevant search
        await stream.search(query="restaurant")
        # relevant search (within the same day, the time of the Urban Space)
        await stream.search_today(query="restaurant")


async def main():
    extra_attributes, profile, base = memory_config_societyagent()
    agent = CustomAgent(name="name", memory=Memory(extra_attributes, profile, base))
    await agent.forward()


if __name__ == "__main__":
    asyncio.run(main())
```

### 2. StatusMemory

`StatusMemory` is designed to unify three different types of memory (status, configuration, dynamic) into a single objective memory.  

The design central is the fusion of semantic richness and adaptability. By integrating embedding models and Faiss-based vector search, StatusMemory transcends static storage, transforming raw data into semantically meaningful representations. 

Fields are dynamically contextualized through user-defined templates, allowing textual descriptions to capture deeper relationships between data points. 

### Usage Example

Use status memory in your agent. If you are using `AgentSimulation.run_from_config`, assign your status memory field define function with `ExpConfig.SetAgentConfig(memory_config_func=<STATUS-CONFIG-DICT>)`.

```python
import asyncio

from agentsociety import Agent, AgentType
from agentsociety.cityagent import memory_config_societyagent
from agentsociety.memory import Memory


class CustomAgent(Agent):
    def __init__(self, name: str, memory: Memory, **kwargs):
        super().__init__(name=name, memory=memory, type=AgentType.Citizen, **kwargs)

    async def forward(
        self,
    ):
        status = self.memory.status
        # update value, note that you can not add a new field to status once the memory is instantiated
        await status.update("city", "Beijing")
        # retrieve value
        print(await status.get("city", default_value="New York"))


async def main():
    _, profile, base = memory_config_societyagent()
    # self-define status field
    # key: field name
    # value: tuple(field name, default value, Optional[whether use embedding for this filed])
    extra_attributes = {
        "type": (str, "citizen"),
        "city": (str, "New York", True),
    }
    agent = CustomAgent(name="name", memory=Memory(extra_attributes, profile, base))
    await agent.forward()


if __name__ == "__main__":
    asyncio.run(main())

```

## memory.embedding_model: Embedding Model

To change the embedding model within the `Memory`, you simply need to assign it with `ExpConfig.SetAgentConfig`.

### Usage Example

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)
from agentsociety.llm import SimpleEmbedding

exp_config = ExpConfig(exp_name="test",).SetAgentConfig(
    embedding_model=SimpleEmbedding()
)
```
The incoming `embedding` is an instance of a subclass from `langchain_core.embeddings.Embeddings` and needs to implement `embed_query`, `embed_documents`.
