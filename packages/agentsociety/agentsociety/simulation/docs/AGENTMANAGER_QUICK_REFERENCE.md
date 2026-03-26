# AgentManager Quick Reference

## Common Operations

### Initialization

```python
from agentsociety.simulation import AgentManager

# Create instance
manager = AgentManager(
    config=config,
    llm=llm,
    environment=environment,
    messager=messager,
    embedding=embedding,
    database_writer=database_writer,
    db_actor=db_actor,
    exp_id="exp_123"
)

# Setup
toolbox = await manager.create_toolbox()
agents = await manager.prepare_agents(agent_configs)
await manager.initialize_agents(agents)
```

### Running Agents

```python
# Execute one simulation step
time_logs = await manager.run_all_agents()

# Check results
for log in time_logs:
    print(f"Agent execution time: {log['duration']}ms")
```

### Memory Access & Updates

```python
# Update single agent memory
await manager.update_agent_memory([agent_id], "status", "active")

# Update multiple agents
await manager.update_agent_memory(
    [1, 2, 3, 4, 5], 
    "position", 
    {"x": 0, "y": 0}
)

# Gather information from all agents
statuses = await manager.gather_from_agents("status")
# Returns: {agent_id: status_value, ...}

# Gather from specific agents
custom_data = await manager.gather_from_agents(
    "custom_field",
    agent_ids=[1, 5, 10]
)

# Gather and flatten results
flat_list = await manager.gather_from_agents(
    "name",
    flatten=True,
    keep_id=False
)
# Returns: [name1, name2, name3, ...]
```

### Filtering Agents

```python
from agentsociety.agent import CitizenAgentBase, FirmAgentBase

# Filter by type
citizens = await manager.filter_agents(
    types=(CitizenAgentBase,)
)
# Returns: [1, 5, 10, ...]

# Filter by type (multiple)
economic_agents = await manager.filter_agents(
    types=(FirmAgentBase, BankAgentBase, NBSAgentBase)
)

# Filter by profile attribute
young_people = await manager.filter_agents(
    filter_str="${profile.age} < 30"
)

# Combined filtering
young_citizens = await manager.filter_agents(
    types=(CitizenAgentBase,),
    filter_str="${profile.age} < 30"
)

# Get all agents
all_ids = await manager.filter_agents()
```

### Agent Access

```python
# Get all agents
all_agents = manager.agents
# Type: dict[int, Agent]

# Get specific agent
agent = manager.get_agent(agent_id=42)

# Get all agent IDs
agent_ids = manager.agent_ids
# Type: list[int]

# Check if agent exists
if agent_id in manager.agents:
    print(f"Agent {agent_id} exists")
```

### Agent Lifecycle

```python
# Initialize agents
agents = await manager.prepare_agents(config.agents)
await manager.initialize_agents(agents)

# Reset for next round
await manager.reset_all_agents()

# Delete specific agents
await manager.delete_agents([old_agent_1, old_agent_2])

# Close all agents (cleanup)
await manager.close_all_agents()
```

### Advanced Operations

```python
# Save agent static information
saved_count = await manager.save_agent_static_info(step=100)
print(f"Saved {saved_count} agent records")

# Validate agent counts on resume
agent_configs = [config1, config2, config3]
try:
    manager._validate_resume_agent_count(
        agents_to_create,
        resume_state
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

### Practical Workflow Example

```python
# 1. Create and setup
manager = AgentManager(config, llm, env, msg, emb, db_writer, db_actor, exp_id)
await manager.create_toolbox()

# 2. Initialize agents
agents = await manager.prepare_agents(config.agents)
await manager.initialize_agents(agents)

# 3. Main simulation loop
for step in range(num_steps):
    # Run agents
    await manager.run_all_agents()
    
    # Check on specific citizens
    citizen_ids = await manager.filter_agents(types=(CitizenAgentBase,))
    
    # Get their positions
    positions = await manager.gather_from_agents(
        "position",
        agent_ids=citizen_ids
    )
    
    # Update if needed
    if some_condition:
        await manager.update_agent_memory(
            citizen_ids,
            "status",
            "event_triggered"
        )

# 4. Cleanup
await manager.close_all_agents()
```

### Error Handling

```python
try:
    await manager.initialize_agents(agents)
except ValueError as e:
    logger.error(f"Failed to initialize agents: {e}")
    # Handle specific errors
    
try:
    await manager.delete_agents(agent_ids)
except Exception as e:
    logger.warning(f"Failed to delete some agents: {e}")
    # Continue or retry
```

## Method Signatures

### Core Methods

```python
async def create_toolbox() -> AgentToolbox
async def prepare_agents(agent_configs, resume_state=None) -> list[tuple]
async def initialize_agents(agents, resume_state=None) -> None
async def run_all_agents() -> list[Any]
async def close_all_agents() -> None
```

### Memory Operations

```python
async def update_agent_memory(
    agent_ids: list[int],
    key: str,
    content: Any
) -> None

async def gather_from_agents(
    content: str,
    agent_ids: Optional[list[int]] = None,
    flatten: bool = False,
    keep_id: bool = False
) -> Union[dict[int, Any], list[Any]]

async def save_agent_static_info(step: int) -> int
```

### Agent Management

```python
async def delete_agents(agent_ids: list[int]) -> None
async def reset_all_agents() -> None
def get_agent(agent_id: int) -> Optional[Agent]
async def filter_agents(
    types: Optional[tuple[type[Agent]]] = None,
    filter_str: Optional[str] = None
) -> list[int]
```

### Properties

```python
@property
def agents() -> dict[int, Agent]

@property
def agent_ids() -> list[int]
```

## Tips & Best Practices

1. **Always create toolbox first**: Call `create_toolbox()` before initialization
2. **Use filter_agents for large datasets**: Instead of iterating, filter and batch operations
3. **Batch memory updates**: Update multiple agents at once for better performance
4. **Check agent existence**: Use `manager.get_agent()` before accessing
5. **Catch exceptions**: Agent operations can fail; handle exceptions gracefully
6. **Use flatten for simple cases**: When you just need a list of values
7. **Keep keep_id=True**: When results need to be mapped back to agents

