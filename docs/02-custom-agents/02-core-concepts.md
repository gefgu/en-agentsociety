# Core Components of an Agent

An agent in our simulation environment is composed of several core components:

## Memory

There two types of `Memory` in our framework, `StreamMemory` and `StatusMemory`.

## `StreamMemory`

`StreamMemory` is used to manage and store time-ordered memory information in a stream-like structure.

### Main Components

- `collections.deque` for memory storage
- **Memory Tags** (`MemoryTag`):
   - Mobility: Movement-related memories
   - Social: Social interaction memories
   - Economy: Economic activities
   - Cognition: Cognitive processes
   - Event: Event-related memories
   - Other: Miscellaneous memories
 - **Memory Node** (`MemoryNode`):
   - tag: Memory category (MemoryTag)
   - day: Event day
   - t: Timestamp
   - location: Event location
   - description: Memory content
   - cognition_id: Optional reference to cognitive memory
   - id: Optional unique identifier

## `StatusMemory`

`StatusMemory` is designed to unify three different types of memory (status, configuration, dynamic) into a single objective memory.

### Main Components

- **Memory Types**:
   - `ProfileMemory`: Stores self-profile for the agent.
   - `StateMemory`: Stores status data of the agent.
   - `DynamicMemory`: Stores user-dynamically configured data.

## Embedding Model
Embedding Model is used in the memory to:
- Convert text descriptions into vector representations
- Enable semantic search across memory entries
- Support similarity-based memory retrieval

To change the embedding model within the `Memory`, you simply need to assign it with `ExpConfig.SetAgentConfig`.

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)
from agentsociety.llm import SimpleEmbedding

exp_config = ExpConfig(exp_name="test",).SetAgentConfig(
    embedding_model=SimpleEmbedding()
)
```
The incoming `embedding` is an instance of a subclass from `langchain_core.embeddings.Embeddings` and needs to implement `embed_query`, `embed_documents`.

## Retrieve Specific Memory

### Time-based Memory Retrieval
- `search_today`

### ID-based Retrieval
- `get_by_ids`

### Filter-based Memory Retrieval
- `search`
  - Semantic
  - Time Range
  - Memory Tag
  - Day Range
  - Top-K

## Urban Simulator
The Simulator serves as a bridge between agents and the physical entities in the simulation environment.
It manages bi-directional communication, allowing agents to perceive their surroundings and interact with the environment through actions.

## Interact Methods

### Environment Management
- `environment`
- `set_environment`
- `sence`
- `update_environment`

### Map Item Query
- `map`
- `get_poi_cate`
- `get_poi_categories`

### Logging History
- `get_log_list`
- `clear_log_list`

### Time-related Operations
- `get_time`
- `get_simulator_day`
- `get_simulator_second_from_start_of_day`

### Simulation Control
- `pause`
- `resume`

### Person Information Retrieval
- `get_person`

## Economy Simulator
The Economy Client serves as a centralized economic settlement system that manages monetary flows between company entities and citizen entities in the simulation environment.

It handles transactions, resource allocation, and financial interactions within the virtual economy.

## Interact Methods

### Value Operations
- `get`: Get value of specific key
- `update`: Update value of specific key
- `add_delta_value`: Incremental update number type value

### Currency Calculation
- `calculate_taxes_due`: Pay tax to the government
- `calculate_consumption`: Buy items from firms
- `calculate_real_gdp`: Calculate GDP
- `calculate_interest`: Calculate interest for bank accounts

### Entity Information Retrieval
- `get_agent`
- `get_org`

### Simulation Control
- `save`
- `load`

### Logging History
- `get_log_list`
- `clear_log_list`

## LLM Client

The LLM Client manages communications between agents and large language models, representing the agent's "soul".

## Core Functions

### Communication Interface
- `atext_request`: Asynchronous chat completion

### API Control
- `show_consumption`: Monitor token consumption
- `set_semaphore`

### Request Configuration
- `set_temperature`: Adjust response randomness
- `set_max_tokens`: Control response length
- `set_top_p`: Configure sampling parameters
- `set_presence_penalty`: Adjust repetition avoidance

### Logging History
- `get_log_list`
- `clear_log_list`
