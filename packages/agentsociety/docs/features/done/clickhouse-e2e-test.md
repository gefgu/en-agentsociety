# ClickHouse E2E Test with Testcontainers
> An end-to-end simulation test that spins up a throwaway ClickHouse container, runs the full simulation with `monitoring_enabled: true`, and passes if no exceptions are raised.

## Purpose & Motivation

The existing e2e test (`tests/e2e/run_e2e.py`) always sets `monitoring_enabled: false` in its config (`tests/e2e/config.default.yaml:17`). This means the entire ClickHouse path — `InfrastructureManager._init_clickhouse_actor()`, `DatabaseActor`, `ClickHouseDatabase._connect()`, and all `flush_batch` calls — is bypassed in every CI run.

Bugs in the ClickHouse write pipeline can therefore survive silently: schema mismatches, `clickhouse-connect` version incompatibilities, batch-flush errors, and actor teardown failures are all invisible until the monitoring stack is brought up manually. This test closes that gap by exercising the full path in an isolated, reproducible container.

The timing is right because: (1) `testcontainers[clickhouse]` already resolves correctly against the repo's Python version constraint (`>=3.11,<3.13`), (2) `clickhouse-connect` is already in `tests/e2e/pyproject.toml:11`, and (3) the `ClickHouseConfig` Pydantic model (`configs/env.py:15`) already accepts `host` and `port` fields, so wiring the container coordinates requires only programmatic config mutation — no structural changes to the production code.

## Success Criteria

The test runs to completion without raising any exception. Specifically:

- `DatabaseActor` is constructed and connects to the testcontainer successfully.
- The simulation completes its 10-step / 600-tick-per-step workflow.
- `society.close()` is called, the ClickHouse actor flushes its batches, and the connection closes cleanly.
- The process exits 0.

No row-count assertions, schema inspections, or query checks are required for this phase.

## Scope

**In scope:**
- A new test file `tests/e2e/run_e2e_clickhouse.py` that mirrors `run_e2e.py` but adds testcontainer setup/teardown.
- A new config file `tests/e2e/config.clickhouse.yaml` that is identical to `config.default.yaml` except `monitoring_enabled: true` and a placeholder `clickhouse:` block whose `host`/`port` the test script overwrites at runtime.
- Adding `testcontainers[clickhouse]` to `tests/e2e/pyproject.toml` as a new dependency.
- Updating `tests/run_e2e_tests.sh` to optionally run the new test (or documenting the standalone command).

**Out of scope:**
- Prometheus, Grafana, Loki, or Alloy containers — `monitoring_enabled: true` guards only the ClickHouse actor and Docker Compose stack startup; the Compose stack itself is bypassed because `_start_monitoring_services()` (`infrastructuremanager.py:259`) calls `start_monitoring()` which will fail gracefully when Docker Compose cannot find the stack. Only the `_init_clickhouse_actor()` branch at `infrastructuremanager.py:290` matters.
- Row-count or schema assertions.
- Wiring the testcontainer into the Prometheus actor or OTLP log handler.
- Any changes to production source code.

## Constraints

- Python version: `>=3.11,<3.13` (inherited from `tests/e2e/pyproject.toml:7`).
- `testcontainers[clickhouse]` pulls `clickhouse-driver` (native protocol, port 9000) as its own client. The simulation uses `clickhouse-connect` (HTTP protocol, port 8123). Both libraries are independent; having both installed causes no conflict. The test script uses only `ClickHouseContainer` from `testcontainers` for lifecycle and `get_exposed_port(8123)` for the HTTP port; it never calls `clickhouse-driver` directly.
- Docker must be available on the machine running the test. `ClickHouseContainer` will raise `DockerException` if the Docker daemon is unreachable; that failure mode should surface as a clear error, not a silent skip.
- The `monitoring_enabled: true` config path calls `start_monitoring()` at `infrastructuremanager.py:265`, which runs `docker compose up -d` for the full Prometheus/Grafana stack. This will fail in CI because that Docker Compose file is not present in the test venv. The call is wrapped in a `try/except` at lines 264–270 and logs a warning on failure, so the simulation continues. The ClickHouse actor is initialized on a separate call at line 361 (`_init_clickhouse_actor()`) and is therefore not affected by the Compose failure.

## Architecture & Integration Points

The call chain from test entry point to ClickHouse write:

```
run_e2e_clickhouse.py::main()
  → ray.init()
  → ClickHouseContainer.__enter__()          # testcontainers spins up Docker container
  → config.env.clickhouse.host = ...         # mutate Pydantic model in-process
  → config.env.clickhouse.port = ...
  → AgentSociety.create(config)              # simulation/agentsociety.py:55
      → SimulationEngine(config, tenant_id)  # simulation/simulationengine.py
  → society.init()
      → InfrastructureManager.initialize_all()  # simulation/infrastructuremanager.py:357
          → _start_monitoring_services()         # line 360 — warns and skips if Compose absent
          → _init_clickhouse_actor()             # line 361
              → DatabaseActor.remote(            # database/database_actor.py:15
                    host=<container_host>,
                    port=<container_8123_port>,
                    username="test",
                    password="test",
                    database="testing",
                    ...)
                  → ClickHouseDatabase.__init__() # database/clickhouse.py:47
                  → ClickHouseDatabase._connect() # database/clickhouse.py:116
                  → ClickHouseDatabase._create_tables() # database/clickhouse.py:154
  → society.run()
      → SimulationEngine step loop
          → DataRecorder.enqueue_clickhouse_status()  # simulation/datarecorder.py:86
          → DatabaseActor.insert_*/flush_batch calls  # database/clickhouse.py:226+
  → society.close()
      → InfrastructureManager.close()             # infrastructuremanager.py:364
          → db_actor.close.remote()               # flushes remaining batches, closes client
  → ClickHouseContainer.__exit__()            # container destroyed
```

Key files and line references for the integration path:

- `agentsociety/configs/env.py:15` — `ClickHouseConfig` Pydantic model; `host` (line 18), `port` (line 21), `username` (line 24), `password` (line 27), `database` (line 30).
- `agentsociety/configs/env.py:65` — `EnvConfig.monitoring_enabled` field.
- `agentsociety/simulation/infrastructuremanager.py:259` — `_start_monitoring_services()` — guarded by `monitoring_enabled`, fails gracefully if Compose stack absent.
- `agentsociety/simulation/infrastructuremanager.py:290` — `_init_clickhouse_actor()` — reads `config.env.clickhouse.*` and constructs `DatabaseActor.remote(...)`. This is the critical path under test.
- `agentsociety/simulation/infrastructuremanager.py:296–307` — the six fields consumed from `ClickHouseConfig` that the test must populate correctly.
- `agentsociety/database/clickhouse.py:116` — `_connect()` — calls `clickhouse_connect.get_client(host=..., port=..., username=..., password=...)`.
- `agentsociety/simulation/datarecorder.py:86` — `enqueue_clickhouse_status()` — produces the records that exercise the write path.
- `agentsociety/simulation/infrastructuremanager.py:364` — `close()` — calls `db_actor.close.remote()`, triggering final flush.

## Similar Patterns & Reuse

- **Existing e2e test structure**: `tests/e2e/run_e2e.py:45` — `async def run(config_path)` — loads config, calls `default(config)`, creates society, calls `init()`/`run()`/`close()`. The new test copies this structure exactly and wraps it with container lifecycle.
- **Config loading**: `agentsociety/configs/utils.py:8` — `load_config_from_file(filepath, Config)` — YAML-to-Pydantic deserialization used in the existing test at `run_e2e.py:47`. The new test calls this identically, then mutates the resulting `Config` object in-process before passing it to `AgentSociety.create()`.
- **Pydantic model mutation**: `ClickHouseConfig` is a plain `BaseModel` instance accessible via `config.env.clickhouse`. Standard attribute assignment (`config.env.clickhouse.host = "..."`) works because Pydantic v2 models are mutable by default unless `model_config = ConfigDict(frozen=True)` is set — and `ClickHouseConfig` sets no such restriction (`configs/env.py:15`).
- **uv-managed test venv**: `tests/e2e/pyproject.toml` — the test uses a dedicated `uv` venv separate from the main package. New dependencies go in this file's `dependencies` list.

## Implementation Strategy

### Step 1: Add `testcontainers[clickhouse]` to the test venv

**Before**: `tests/e2e/pyproject.toml:8–13` has four dependencies: `agentsociety`, `clickhouse-connect`, `opentelemetry-exporter-otlp-proto-grpc`, `setuptools`.

**After**: Add `"testcontainers[clickhouse]"` to that list. This pulls `testcontainers` core (Docker SDK wrapper, wait strategies) and `clickhouse-driver` (used only by testcontainers internally for its `get_connection_url` helper — never called by our code).

```toml
dependencies = [
  "agentsociety",
  "clickhouse-connect",
  "opentelemetry-exporter-otlp-proto-grpc",
  "setuptools",
  "testcontainers[clickhouse]",
]
```

### Step 2: Create `tests/e2e/config.clickhouse.yaml`

**Before**: No config file exists that enables monitoring.

**After**: A new YAML file that is a copy of `config.default.yaml` with two changes: `monitoring_enabled: true` and a `clickhouse:` block with placeholder values. The test script will overwrite `host`, `port`, `username`, `password`, and `database` in-process after loading, so the YAML values serve only as documentation of intent.

```yaml
llm:
  - provider: vllm
    base_url: "http://localhost:8080/v1/"
    api_key: ""
    model: "Qwen/Qwen2.5-32B-Instruct-AWQ"
    concurrency: 256
    timeout: 60

env:
  db:
    enabled: true
    db_type: sqlite
  clickhouse:
    # host and port are overwritten at runtime by the testcontainer
    host: "localhost"
    port: 8123
    username: "test"
    password: "test"
    database: "testing"
    auto_create_database: true
  home_dir: "./data/home_data/"
  data_dir: "./data/data"
  monitoring_enabled: true

map:
  file_path: "./data/home_data/studied_massy_osm_pois.pb"
  neighborhood_file_path: null

agents:
  citizens:
    - agent_class: citizen
      number: 1

exp:
  name: "e2e_test_clickhouse"
  workflow:
    - type: step
      steps: 10
      ticks_per_step: 600
  environment:
    start_tick: 25200
    workday: true
    weather: "The weather is sunny"
    temperature: "The temperature is 15C"

logging_level: INFO
```

### Step 3: Create `tests/e2e/run_e2e_clickhouse.py`

**Before**: No file exists. The existing `run_e2e.py:45–56` is the closest pattern.

**After**: New file that imports `ClickHouseContainer`, starts it, mutates the config, then delegates to the same `run()` coroutine shape. The container is kept alive for the entire duration of `society.init()` + `society.run()` + `society.close()` so actor connections are valid throughout.

```python
"""
End-to-end simulation test with live ClickHouse container.

Spins up a throwaway ClickHouse container via testcontainers, runs a
single SocietyAgent for 10 steps (600 ticks each) with monitoring_enabled=true,
and exits 0 if no exception is raised.

Usage:
    python tests/e2e/run_e2e_clickhouse.py
    python tests/e2e/run_e2e_clickhouse.py --config /path/to/config.clickhouse.yaml
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import os

# Must be set before importing ray.
os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"

import ray
from testcontainers.clickhouse import ClickHouseContainer

from agentsociety.cityagent import default  # type: ignore
from agentsociety.configs import Config  # type: ignore
from agentsociety.configs.utils import load_config_from_file  # type: ignore
from agentsociety.simulation import AgentSociety  # type: ignore

DEFAULT_CONFIG = Path(__file__).parent / "config.clickhouse.yaml"

CLICKHOUSE_IMAGE = "clickhouse/clickhouse-server:latest"
CLICKHOUSE_USERNAME = "test"
CLICKHOUSE_PASSWORD = "test"
CLICKHOUSE_DATABASE = "testing"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AgentSociety ClickHouse end-to-end test"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    return parser.parse_args()


async def run(config: Config) -> None:
    society = AgentSociety.create(config)
    try:
        await society.init()
        await society.run()
        logging.info(
            "E2E ClickHouse test PASSED — simulation completed without exceptions."
        )
    finally:
        await society.close()


def main() -> None:
    args = parse_args()

    if not args.config.exists():
        print(f"ERROR: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    # Start the throwaway ClickHouse container. The context manager blocks until
    # the HTTP port 8123 returns "Ok" (ClickHouseContainer._connect wait strategy).
    with ClickHouseContainer(
        image=CLICKHOUSE_IMAGE,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        dbname=CLICKHOUSE_DATABASE,
    ) as clickhouse:
        host = clickhouse.get_container_host_ip()
        port = int(clickhouse.get_exposed_port(8123))

        logging.info(f"ClickHouse container ready at {host}:{port}")

        # Load the YAML config, then overwrite the ClickHouse coordinates so the
        # simulation connects to our throwaway container instead of a real server.
        config: Config = load_config_from_file(str(args.config), Config)
        config = default(config)

        config.env.monitoring_enabled = True
        config.env.clickhouse.host = host
        config.env.clickhouse.port = port
        config.env.clickhouse.username = CLICKHOUSE_USERNAME
        config.env.clickhouse.password = CLICKHOUSE_PASSWORD
        config.env.clickhouse.database = CLICKHOUSE_DATABASE

        ray.init()

        try:
            asyncio.run(run(config))
        except Exception as e:
            logging.exception(f"E2E ClickHouse test FAILED: {e}")
            sys.exit(1)
        finally:
            ray.shutdown()


if __name__ == "__main__":
    main()
```

### Step 4: Update `tests/run_e2e_tests.sh` (optional but recommended)

**Before**: The shell script runs only `run_e2e.py` (`tests/run_e2e_tests.sh:28`).

**After**: Add an optional `--clickhouse` flag, or simply run the new test unconditionally after the existing one. The simplest approach that preserves the current fast path:

```sh
# Run the baseline test first (no monitoring)
uv run python "run_e2e.py" "$@"

# Run the ClickHouse test (requires Docker)
uv run python "run_e2e_clickhouse.py" "$@"
```

Alternatively, gate on an env var so CI can opt in:

```sh
if [ "${RUN_CLICKHOUSE_E2E:-0}" = "1" ]; then
    uv run python "run_e2e_clickhouse.py" "$@"
fi
```

## Trade-Offs

| Gained | Sacrificed / Risked |
|--------|---------------------|
| Full ClickHouse write path is exercised in CI | Test requires Docker daemon; fails on Docker-less runners |
| Connection failures surface before production | Container pull adds ~30–60 s on first run (image is cached thereafter) |
| Actor teardown and final flush verified | `monitoring_enabled: true` triggers a harmless `start_monitoring()` warning about Docker Compose not being available, adding noise to test output |
| No changes to production code or existing test | Two separate venv lockfiles (`uv.lock`) must be kept consistent when adding the new dependency |
| Config mutation is in-process — no temp file needed | Pydantic model mutation is silent; if `ClickHouseConfig` is ever made frozen, the assignment will raise at runtime |

## Rejected Approaches

**Writing a modified YAML to a tempfile, then passing its path to the existing `run_e2e.py`**
Rejected because: the container's mapped port is only known at runtime, after the container starts. Writing the port into a YAML file and passing it via `--config` would work, but creates a temp file that must be cleaned up and couples the shell script to the test implementation. In-process Pydantic mutation is cleaner and keeps all test logic in one Python file.

**Using `docker-compose` with a `clickhouse-only` profile**
Rejected because: this reuses the production `performance/docker-compose.yml` fixture, which mounts host paths and volume names that will conflict if multiple tests run in parallel. Testcontainers assigns random host ports and unique container names, making it collision-safe by design.

**Setting `monitoring_enabled: false` and constructing `DatabaseActor` manually in the test**
Rejected because: the goal is to test the actual production code path, including the guard at `infrastructuremanager.py:292`. Constructing the actor outside `InfrastructureManager` would bypass the code under test.

**Using `pytest` with a `@pytest.fixture` for the container**
Rejected because: the existing test suite uses plain Python scripts, not pytest. Introducing pytest would require framework setup and is out of scope; it can be done in a follow-on.

**Pinning to a specific ClickHouse image version (e.g., `21.8`)**
Rejected for now because: the production `docker-compose.yml` at `performance/docker-compose.yml:42` uses `clickhouse/clickhouse-server:latest`. Using the same tag keeps the test representative of the production environment. If schema or API drift becomes a problem, pinning can be added then.

## Assumptions & Open Questions

1. **Pydantic v2 model mutability**: `ClickHouseConfig` does not set `model_config = ConfigDict(frozen=True)`, so direct attribute assignment (`config.env.clickhouse.host = ...`) is valid. Confirmed by reading `configs/env.py:15` — no `model_config` is defined.

2. **`monitoring_enabled: true` in the test does not block on Docker Compose**: Confirmed by reading `infrastructuremanager.py:259–270` — `start_monitoring()` is called inside a `try/except Exception` block that logs a warning and continues. The ClickHouse actor is initialized on a separate, unconditional call at line 361.

3. **Container host reachability from Ray actors**: Ray worker processes run on `localhost` by default in single-node mode. `clickhouse.get_container_host_ip()` returns `"localhost"` or `"127.0.0.1"` on Linux when Docker uses the default bridge network. This is the same host as the Ray workers, so connectivity is guaranteed. If running on a Docker-in-Docker CI environment, this assumption may not hold.

4. **`uv.lock` regeneration**: Adding `testcontainers[clickhouse]` to `pyproject.toml` requires running `uv lock` inside `tests/e2e/` to regenerate `uv.lock`. The plan does not include the lock file content; the implementer must run this step.

5. **Open question**: Should the test call `ray.shutdown()` in a `finally` block or let Ray shut down naturally? The existing `run_e2e.py` does not call `ray.shutdown()` (`run_e2e.py:59–73` — no explicit shutdown). The new test includes it explicitly in `finally` to ensure Ray cleans up its actor handles before the testcontainer is destroyed. If `ray.shutdown()` is called before `society.close()`, pending remote calls will fail. The plan places `ray.shutdown()` in the outer `finally` block, after `asyncio.run(run(config))` completes (which already called `society.close()`).

## Code That Could Be Refactored *(informational)*

- `tests/e2e/run_e2e.py:45–56` — the `async def run(config_path)` function accepts a `Path` and loads the config internally. If it accepted a pre-loaded `Config` object instead, both the existing test and the new ClickHouse test could share the same `run()` coroutine body without duplication. Not a blocker, but worth noting for a future cleanup pass.

- `agentsociety/simulation/infrastructuremanager.py:259–270` — `_start_monitoring_services()` calls `start_monitoring()` (which launches Docker Compose) and `_init_metrics_actor()` (which creates the Prometheus actor) in the same function. These are logically independent: a test might want the Prometheus actor without the full Compose stack. Splitting them would make the monitoring path more testable.

## Proposed Next Steps

1. Add `"testcontainers[clickhouse]"` to `tests/e2e/pyproject.toml:dependencies`.
2. Run `cd tests/e2e && uv lock` to regenerate `uv.lock`.
3. Create `tests/e2e/config.clickhouse.yaml` with the content shown in Step 2 above.
4. Create `tests/e2e/run_e2e_clickhouse.py` with the content shown in Step 3 above.
5. Update `tests/run_e2e_tests.sh` per Step 4, either unconditionally or gated on `RUN_CLICKHOUSE_E2E=1`.
6. Run the test manually once to verify:
   ```sh
   cd /mnt/raid5/gustavo/citysim/packages/agentsociety/tests/e2e
   uv run python run_e2e_clickhouse.py
   ```
7. Confirm the process exits 0 and that the log contains both "ClickHouse container ready at" and "ClickHouse actor initialized" and "E2E ClickHouse test PASSED".
