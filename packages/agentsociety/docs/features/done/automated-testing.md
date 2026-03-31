# End-to-End Simulation Test

> A single-command, real end-to-end simulation test: one citizen agent, one day, 10 steps at 600 ticks each, using a real LLM and a real environment. Passes if the simulation completes without any exception.

## Purpose & Motivation

The project currently has no test suite. Correctness is validated manually by running scripts in `/mnt/raid5/gustavo/citysim/examples/`. Every non-trivial change — a new block, a prompt refactor, an engine change — is unverifiable until a developer manually runs a full example script.

This feature introduces a minimal automated gate: confirm the engine initializes, runs 10 steps against a real LLM and real environment, and does not crash. The intent is to catch regression bugs introduced by code changes while keeping the test simple enough to run with one command.

The primary driver is the sim/citysim branch, which has accumulated several refactors (PromptManager, DataRecorder, InfrastructureManager, load-balanced LLM). None of these are regression-tested.

## Success Criteria

1. `python tests/e2e/run_e2e.py` exits `0` after completing 10 simulation steps.
2. Any unhandled exception causes the script to exit `1` and log the full traceback.
3. The test is configurable: LLM endpoints and map file path are set in a YAML file.

## Scope

**In scope:**
- A single runner script at `tests/e2e/run_e2e.py`
- A default YAML config at `tests/e2e/config.default.yaml`
- One real `SimulationEngine` run: 1 `SocietyAgent`, 10 `WorkflowType.STEP` steps, 600 ticks/step
- Configurable LLM endpoint (default: local vLLM at `localhost:8080`)
- Configurable map file path (user provides a small `.pb` file for testing)
- No demographics/memory file — agent uses generated distributions from `default()`
- Standard Python `logging` output only (no Prometheus, no ClickHouse)
- SQLite database enabled (normal simulation output)

**Out of scope:**
- Mocks, stubs, or fakes of any kind
- pytest, GitHub Actions CI, or any test framework
- Multi-agent tests
- Institution agents (`FirmAgent`, `BankAgent`, `GovernmentAgent`, `NBSAgent`)
- Survey, interview, and intervention workflow steps
- Performance benchmarks

## Design

### Files

```
tests/
└── e2e/
    ├── run_e2e.py          # runner script
    └── config.default.yaml # default config (edit before running)
```

### Runner Script (`run_e2e.py`)

- Accepts `--config <path>` CLI argument; defaults to `config.default.yaml` in the same directory
- Loads config with `load_config_from_file(path, Config)` from `agentsociety.configs.utils`
- Applies `default(config)` from `agentsociety.cityagent` to resolve string agent class names and fill in default blocks/memory distributions
- Creates and runs the simulation: `AgentSociety.create(config)` → `init()` → `run()` → `close()`
- On success: logs `E2E test PASSED` and exits `0`
- On any exception: logs `E2E test FAILED` with full traceback and exits `1`

### YAML Config (`config.default.yaml`)

Key fields and their values for the automated test:

| Field | Value | Notes |
|---|---|---|
| `llm[0].provider` | `vllm` | Local vLLM instance |
| `llm[0].base_url` | `http://localhost:8080/v1/` | Default endpoint |
| `llm[0].model` | `Qwen/Qwen2.5-32B-Instruct-AWQ` | Default model |
| `map.file_path` | configurable | User provides a small `.pb` map |
| `map.neighborhood_file_path` | `null` | Not required for basic test |
| `agents.citizens[0].agent_class` | `citizen` | Resolved to `SocietyAgent` by `default()` |
| `agents.citizens[0].number` | `1` | Single agent |
| `agents.citizens[0].memory_from_file` | *(absent)* | Uses generated distributions instead |
| `exp.workflow[0].type` | `step` | `WorkflowType.STEP` |
| `exp.workflow[0].steps` | `10` | 10 agent steps |
| `exp.workflow[0].ticks_per_step` | `600` | Ticks per step |
| `exp.environment.start_tick` | `25200` | 7:00 AM (7 × 60 × 60) |
| `exp.environment.workday` | `true` | Weekday mode |
| `env.db.enabled` | `true` | SQLite output enabled |
| `env.db.db_type` | `sqlite` | |
| `logging_level` | `DEBUG` | Full logging output |

### Usage

```bash
# Run with default config (edit map.file_path first)
python tests/e2e/run_e2e.py

# Run with a custom config
python tests/e2e/run_e2e.py --config /path/to/my_config.yaml
```

## Configuration Before Running

1. **Map file**: Set `map.file_path` in `config.default.yaml` (or your own config) to a small `.pb` map file. The user provides this separately.
2. **LLM endpoint**: Default is `http://localhost:8080/v1/` with `Qwen/Qwen2.5-32B-Instruct-AWQ`. Adjust `base_url` and `model` as needed.
3. **Data directories**: `env.home_dir` and `env.data_dir` default to `../../agentsociety_data` and `../../agentsociety_db` relative to the script. Adjust as needed.

## Trade-Offs

| Gain | Cost |
|---|---|
| Tests the real code path end-to-end | Requires a running LLM and a real map file |
| No mocks that drift from reality | Slower than a pure unit test |
| Simple — one file, one command | Cannot run in CI without infrastructure |
| Catches real integration bugs | Does not test specific agent behaviors, only that nothing crashes |

## Rejected Approaches

**Approach: pytest with mocks/stubs for LLM and C++ binary**
**Why rejected**: User explicitly wants end-to-end testing with real LLM and real environment. Unit testing, smoke testing, and integration testing with fakes are out of scope. The goal is to confirm the system works in its actual running state, especially after code changes.

**Approach: Use `IndividualEngine` instead of `SimulationEngine`**
**Why rejected**: `IndividualEngine` uses a task-solver paradigm that does not exercise the block dispatch system, mobility, or economy paths. It would not catch regressions in the main city simulation code.

**Approach: Hardcode the config in the script**
**Why rejected**: The user needs to configure different LLM endpoints and map files depending on the machine. YAML config + `--config` flag gives flexibility without changing code.

## Implementation Status

| File | Status |
|---|---|
| `tests/e2e/run_e2e.py` | Done |
| `tests/e2e/config.default.yaml` | Done |
