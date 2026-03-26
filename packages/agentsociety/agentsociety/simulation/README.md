# `simulation/` — Simulation Runtime Engines

This package contains the core runtime that orchestrates agent execution.

---

## Files

| File | Purpose |
|---|---|
| `agentsociety.py` | `AgentSociety` factory class — creates the right engine from config |
| `simulationengine.py` | `SimulationEngine` — city-scale population simulation runtime |
| `agentmanager.py` | `AgentManager` — centralized agent management (creation, initialization, execution, memory) |
| `individualengine.py` | `IndividualEngine` — task-solving pipeline runtime |
| `type.py` | `ExperimentStatus` enum, `Logs` model |

---

## `AgentManager`

Centralized agent lifecycle management for `SimulationEngine`.

### Responsibilities

1. **Agent Creation**: Prepares and validates agent initialization tuples from configurations
2. **Agent Initialization**: Instantiates agents, runs init hooks, exports profiles, initializes embeddings
3. **Agent Execution**: Runs all agents in parallel for simulation steps
4. **Memory Management**: Updates agent memory, retrieves agent state, saves static information  
5. **Agent Filtering**: Filters agents by type or custom properties
6. **Agent Lifecycle**: Resets, deletes, and closes agents

### Usage

```python
# Initialize manager (done internally by SimulationEngine)
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

# Create toolbox
await manager.create_toolbox()

# Initialize agents
agents = await manager.prepare_agents(config.agents)
await manager.initialize_agents(agents)

# Execute step
await manager.run_all_agents()

# Query agents  
citizen_ids = await manager.filter_agents(types=(CitizenAgentBase,))
data = await manager.gather_from_agents("status", agent_ids=citizen_ids)

# Update agents
await manager.update_agent_memory(citizen_ids, "status", "active")

# Cleanup
await manager.close_all_agents()
```

---

## `SimulationEngine`

Full city-scale simulation runtime.

### Responsibilities

1. **Initialization**: Sets up Ray, LLM, environment simulators, message bus, database, embeddings.
2. **Agent Management**: Delegates to `AgentManager` for all agent-related operations.
3. **Workflow execution**: Iterates through `ExpConfig.workflow` steps, calling the appropriate handler for each `WorkflowType`.
4. **Decision routing**: Optionally routes need adjustment to `CatBoostAdjustNeedsActor` instead of LLM.
5. **DayNight cycle**: Manages simulation time, day/night transitions, and environment state.
6. **Persistence**: Writes agent status snapshots, dialog logs, and interview/survey results to storage.
7. **Monitoring**: Optionally starts Prometheus + Grafana + ClickHouse Docker stack.

### Key Methods

```python
engine = SimulationEngine(config, tenant_id="")

await engine.run()                              # execute full workflow
await engine.step(ticks=300)                    # advance N ticks
await engine.send_interview_message(question, agent_ids)    # ask agents
await engine.send_survey(survey, agent_ids)     # send survey
await engine.update_environment(key, value)     # change global state
await engine.update(agent_ids, key, content)    # set agent memory fields
await engine.gather(query, agent_ids)           # bulk read agent memory
await engine.filter(types=..., filter_str=...)  # filter agents
```

---

## Integration Pattern

SimulationEngine now uses AgentManager for all agent operations:

```python
class SimulationEngine:
    def __init__(self, config):
        self._agent_manager = None
    
    async def init(self):
        # Create manager
        self._agent_manager = AgentManager(...)
        await self._agent_manager.create_toolbox()
        
        # Prepare and initialize agents
        agents = await self._prepare_agents()
        await self._agent_manager.initialize_agents(agents)
    
    async def step(self):
        # Run agents via manager
        await self._agent_manager.run_all_agents()
        
        # Update via manager
        await self._agent_manager.update_agent_memory(ids, key, value)
        
        # Query via manager
        data = await self._agent_manager.gather_from_agents(content)
    
    async def close(self):
        # Cleanup via manager
        await self._agent_manager.close_all_agents()
```

Benefits:
- **Cleaner code**: Separation of concerns  
- **Maintainability**: Agent logic isolated
- **Testability**: AgentManager can be tested independently
- **Reusability**: Can be used in other contexts

---

## `IndividualEngine`

Lightweight task-solving runtime.

### Responsibilities

1. **Task loading**: Uses `TaskLoader` to load task batches from JSON/JSONL files.
2. **Agent initialization**: Creates `IndividualAgentBase`-typed agents with shared LLM and memory.
3. **Task assignment**: Round-robin assignment of tasks to agents.
4. **Result collection**: Gathers task results after all tasks complete.
5. **No city environment**: Does not start mobility or economic simulators.

### Lifecycle

```python
engine = IndividualEngine(config, tenant_id="")
await engine.run()       # loads tasks, assigns to agents, waits for completion
results = engine.get_results()
```

---

## Experiment Status

```python
class ExperimentStatus(Enum):
    NOT_STARTED = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3
    PAUSED = 4
```

Status is persisted to the database and exposed via the web API.

---

## Ray Distribution

`SimulationEngine` distributes agents across Ray workers using **AgentGroup** batches. Each group handles a slice of the total agent population:

```
SimulationEngine
  └── AgentGroup[0..N] (Ray actors)
        └── Agent[0..batch_size] (per-group workers)
```

This enables transparent scale-out to multi-node Ray clusters.
