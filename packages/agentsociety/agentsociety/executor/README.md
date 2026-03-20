# `executor/` — Multi-Process Execution Helpers

This package provides utilities for spawning and managing multi-process simulation runs.

---

## Files

| File | Purpose |
|---|---|
| `process.py` | Process spawning and lifecycle management helpers |

---

## Purpose

When running large simulations on a single machine, `executor/` helpers:

1. Spawn the external city simulator subprocesses (mobility engine, economy engine).
2. Monitor subprocess health and restart on crash.
3. Collect and forward subprocess logs to the AgentSociety logger.
4. Clean up child processes on `KeyboardInterrupt` or experiment completion.

---

## Usage

`SimulationEngine` and `IndividualEngine` use this internally via `EnvironmentStarter`.

```python
from agentsociety.executor.process import ProcessManager

manager = ProcessManager()
pid = manager.spawn(
    cmd=["./city_simulator", "--port", "8888"],
    name="mobility_sim",
)

# Wait and check health
if not manager.is_alive(pid):
    manager.restart(pid)

# Stop all
manager.stop_all()
```

---

## Notes

- The CLI (`cli/cli.py`) also uses this when starting a full simulation stack from the command line.
- The `commercial/executor/` package extends this with cloud/remote execution capabilities.
