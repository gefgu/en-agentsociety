# `simulation/` — Simulation Runtime Engines

This package contains the core runtime that orchestrates agent execution.

---

## Files

| File | Purpose |
|---|---|
| `agentsociety.py` | `AgentSociety` factory class — creates the right engine from config |
| `simulationengine.py` | `SimulationEngine` — city-scale population simulation runtime |
| `individualengine.py` | `IndividualEngine` — task-solving pipeline runtime |
| `type.py` | `ExperimentStatus` enum, `Logs` model |

---

## `AgentSociety` (Factory)

```python
from agentsociety import AgentSociety

engine = AgentSociety.create(config)  # returns SimulationEngine or IndividualEngine
await engine.run()
```

`AgentSociety.create(config)` inspects the config type:
- `Config` → `SimulationEngine`
- `IndividualConfig` → `IndividualEngine`

The `AgentSociety(config)` constructor path still works but is **deprecated** and emits a warning.

---

## `SimulationEngine`

Full city-scale simulation runtime.

### Responsibilities

1. **Initialization**: Sets up Ray, LLM, environment simulators, message bus, database, embeddings.
2. **Agent creation**: Instantiates all agent types (citizens, firms, banks, governments, NBS, supervisor) as Ray remote actors grouped in `AgentGroup` batches.
3. **Memory initialization**: Runs `MemoryConfigGenerator` instances per agent, sets default `StatusAttributes`.
4. **Workflow execution**: Iterates through `ExpConfig.workflow` steps, calling the appropriate handler for each `WorkflowType`.
5. **CatBoost / ML need adjustment**: Optionally routes need adjustment to `CatBoostAdjustNeedsActor` instead of LLM.
6. **DayNight cycle**: Manages simulation time, day/night transitions, and environment state.
7. **Persistence**: Writes agent status snapshots, dialog logs, and interview/survey results to storage.
8. **Monitoring**: Optionally starts Prometheus + Grafana + ClickHouse Docker stack.

### Key Methods

```python
engine = SimulationEngine(config, tenant_id="")

await engine.run()                              # execute full workflow
await engine.step(ticks=300)                    # advance N ticks
await engine.interview(agent_ids, question)     # ask agents a question
await engine.survey(agent_ids, survey)          # send survey
await engine.update_environment(data)           # change global prompt
await engine.update_state(agent_ids, data)      # set agent memory fields
await engine.gather(query)                      # bulk read agent memory
```

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
