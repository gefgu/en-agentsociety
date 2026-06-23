# AgentManager - Agent Lifecycle Management

## Overview

The `AgentManager` class provides comprehensive agent management for the agent society simulation system. It handles all aspects of agent lifecycle management, from creation and initialization through execution and cleanup.

**Location**: `agentsociety/simulation/agentmanager.py`

## What AgentManager Does

### 1. **Agent Creation** 🏗️
- Prepares agent initialization tuples from configuration
- Validates agent counts on simulation resume
- Handles both normal and file-based agent memory loading
- Generates unique agent IDs

### 2. **Agent Initialization** 🚀
- Creates agent instances with proper toolbox setup
- Initializes memory with configuration
- Creates and links agent blocks/components
- Runs agent initialization hooks
- Exports and saves agent profiles
- Initializes embeddings for semantic understanding

### 3. **Agent Execution** ⚡
- Executes all agents in parallel for each simulation step
- Collects performance metrics
- Manages agent state transitions

### 4. **Memory & State Management** 💾
- Updates agent memory across multiple agents efficiently
- Gathers information from agents with flexible filtering
- Saves static agent information to database
- Supports batch operations for performance

### 5. **Agent Filtering & Querying** 🔍
- Filter agents by type (Citizen, Firm, Bank, etc.)
- Filter agents by profile properties (age, education, etc.)
- Combined type and property filtering
- Quick lookup of specific agents

### 6. **Agent Lifecycle** 🔄
- Manages agent initialization
- Handles reset operations for new rounds
- Coordinates safe agent deletion
- Proper cleanup and resource release

## Quick Start

### Installation

The AgentManager is already integrated into the simulation module:

```python
from en_agentsociety.simulation import AgentManager
```

### Basic Usage

```python
# 1. Create manager
manager = AgentManager(
    config=config,
    llm=llm,
    environment=environment,
    messager=messager,
    embedding=embedding,
    database_writer=database_writer,
    db_actor=db_actor,
    exp_id="experiment_001"
)

# 2. Setup
toolbox = await manager.create_toolbox()

# 3. Initialize agents
agents = await manager.prepare_agents(config.agents)
await manager.initialize_agents(agents)

# 4. Main simulation loop
for step in range(num_steps):
    await manager.run_all_agents()
    
    # Get information
    data = await manager.gather_from_agents("status")
    
    # Update if needed
    await manager.update_agent_memory([1, 2, 3], "status", "new_value")

# 5. Cleanup
await manager.close_all_agents()
```

## Core Concepts

### Agent Storage
Agents are stored in two internal structures:

1. **`_id2agent`**: Dictionary mapping agent IDs to agent instances
   - Fast O(1) lookup of agents
   - Direct access to agent objects

2. **`_filter_base`**: Dictionary storing metadata for filtering
   - Agent class type (for type filtering)
   - Memory configuration (for property filtering)

### Agent Lifecycle

```
Configured → Initialized → Ready → Running (repeated) → Cleanup
```

### Filtering

Agents can be efficiently filtered using:

```python
# By type
citizens = await manager.filter_agents(types=(CitizenAgentBase,))

# By property
young_people = await manager.filter_agents(
    filter_str="${profile.age} < 30"
)

# Combined
result = await manager.filter_agents(
    types=(CitizenAgentBase,),
    filter_str="${profile.education} == 'university'"
)
```

## API Reference

### Initialization

```python
async def create_toolbox() -> AgentToolbox
```
Creates the shared AgentToolbox used by all agents.

```python
async def initialize_agents(agents: list[tuple], resume_state: Optional[dict] = None) -> None
```
Instantiates agents and runs initialization hooks.

### Execution

```python
async def run_all_agents() -> list[Any]
```
Executes one step for all agents in parallel.

### Memory Operations

```python
async def update_agent_memory(
    agent_ids: list[int],
    key: str,
    content: Any
) -> None
```
Updates memory for specified agents.

```python
async def gather_from_agents(
    content: str,
    agent_ids: Optional[list[int]] = None,
    flatten: bool = False,
    keep_id: bool = False
) -> Union[dict[int, Any], list[Any]]
```
Gathers information from agents.

### Querying

```python
async def filter_agents(
    types: Optional[tuple[type[Agent], ...]] = None,
    filter_str: Optional[str] = None
) -> list[int]
```
Filters agents by type or property.

```python
def get_agent(self, agent_id: int) -> Optional[Agent]
```
Gets a specific agent.

### Lifecycle

```python
async def delete_agents(agent_ids: list[int]) -> None
```
Deletes specified agents.

```python
async def reset_all_agents() -> None
```
Resets all agents for next round.

```python
async def close_all_agents() -> None
```
Closes and cleans up all agents.

### Properties

```python
@property
def agents() -> dict[int, Agent]:
    """Get all agents"""

@property
def agent_ids() -> list[int]:
    """Get all agent IDs"""
```

## Documentation Files

The AgentManager comes with comprehensive documentation:

1. **AGENTMANAGER_QUICK_REFERENCE.md** - Common operations and examples
2. **AGENTMANAGER_INTEGRATION_GUIDE.md** - How to integrate with SimulationEngine
3. **AGENTMANAGER_DESIGN.md** - Architecture and design patterns

## Examples

### Filter Citizens by Age

```python
young_citizens = await manager.filter_agents(
    types=(CitizenAgentBase,),
    filter_str="${profile.age} < 30"
)

# Get their names
names = await manager.gather_from_agents(
    "name",
    agent_ids=young_citizens,
    flatten=True
)
```

### Update Multiple Agents

```python
# Get all firm agents
firms = await manager.filter_agents(types=(FirmAgentBase,))

# Update their status
await manager.update_agent_memory(
    firms,
    "status",
    "market_open"
)
```

### Process Agent Statistics

```python
# Get all agents
all_ids = manager.agent_ids

# Filter by type
citizen_ids = await manager.filter_agents(types=(CitizenAgentBase,))

# Gather statistics
ages = await manager.gather_from_agents("age", citizen_ids)
avg_age = sum(ages.values()) / len(ages)
```

## Performance Considerations

### Parallel Execution ⚡
- All agents run in parallel each step
- Batch operations use `asyncio.gather()` for concurrency

### Efficient Filtering 🔍
- Type filtering: O(n) where n = number of agents
- Property filtering: O(m) where m = filtered agents
- Combined filtering: O(n) + O(m)

### Memory Management 💾
- Single dictionary storage for O(1) lookups
- No duplicate agent data
- Batch memory updates supported

## Integration with SimulationEngine

To use AgentManager in SimulationEngine:

```python
class SimulationEngine:
    def __init__(self, config: Config, ...):
        self._agent_manager = AgentManager(
            config=config,
            llm=self._llm,
            environment=self._environment,
            messager=self._messager,
            embedding=self._embedding,
            database_writer=self._database_writer,
            db_actor=self._db_actor,
            exp_id=self.exp_id
        )
    
    async def init(self):
        # Create toolbox
        await self._agent_manager.create_toolbox()
        
        # Initialize agents
        agents = await self._agent_manager.prepare_agents(
            self._config.agents,
            self._resume_state
        )
        await self._agent_manager.initialize_agents(agents, self._resume_state)
    
    async def step(self):
        # Run agents
        await self._agent_manager.run_all_agents()
        
        # Access agents as needed
        citizen_ids = await self._agent_manager.filter_agents(
            types=(CitizenAgentBase,)
        )
```

See **AGENTMANAGER_INTEGRATION_GUIDE.md** for detailed integration steps.

## Benefits

✅ **Separation of Concerns** - Agent management is isolated and focused
✅ **Maintainability** - Easier to test, debug, and extend
✅ **Reusability** - Can be used in other simulation contexts
✅ **Performance** - Parallel execution and batch operations
✅ **Clarity** - Clear API and method names
✅ **Scalability** - Easy to add features without bloating parent class
✅ **Flexibility** - Can filter and query agents efficiently

## Error Handling

AgentManager handles errors gracefully:

```python
try:
    await manager.initialize_agents(agents)
except ValueError as e:
    # Handle configuration or resume errors
    logger.error(f"Initialization failed: {e}")

try:
    await manager.delete_agents(agent_ids)
except Exception as e:
    # Warn but continue
    logger.warning(f"Failed to delete some agents: {e}")
```

## Future Enhancements

Potential future features:

- 📊 Agent statistics and monitoring
- 💾 Agent state serialization
- 🔄 Agent pooling for efficiency
- 📈 Performance profiling
- 🔗 Agent relationship tracking
- 🎯 Advanced filtering operators
- 🚀 Distributed agent execution

## Contributing

When extending AgentManager:

1. Keep the single responsibility principle
2. Maintain async-first design
3. Add comprehensive docstrings
4. Include type hints
5. Write unit tests
6. Update documentation

## Support

For issues or questions:

1. Check AGENTMANAGER_QUICK_REFERENCE.md for common operations
2. Read AGENTMANAGER_DESIGN.md for architecture details
3. See AGENTMANAGER_INTEGRATION_GUIDE.md for integration help

---

*AgentManager - Centralizing Agent Management* 🎯

