# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Installation
```bash
# From workspace root (uses uv workspace)
pip install -e packages/agentsociety

# Or with uv
uv sync
```

### CLI
```bash
agentsociety run --config <file.yaml>         # run simulation
agentsociety check --config <file.yaml>       # validate config
agentsociety ui --config <file.yaml>          # launch web UI
```

### Documentation
```bash
# From workspace root /mnt/raid5/gustavo/citysim/
make html-en   # English docs (Sphinx)
make html-zh   # Chinese docs
```

There is no test suite — the project uses example scripts in `/mnt/raid5/gustavo/citysim/examples/` for validation.

---

## Architecture

This is a **CitySim fork** of [tsinghua-fib-lab/agentsociety](https://github.com/tsinghua-fib-lab/agentsociety). Key divergences from upstream are catalogued in `agentsociety/CHANGES.md`. A comprehensive developer guide is in `agentsociety/AGENT_WORKFLOW.md`.

### Factory / Dual-Engine Pattern

`AgentSociety.create(config)` is the main entry point. It returns one of two engines based on config type:

| Config type | Engine returned | Use case |
|---|---|---|
| `Config` | `SimulationEngine` | City-scale multi-agent population simulation |
| `IndividualConfig` | `IndividualEngine` | Task-solving pipeline (no city env needed) |

Files: `simulation/agentsociety.py`, `simulation/simulationengine.py`, `simulation/individualengine.py`

### Agent Execution Model

Agents run as **Ray remote actors** in parallel. Each tick:
1. `AgentManager` dispatches `agent.forward()` across all Ray actors
2. Agent sets `context.current_intention`
3. `BlockDispatcher` selects the appropriate `Block` via LLM function-calling
4. The selected `Block.forward(context)` runs (reads/writes memory, calls LLM, accesses environment)

The `Block` is the fundamental composable unit — analogous to a PyTorch `Layer`. Blocks are registered on an `Agent` and routed to by the dispatcher.

Key files: `agent/agent.py`, `agent/block.py`, `agent/dispatcher.py`, `simulation/agentmanager.py`

### Memory System (3-store model)

Every agent has a `Memory` object with three stores:
- `memory.status` — `KVMemory`: mutable numeric/categorical state (hunger, energy, location, etc.)
- `memory.profile` — `KVMemory`: stable demographic info (age, occupation, income, personality)
- `memory.stream` — `StreamMemory`: ordered event log with semantic BM25 search

Semantic search uses `fastembed.SparseTextEmbedding` (BM25), not dense embeddings.

Key file: `memory/memory.py`

### LLM Layer

`LLM` wraps the OpenAI SDK with round-robin load balancing across multiple provider configs, token tracking, and exponential backoff. It is shared across agents via `AgentToolbox`.

Key file: `llm/llm.py`

### Prompt Management

Recent work (see git log) added a `PromptManager` system for versioned, maintainable prompts. Prompts are managed per-block rather than scattered as module-level strings. When modifying prompts in blocks like `cognition_block.py`, `economy_block.py`, `mobility_block.py`, or `daily_schedule_block.py`, use the existing `PromptManager` pattern in that file.

### CitySim Citizen Agent (`SocietyAgent`)

The default citizen agent in `cityagent/societyagent.py` models:
- **4 needs**: `hunger_satisfaction`, `energy_satisfaction`, `safety_satisfaction`, `social_satisfaction`
- **Big Five personality**: `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`
- **6-dimensional emotion** state
- **Goals**, **hobbies**, `life_stage`, `household` — all LLM-generated at init from demographics

Institution agents: `BankAgent`, `FirmAgent`, `GovernmentAgent`, `NBSAgent` in `cityagent/`.

### Configuration (Pydantic models)

All config lives in `configs/__init__.py`. Workflow steps are defined as a list of `WorkflowStepConfig` objects with types from `WorkflowType`:
`RUN`, `STEP`, `INTERVIEW`, `SURVEY`, `UPDATE_STATE`, `FUNCTION`, `NEXT_ROUND`, `DELETE_AGENT`

### External Simulators

`SimulationEngine` connects to external C++ binaries (via gRPC) for mobility and economy simulation. These are managed by `InfrastructureManager` and accessed through the `Environment` facade (`environment/environment.py`).

### Storage

`DatabaseWriter` batches writes to SQLite (dev) or PostgreSQL (prod). Schema models are in `storage/type.py`. A `DataRecorder` in `simulation/datarecorder.py` handles experiment-level data capture.

### Observability

`performance/` provides an optional Prometheus + Grafana + ClickHouse + Loki stack. `PrometheusActor` and `DatabaseActor` are Ray actors for metrics. Enable via Docker Compose in `performance/`.

### Testing

Always run tests using the shell script, never with `python` directly:

```bash
# From packages/agentsociety/
sh tests/run_e2e_tests.sh
```

The script handles Python interpreter selection, Ray environment variables, and working directory setup. Running individual test files with `python` directly will fail due to missing environment setup.