# DuckDB Resume Tests
> Explicit end-to-end tests that verify the DuckDB backend can write, checkpoint, and restore simulation state across a simulated crash.

## Purpose & Motivation

The DuckDB backend is the only fallback path when ClickHouse is unavailable. It shares all resume logic with the ClickHouse backend through `BaseSimulationDatabase.fetch_resume_data()` and `_fetch_checkpoint_snapshots()`, but no test currently exercises it explicitly. The existing resume tests (`003_resume_agent_state.py`, `004_resume_moving_agent_state.py`, `005_resume_lane_position_state.py`) all spin up a ClickHouse testcontainer and rely on ClickHouse being available — DuckDB is only activated implicitly when ClickHouse fails. There is no test that starts with DuckDB from the beginning, writes checkpoints through it, and then resumes from those checkpoints.

The user reports that ClickHouse resume works well; they are not confident about DuckDB. That asymmetry is a blind spot.

## Success Criteria

1. A test named `007_resume_with_duckdb.py` exists in `tests/e2e/` and passes when run with `sh tests/run_e2e_tests.sh`.
2. The test verifies that, after a simulated crash, a second run re-reads checkpoint data from the `.duckdb` file and completes the remaining steps.
3. The test verifies the DuckDB file path `<data_dir>/duckdb/<exp_id>.duckdb` is non-empty after run 1.
4. The test verifies that `last_mobility_safe_step` in the DuckDB `experiment_info` table is positive after run 1 (confirming a checkpoint was actually written to DuckDB).
5. Run 2 completes without raising an exception.

## Scope

**In scope:**
- A single new e2e test file `tests/e2e/007_resume_with_duckdb.py`.
- A new YAML config `tests/e2e/configs/007_resume_with_duckdb.yaml` mirroring the 1-agent resume config but with DuckDB forced as the active backend.
- A helper function `build_duckdb_config()` in `tests/e2e/utils.py` that forces DuckDB by pointing ClickHouse at an unreachable host.
- A `query_duckdb()` helper in `tests/e2e/utils.py` (analogous to `create_clickhouse_client()`) to directly inspect the DuckDB file from the test driver.
- Adding `duckdb>=1.1.0` to `tests/e2e/pyproject.toml` dependencies.
- Updating `tests/run_e2e_tests.sh` to include the new test.

**Out of scope:**
- Unit tests of DuckDB-specific SQL conversion (`_to_duckdb_statements`, `_convert_clickhouse_types`, etc.) — these are isolated pure-Python functions and could have their own unit test file, but are not part of this plan.
- Testing DuckDB-to-ClickHouse failover or mid-run backend switching.
- Moving-agent or lane-position variants of the DuckDB resume test (those scenarios are covered by tests 004 and 005 for ClickHouse; DuckDB parallels can be added later once the baseline passes).

## Constraints

- There is no `testcontainers[duckdb]` package. DuckDB runs in-process with a file on disk. No container is needed — the test is simpler than the ClickHouse tests.
- The `duckdb` Python package is an optional dependency of `agentsociety` (declared under `[project.optional-dependencies] duckdb` in `pyproject.toml:33`). It must be added to `tests/e2e/pyproject.toml` explicitly.
- All tests run via `tests/run_e2e_tests.sh` using the `.venv/bin/python` interpreter.
- The DuckDB file is stored at `<data_dir>/duckdb/<exp_id>.duckdb` (set by `DuckDBConfig.resolve_db_file()` at `agentsociety/database/duckdb.py:26`).

## Architecture & Integration Points

The call chain for DuckDB resume is identical to ClickHouse except for the concrete class used in `DatabaseActor.__init__`:

- `tests/e2e/007_resume_with_duckdb.py` — new file, calls `run_with_ray(run_society(config))` twice
- `tests/e2e/utils.py:59` — `build_clickhouse_config()` is the model; `build_duckdb_config()` will be a parallel helper that sets a broken ClickHouse host so `DatabaseActor` falls back to DuckDB
- `agentsociety/simulation/agentsociety.py` — `AgentSociety.create(config)` returns `SimulationEngine`
- `agentsociety/simulation/simulationengine.py:70` — reads `config.env.exp_id` to determine resume mode; if set, uses it as the source experiment
- `agentsociety/simulation/simulationengine.py:249` — calls `infrastructure_manager.load_resume_state(expected_agent_ids)`
- `agentsociety/simulation/infrastructuremanager.py:559` — `_init_clickhouse_actor()` creates `DatabaseActor.remote(...)` with the ClickHouse config from YAML; the actor tries ClickHouse first
- `agentsociety/database/database_actor.py:44-74` — `DatabaseActor.__init__` tries `ClickHouseDatabase.is_available()`; on failure falls back to `DuckDBDatabase`
- `agentsociety/database/duckdb.py:77-89` — `DuckDBDatabase._connect()` opens `<data_dir>/duckdb/<exp_id>.duckdb`
- `agentsociety/database/duckdb.py:91-140` — `DuckDBDatabase._create_tables()` converts all 13 ClickHouse migration files at runtime via `_to_duckdb_statements()`
- `agentsociety/database/base_database.py:383-463` — `fetch_resume_data()` is the shared resume data loader; both backends call it
- `agentsociety/database/duckdb.py:283-369` — `DuckDBDatabase._resume_query()` provides DuckDB-flavored SQL for all six named queries (`latest_experiment_info`, `latest_step`, `candidate_steps`, `kv_rows`, `stream_rows`, `spatial_rows`, `pending_messages`, `experiment_info_for_update`)
- `agentsociety/simulation/checkpointmanager.py:509-608` — `save_checkpoint()` writes snapshots and calls `db_actor.update_experiment_info_checkpoint.remote(...)` to record `last_mobility_safe_step`

The checkpoint write path is:

`CheckpointManager.save_checkpoint()` at `checkpointmanager.py:509` → `DataRecorder.enqueue_kv_snapshot()` → `DatabaseActor.insert_kv_snapshot_batch.remote()` → `BaseSimulationDatabase.insert_records()` → `DuckDBDatabase._flush_records()` at `duckdb.py:235-248`

The resume read path is:

`InfrastructureManager.load_resume_state()` at `infrastructuremanager.py:273` → `DatabaseActor.fetch_resume_data.remote()` at `database_actor.py:235` → `BaseSimulationDatabase.fetch_resume_data()` at `base_database.py:383` → `_fetch_checkpoint_snapshots()` at `base_database.py:465` → `DuckDBDatabase._resume_query()` + `_query_rows()` at `duckdb.py:255-267`

## Similar Patterns & Reuse

- **What it is**: `tests/e2e/utils.py:42` — `apply_clickhouse_overrides(config, host, port, exp_id)`
- **What it does**: Mutates a loaded `Config` to point at a given ClickHouse host/port and optionally fix the experiment ID.
- **How this feature uses it**: A new `apply_duckdb_overrides(config, exp_id)` will instead set `config.env.clickhouse.host = "127.0.0.1"` and `config.env.clickhouse.port = 1` (an unreachable address) to force the `DatabaseActor` to fall back to DuckDB. No container is needed.

- **What it is**: `tests/e2e/003_resume_agent_state.py` — the minimal two-run crash+resume test
- **What it does**: Run 1 crashes after a timeout; Run 2 resumes with the same `exp_id`.
- **How this feature uses it**: The DuckDB test follows the same two-run structure exactly, replacing ClickHouse setup with the DuckDB override approach.

- **What it is**: `tests/e2e/utils.py:97` — `run_society(config, timeout, raise_on_timeout)`
- **What it does**: Creates `AgentSociety`, calls `init()` and `run()` with an optional wall-clock timeout.
- **How this feature uses it**: Reused without modification for both run 1 (crash) and run 2 (resume).

## Implementation Strategy

### Step 1: Add `duckdb` to the e2e test environment

**Before**: `tests/e2e/pyproject.toml:8-14` lists `agentsociety`, `clickhouse-connect`, `opentelemetry-exporter-otlp-proto-grpc`, `setuptools`, `testcontainers[clickhouse]` only.

**After**: Add `duckdb>=1.1.0` to that dependencies list. Run `uv sync` in `tests/e2e/` to update the lockfile.

### Step 2: Add `build_duckdb_config()` and `query_duckdb()` helpers to `utils.py`

**Before**: `tests/e2e/utils.py:42` has `apply_clickhouse_overrides()` and `build_clickhouse_config()` — no DuckDB equivalent.

**After**: Add two functions:

```
def apply_duckdb_overrides(config: Config, exp_id: str | None = None) -> Config:
    # Force ClickHouse to an unreachable address so DatabaseActor falls back to DuckDB.
    config.env.clickhouse.host = "127.0.0.1"
    config.env.clickhouse.port = 1         # guaranteed unreachable
    config.env.monitoring_enabled = False
    if exp_id is not None:
        config.env.exp_id = exp_id
    return config

def build_duckdb_config(config_path, exp_id=None):
    config = load_default_config(config_path)
    return apply_duckdb_overrides(config, exp_id=exp_id)

def query_duckdb(db_file: Path, sql: str, params=None) -> list[dict]:
    import duckdb
    conn = duckdb.connect(str(db_file), read_only=True)
    try:
        cursor = conn.execute(sql, params or [])
        rows = cursor.fetchall()
        cols = [d[0] for d in (cursor.description or [])]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()
```

`query_duckdb()` attaches to `<data_dir>/duckdb/<exp_id>.duckdb` from outside Ray. It is the DuckDB analogue of `create_clickhouse_client()` at `utils.py:85`.

### Step 3: Create the YAML config `007_resume_with_duckdb.yaml`

**Before**: No such config exists.

**After**: Copy `tests/e2e/configs/003_resume_single_agent_with_local.yaml`, change `exp.name` to `e2e_test_duckdb_resume`, keep `database_enabled: true`, keep `clickhouse` block (it will be overridden at runtime anyway). The clickhouse block in the YAML file does not matter because `apply_duckdb_overrides` replaces host/port at runtime.

### Step 4: Write `tests/e2e/007_resume_with_duckdb.py`

**Before**: No DuckDB-explicit resume test exists.

**After**: A new script with this structure:

```
DEFAULT_CONFIG = Path(__file__).parent / "configs/007_resume_with_duckdb.yaml"
CRASH_TIMEOUT_SECONDS = 300  # same as test 003

def main():
    exp_id = str(uuid.uuid4())

    # RUN 1: crash after timeout
    config_run1 = build_duckdb_config(DEFAULT_CONFIG, exp_id=exp_id)
    try:
        run_with_ray(run_society(config_run1, timeout=CRASH_TIMEOUT_SECONDS))
    except Exception:
        pass  # crash expected

    # Assert DuckDB file exists and has a checkpoint
    duckdb_file = Path(config_run1.env.data_dir) / "duckdb" / f"{exp_id}.duckdb"
    assert duckdb_file.exists(), f"DuckDB file not found: {duckdb_file}"
    rows = query_duckdb(duckdb_file,
        "SELECT last_mobility_safe_step FROM experiment_info "
        "WHERE id = ? ORDER BY updated_at DESC LIMIT 1",
        [exp_id])
    assert rows, "No experiment_info row found in DuckDB"
    safe_step = rows[0]["last_mobility_safe_step"]
    assert safe_step > 0, f"Expected last_mobility_safe_step > 0, got {safe_step}"
    logging.info(f"Run 1 wrote checkpoint at step {safe_step} to DuckDB.")

    # RUN 2: resume
    config_run2 = build_duckdb_config(DEFAULT_CONFIG, exp_id=exp_id)
    run_with_ray(run_society(config_run2))  # must complete without raising
    logging.info("DuckDB RESUME test PASSED.")
```

The assertion block between run 1 and run 2 is the key addition not present in test 003 — it proves DuckDB actually wrote a usable checkpoint, not just that the simulation ran to completion.

### Step 5: Update `tests/run_e2e_tests.sh`

**Before**: The active (uncommented) line runs only `003_resume_agent_state.py`.

**After**: Add a line for `007_resume_with_duckdb.py` alongside (or instead of) 003, depending on whether the operator wants both.

## Trade-Offs

**Gained**: Explicit coverage of the DuckDB code path through the full write/read/restore cycle. Any regression in `DuckDBDatabase._resume_query()`, `_flush_records()`, or `_to_duckdb_statements()` will be caught.

**Sacrificed**: The "force DuckDB" mechanism (pointing ClickHouse at port 1) relies on the fallback behavior in `DatabaseActor.__init__:54` being stable. If someone adds a config flag to select backend explicitly, this approach becomes obsolete. A proper `force_backend: duckdb` config field would be cleaner but is out of scope.

**Risk**: The DuckDB fallback depends on `clickhouse_connect.get_client()` failing quickly when the host is unreachable. If the client hangs for a long timeout before failing, run startup will be slow. This should be measured on first run. If it is too slow, the ClickHouse config host should be set to `"invalid-host-that-does-not-exist.local"` instead of `127.0.0.1:1` — DNS failure is typically faster than a TCP refused-connection timeout.

## Rejected Approaches

**Approach**: Patch `DatabaseActor.__init__` with a `force_backend: Literal["clickhouse", "duckdb"] = "auto"` parameter.
**Why rejected**: Requires modifying production code for a test concern. The test concern is better handled in the test layer. The hack of pointing ClickHouse at an invalid address is a well-known test pattern for fallback-path testing, and the existing comment in `database_actor.py:57` ("ClickHouse unavailable at startup. Falling back to DuckDB.") confirms this is the documented fallback path.

**Approach**: Add dedicated DuckDB unit tests (`tests/unit/test_duckdb.py`) that call `DuckDBDatabase` directly in memory without Ray.
**Why rejected**: This does not test the wiring through `DatabaseActor`, `InfrastructureManager`, `CheckpointManager`, and the full simulation loop. These are the places most likely to have bugs in the DuckDB path (e.g., the actor never calling `flush_all_batches` before the DuckDB connection is read by the second Ray process). Unit tests are complementary, not a substitute.

**Approach**: Mirror all three ClickHouse resume tests (003, 004, 005) as DuckDB variants simultaneously.
**Why rejected**: The moving-agent (004) and lane-position (005) tests require `clickhouse-connect` for mid-run polling. The DuckDB equivalents would need a different polling strategy (polling the DuckDB file directly). That is a significant additional scope. Start with the baseline (003-equivalent) and add variants after the baseline passes.

**Approach**: Use the `testcontainers` library with a dummy container to guarantee ClickHouse unavailability.
**Why rejected**: Unnecessary complexity. Pointing ClickHouse at a non-listening port achieves the same effect with zero container overhead.

## Assumptions & Open Questions

1. **ClickHouse connection-failure speed**: It is assumed that `clickhouse_connect.get_client()` with `host="127.0.0.1", port=1` fails quickly (within a few seconds). If it does not, an `invalid-host` DNS name may be faster. Needs to be measured on first test run.

2. **DuckDB file path is deterministic**: The path `<data_dir>/duckdb/<exp_id>.duckdb` is derived from `DuckDBConfig.resolve_db_file()` at `duckdb.py:26` using `home_dir=config.env.data_dir`. The test hardcodes this formula. If `DuckDBConfig.file_name_template` changes, the assertion will fail with a misleading message about a missing file.

3. **Run 1 writes at least one checkpoint**: The test asserts `last_mobility_safe_step > 0`. This requires the crash timeout to be long enough that `CheckpointManager.save_checkpoint()` fires at least once. With 1 agent and a 300-second timeout, this should be achievable, but depends on LLM response latency. If the first LLM call has not completed within 300 seconds, step 0 will be the only checkpoint and it is excluded by design (`base_database.py:429-433`). The timeout may need tuning.

4. **`experiment_info` query uses `updated_at DESC LIMIT 1`**: DuckDB does not have `ReplacingMergeTree` semantics. The `experiment_info` table in DuckDB is an append-only log (same schema, just no deduplication engine). The resume query at `duckdb.py:295-304` already handles this with `ORDER BY updated_at DESC LIMIT 1`. The test's direct query of the file should use the same ordering.

5. **Ray teardown between runs**: The existing tests do `ray.shutdown()` at the end of each `run_with_ray()` call (`utils.py:150`). Between run 1 and run 2, the DuckDB connection held inside the Ray actor is closed during teardown (`database_actor.py:253-255` → `duckdb.py:250-253`). The file on disk should be readable immediately after. This assumption should be verified on first run.

## Code That Could Be Refactored (informational)

- `agentsociety/database/duckdb.py:96-105` — The filter `if not path.name.endswith(".duckdb.sql")` is labeled "No ClickHouse migration files found" in the warning at line 103, but the glob returns all `.sql` files, not just ClickHouse-specific ones. The warning message is misleading. Low priority.

- `agentsociety/simulation/infrastructuremanager.py:405` — The method is named `_init_clickhouse_actor()` but it initializes the generic `DatabaseActor` which may end up using DuckDB. A rename to `_init_database_actor()` would be more accurate. Low priority.

- `agentsociety/database/database_actor.py:32-74` — There is no `force_backend` parameter. Adding one as an optional `Literal["auto", "clickhouse", "duckdb"] = "auto"` would make explicit-DuckDB testing cleaner and not require the port-1 hack. This is a small, safe addition if it ever becomes desirable.

## Proposed Next Steps

1. Add `duckdb>=1.1.0` to `tests/e2e/pyproject.toml` and run `uv sync` in that directory.
2. Add `apply_duckdb_overrides()`, `build_duckdb_config()`, and `query_duckdb()` to `tests/e2e/utils.py`.
3. Create `tests/e2e/configs/007_resume_with_duckdb.yaml` (copy of `003_resume_single_agent_with_local.yaml`, name changed).
4. Write `tests/e2e/007_resume_with_duckdb.py` following the structure in the Implementation Strategy section above.
5. Run the test once manually to measure ClickHouse connection-failure latency; adjust the host string if it is too slow.
6. Add the new test to `tests/run_e2e_tests.sh`.
7. If the baseline passes, consider adding `008_resume_moving_agent_duckdb.py` as a DuckDB parallel of test 004 (deferred).
