# AgentManager Design Documentation

## Design Principles

### 1. **Single Responsibility**
AgentManager is solely responsible for agent management. It does not:
- Manage the simulation workflow
- Handle environment updates
- Process messages
- Manage experiment state
- Handle database writes (delegates to components)

### 2. **Dependency Injection**
All dependencies are injected at initialization:
```python
manager = AgentManager(
    config=config,           # Configuration
    llm=llm,                 # Language model
    environment=environment, # Simulation environment
    messager=messager,       # Message system
    embedding=embedding,     # Embedding model
    database_writer=writer,  # Database persistence
    db_actor=actor,          # ClickHouse actor
    exp_id=exp_id           # Experiment ID
)
```

This design allows:
- Easy testing with mock dependencies
- Flexibility in implementations
- Clear separation of concerns
- Easy to reason about requirements

### 3. **Async-First Design**
All I/O operations are async to maximize concurrency:
- Agent initialization happens in parallel
- Agent execution happens in parallel
- Agent memory operations batch effectively
- Integration with async SimulationEngine

### 4. **Type Safety**
Uses Python type hints throughout:
```python
def get_agent(self, agent_id: int) -> Optional[Agent]
async def filter_agents(
    self,
    types: Optional[tuple[type[Agent], ...]] = None,
    filter_str: Optional[str] = None,
) -> list[int]
```

## Architecture

### Data Models

#### Agent Storage
```
_id2agent: dict[int, Agent]
├── Key: Agent ID (unique integer)
└── Value: Agent instance (fully initialized)

_filter_base: dict[int, tuple[type[Agent], dict[str, Any]]]
├── Key: Agent ID
└── Value: 
    ├── Agent class (for type filtering)
    └── Memory config (for property filtering)
```

#### Agent Lifecycle States
```
1. Configuration Phase
   ├── AgentConfig objects define agent parameters
   └── Memory configurations prepared

2. Initialization Phase
   ├── Agent instances created
   ├── Memory objects initialized
   ├── Blocks (if any) instantiated
   └── Agent.init() hooks executed

3. Ready Phase
   ├── Agents ready for execution
   ├── Embeddings initialized
   └── Profiles exported

4. Execution Phase (Repeated)
   ├── Agent.run() called each step
   ├── Memory updated as needed
   └── Data gathered for analysis

5. Cleanup Phase
   ├── Agent.close() called
   └── Resources released
```

### Key Methods by Category

#### Initialization
```
create_toolbox()           # Setup shared toolbox
prepare_agents()           # Create initialization tuples
initialize_agents()        # Instantiate and init agents
```

#### Execution
```
run_all_agents()           # Execute one step
reset_all_agents()         # Reset for new round
```

#### Lifecycle
```
close_all_agents()         # Cleanup
delete_agents()            # Remove agents
```

#### Memory Operations
```
update_agent_memory()      # Update agent state
gather_from_agents()       # Query agent state
save_agent_static_info()   # Persist static data
```

#### Queries
```
filter_agents()            # Filter by type or profile
get_agent()                # Lookup specific agent
agent_ids (property)       # Get all IDs
agents (property)          # Get all agents
```

## Design Patterns

### 1. **Facade Pattern**
AgentManager provides a simplified interface to complex agent operations:

```python
# Without AgentManager (Complex)
for agent_id in target_agent_ids:
    if agent_id in self._id2agent:
        agent = self._id2agent[agent_id]
        await agent.status.update(key, new_value)

# With AgentManager (Simple)
await manager.update_agent_memory(target_agent_ids, key, new_value)
```

### 2. **Manager Pattern**
Central management of a collection of related objects:

```python
class AgentManager:
    def __init__(self, ...):
        self._id2agent: dict[int, Agent] = {}
        # Manages the collection
    
    def get_agent(self, agent_id: int) -> Optional[Agent]:
        return self._id2agent.get(agent_id)
```

### 3. **Repository Pattern**
AgentManager acts as a repository for agents:

```python
# Query operations
await manager.filter_agents(types=(CitizenAgent,))
await manager.filter_agents(filter_str="${profile.age} > 18")

# Access operations
agent = manager.get_agent(agent_id)
all_agents = manager.agents
```

### 4. **Batch Operations Pattern**
Operations are batched for efficiency:

```python
# Batch memory update
await manager.update_agent_memory(
    [1, 2, 3, 4, 5],  # Multiple agents
    "status",
    "event"
)

# Batch execution
await manager.run_all_agents()  # All agents in parallel
```

### 5. **Lazy Initialization**
Some operations are deferred until needed:

```python
# Toolbox created only when first initialized
if self._agent_toolbox is None:
    raise RuntimeError("Create toolbox first")

# Embeddings initialized during agent setup
await agent.memory.initialize_embeddings()
```

## Performance Considerations

### Parallel Execution
```python
# Agents run in parallel
tasks = [agent.run() for agent in self._id2agent.values()]
await asyncio.gather(*tasks)

# Memory updates batched
tasks = [agent.status.update(...) for agent in selected_agents]
await asyncio.gather(*tasks)
```

### Efficient Filtering

**Type Filtering** - O(n) where n = number of agents
```python
filtered = [
    agent_id
    for agent_id, (agent_class, _) in self._filter_base.items()
    if any(issubclass(agent_class, t) for t in types)
]
```

**Profile Filtering** - O(n) where n = filtered agents
```python
filtered = [
    agent_id
    for agent_id in filtered_ids
    if evaluate_filter(filter_str, self._filter_base[agent_id][1])
]
```

### Memory Management
- Agents stored in single dictionary for O(1) lookup
- Filter base maintains metadata for quick filtering
- No duplicate storage of agent data

## Error Handling Strategy

### Initialization Errors
```python
try:
    await manager.initialize_agents(agents)
except ValueError as e:
    # Handle missing resume data
    # Handle invalid configurations
```

### Runtime Errors
```python
try:
    await manager.run_all_agents()
except Exception as e:
    # Agent-specific errors are logged
    # Simulation can continue or be paused
```

### Cleanup Errors
```python
try:
    await manager.close_all_agents()
except Exception as e:
    # Warn but continue cleanup
    logger.warning(f"Error closing agent: {e}")
```

## Extension Points

### 1. Custom Agent Filtering
```python
# Add custom filter methods
async def filter_by_custom_criteria(self, criteria):
    return await self.filter_agents(
        filter_str=f"${{profile.{criteria}}} ..."
    )
```

### 2. Agent Statistics
```python
# Add statistics collection
def get_agent_statistics(self):
    return {
        "total": len(self._id2agent),
        "by_type": self._count_by_type(),
        ...
    }
```

### 3. Advanced Memory Operations
```python
# Add memory querying
async def query_agent_memory(self, agent_id, query):
    agent = self.get_agent(agent_id)
    return await agent.memory.query(query)
```

## Testing Strategy

### Unit Tests
```python
# Test with mock dependencies
mock_llm = Mock()
mock_env = Mock()

manager = AgentManager(
    config=test_config,
    llm=mock_llm,
    environment=mock_env,
    ...
)

# Test specific methods
await manager.filter_agents(types=(CitizenAgent,))
```

### Integration Tests
```python
# Test with real components
manager = AgentManager(
    config=config,
    llm=real_llm,
    environment=real_env,
    ...
)

# Test full workflow
await manager.initialize_agents(agents)
await manager.run_all_agents()
```

### End-to-End Tests
```python
# Test with SimulationEngine
engine = SimulationEngine(config)
await engine.init()
await engine.step()
```

## Future Enhancements

1. **Agent Pooling**: Reuse agent instances for efficiency
2. **Agent Caching**: Cache frequently accessed agent data
3. **Agent Monitoring**: Built-in performance metrics
4. **Agent Clustering**: Group agents for distributed execution
5. **Agent Serialization**: Save/load agent state
6. **Agent Versioning**: Track agent configuration versions
7. **Agent Lineage**: Track agent creation and relationships
8. **Dynamic Agent Creation**: Create agents during simulation

## Migration Guide for Existing Code

### Before (Direct Access)
```python
# Breaking up SimulationEngine responsibility
for agent_id in agent_ids:
    agent = self._id2agent.get(agent_id)
    if agent:
        await agent.status.update(key, value)
```

### After (Using AgentManager)
```python
# Clean separation
await self._agent_manager.update_agent_memory(agent_ids, key, value)
```

### Benefits
- Cleaner code
- Better encapsulation
- Easier testing
- Better maintainability
- Clearer intent

