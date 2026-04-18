# Robust Resume Recovery
> Harden the two resume failure modes — configuration mismatch detection and SQLite file corruption — so that transient environmental differences and stale database files do not abort an otherwise valid resume.

## Purpose & Motivation

Two failure modes are observed in production when attempting to resume a simulation:

1. A `ValueError` raised at `infrastructuremanager.py:275-279` with message "Configuration mismatch with resume experiment" aborts the resume even when the semantic intent of the configurations is identical but the serialized YAML differs in inconsequential ways (e.g., `home_dir` changed between runs, new optional fields appeared in `EnvConfig`, or LLM routing entries differ in field ordering after YAML round-trip).

2. A `sqlite3.DatabaseError: file is not a database` propagates up through `database.py:111-113` during `_create_tables()` when the SQLite file at `home_dir/sqlite.db` exists but is corrupted — e.g., from a previous crash mid-write, a partial download, or a zero-byte file created by the OS before a prior run completed initialization.

Both failures happen before any simulation work begins, meaning the resume is abandoned entirely for recoverable root causes. Making recovery more robust without introducing new abstractions is the right scope here.

## Success Criteria

1. When `_normalize_resume_config` produces a mismatch, the engine logs a structured diff of exactly which keys differ, rather than a bare "mismatch" string. An operator can immediately see whether the difference is meaningful.
2. A new config field `env.resume_config_mismatch_action` (default `"error"`) supports a second value `"warn"`, allowing operators to force-resume despite a config diff by accepting the risk.
3. When SQLite initialization encounters `sqlite3.DatabaseError` (or the SQLAlchemy equivalent `OperationalError` with "not a database" / "file is not a database" in the message), the writer renames the corrupted file (not deletes — preserves forensic value), creates a fresh file, and retries table creation once. If the retry also fails, the original error propagates.
4. No behavior changes when neither failure mode is triggered. All existing e2e tests pass.

## Scope

**In scope:**
- `infrastructuremanager.py` — extend `load_resume_state()` to log a diff and respect the new mismatch action config.
- `storage/database.py` — extend `_create_tables()` to detect SQLite corruption and recover by rename + retry.
- `configs/env.py` — add `resume_config_mismatch_action: Literal["error", "warn"] = "error"`.
- `_normalize_resume_config` — strip `home_dir` from the comparison (currently not stripped, but `home_dir` legitimately changes when a user moves their data directory between runs).

**Out of scope:**
- Changing how checkpoints are written.
- Changing the DuckDB backend.
- Adding new metrics or observability for these failure paths.
- PostgreSQL corruption recovery (corruption there requires DBA intervention; SQLite is the only path where rename-and-retry is safe at the application level).
- Automatic migration of old SQLite data into the fresh file.

## Constraints

- The `resume_config_mismatch_action` field must default to `"error"` so existing behavior is preserved for all current users.
- SQLite rename must use a timestamped suffix (e.g., `sqlite.db.corrupt.20260418T103012`) to avoid collision if the file is renamed multiple times.
- The retry must be a single attempt, not a loop. Retrying more than once masks a systematic problem.
- `_normalize_resume_config` changes must not broaden the normalization so far that legitimately incompatible configs (e.g., different agent counts) pass through undetected.
- No new Ray actors, no new base classes.

## Architecture & Integration Points

### Failure Mode 1: Configuration mismatch

Call chain for this failure:

```
SimulationEngine.init (simulationengine.py:222)
  → InfrastructureManager.initialize_all (infrastructuremanager.py:506)
      → _init_database_writer_if_enabled (infrastructuremanager.py:311)
  → InfrastructureManager.load_resume_state (infrastructuremanager.py:236)
      → db_actor.fetch_resume_data.remote (infrastructuremanager.py:255)
      → _normalize_resume_config(source_config) (infrastructuremanager.py:273)
      → _normalize_resume_config(current_config) (infrastructuremanager.py:274)
      → raise ValueError if source_config != current_config (infrastructuremanager.py:275-279)
```

Key code points:

- `infrastructuremanager.py:89-104` — `yaml_config` is built with `model_dump(exclude_defaults=True, exclude_none=True)`. The `exclude_defaults=True` flag means fields that were added to `EnvConfig` with new defaults after the original experiment was recorded will appear in the current config's YAML but not in the stored config. This is a systematic source of false-positive mismatches.
- `infrastructuremanager.py:175-183` — `_normalize_resume_config` strips `exp_id`, `db`, `clickhouse`, `s3`, `logging_level`, `monitoring_enabled`, `data_dir` from `env`. It does **not** strip `home_dir`. A user who moves their data directory between runs gets a spurious mismatch on `env.home_dir`.
- `infrastructuremanager.py:275-279` — The `raise ValueError` gives no indication of which key(s) differ.

### Failure Mode 2: SQLite corruption

Call chain:

```
SimulationEngine.init (simulationengine.py:222)
  → InfrastructureManager.initialize_all (infrastructuremanager.py:506)
      → _init_database_writer_if_enabled (infrastructuremanager.py:311)
          → DatabaseWriter.__init__ (database.py:144)
              (constructs engine, does not yet touch file)
          → DatabaseWriter.init() (database.py:170)
              → _create_tables() (database.py:193)
                  → _create_tables(exp_id, config, sqlite_path) (database.py:106)
                      → engine.begin() as conn (database.py:111)
                          → sqlite3.DatabaseError: file is not a database
```

Key code points:

- `database.py:158` — `self._sqlite_path = Path(home_dir) / "sqlite.db"`. This is a shared file across all experiments. When the file is corrupt, **every** `DatabaseWriter.init()` call will fail until the file is replaced.
- `database.py:106-141` — `_create_tables()` is a module-level function called by `DatabaseWriter._create_tables()` at line 195. The error from `engine.begin()` propagates uncaught through the `async with` block and then through the `finally: await engine.dispose()` call. There is no corruption-detection guard.
- `database.py:82-101` — `_create_async_engine_from_config()` registers `PRAGMA journal_mode=WAL` on the `connect` event. SQLite raises `sqlite3.DatabaseError` when `PRAGMA` is executed against a non-database file. aiosqlite wraps this as an `sqlalchemy.exc.OperationalError` with an error message containing "file is not a database".
- `infrastructuremanager.py:321` — `await self._database_writer.init()` is called with no exception handling beyond the top-level `try/except` in `SimulationEngine.init()` at `simulationengine.py:222`. Any exception here aborts the entire initialization.

## Similar Patterns & Reuse

- **`_is_sqlite_lock_error` — `database.py:206-212`**: `DatabaseWriter` already has a helper that inspects `OperationalError` message strings to classify SQLite errors. The corruption detection for failure mode 2 follows the same pattern: inspect `str(error).lower()` for `"file is not a database"` or `"not a database"` inside an `OperationalError`.

- **`_build_economy_checkpoint_candidates` — `checkpointmanager.py:34-79`**: Shows the established pattern for recoverable retry logic: try the primary path, on failure collect candidates, iterate. The SQLite rename-and-retry follows the same single-shot retry idiom used throughout this codebase.

- **Warning-vs-error branching in `_validate_resume_agent_count` — `infrastructuremanager.py:190-234`**: The agent count check already differentiates between a `warning` (old snapshot, backward-compat path) and a `raise` (genuine mismatch). The same conditional pattern fits the config mismatch action: inspect `self._config.env.resume_config_mismatch_action` and either `raise` or `get_logger().warning(...)`.

## Implementation Strategy

### Step 1: Add `resume_config_mismatch_action` to `EnvConfig`

**Before:** `configs/env.py:59` has `exp_id: Optional[str]` and no mismatch action field.

**After:** Add after `exp_id`:
```python
resume_config_mismatch_action: Literal["error", "warn"] = Field(
    default="error",
    description=(
        "What to do when the current config does not match the source experiment config during resume. "
        "'error' (default) aborts the resume. 'warn' logs the diff and continues."
    ),
)
```
This requires `from typing import Literal` (already imported via pydantic). The `EnvConfig` model is in `configs/env.py`. No validator needed — pydantic enforces the literal.

### Step 2: Strip `home_dir` in `_normalize_resume_config`

**Before:** `infrastructuremanager.py:175-183` — `_normalize_resume_config` pops six env keys but not `home_dir`.

**After:** Add `env_config.pop("home_dir", None)` to the six existing `env_config.pop()` calls. This is a one-line change. Rationale: `home_dir` is a local filesystem path with no bearing on simulation semantics; it changes whenever a user moves their working directory.

### Step 3: Log a structured diff and respect mismatch action

**Before:** `infrastructuremanager.py:275-279`:
```python
if source_config != current_config:
    raise ValueError(
        "Configuration mismatch with resume experiment. "
        "Current configuration fields must match the source experiment config."
    )
```

**After:** Replace with a helper that:
1. Computes `_compute_config_diff(source_config, current_config)` — a pure function that recursively collects `(key_path, source_value, current_value)` triples for keys that differ. Returns a list of strings like `"env.qdrant_cache.enabled: source=False, current=True"`. This does not require a new class — it is a `@staticmethod` on `InfrastructureManager` alongside the existing `_normalize_resume_config` and `_normalize_config_value`.
2. If `diff` is empty, continues normally (no mismatch).
3. If `diff` is non-empty, formats the diff as a multi-line log message.
4. If `self._config.env.resume_config_mismatch_action == "error"`, raises `ValueError` with the diff included in the message.
5. If `"warn"`, calls `get_logger().warning(...)` with the diff and continues.

The `diff` helper touches no existing logic — it reads the already-computed `source_config` and `current_config` dicts.

Integration point: The new code sits entirely within `load_resume_state()` at `infrastructuremanager.py:273-279`, replacing the three lines with approximately eight lines.

### Step 4: SQLite corruption detection and rename-and-retry

**Before:** `database.py:106-141` — `_create_tables()` has no corruption handling. The `async with engine.begin() as conn:` call raises through to the caller.

**After:** Wrap the `engine.begin()` block in a new helper `_is_sqlite_corruption_error(error: Exception) -> bool` that returns `True` when:
- The database type is `sqlite` (checked via `config.db_type`), AND
- The exception is an instance of `sqlalchemy.exc.OperationalError`, AND
- Any of `["file is not a database", "not a database", "unable to open database"]` appear in `str(error).lower()`.

This helper mirrors the existing `DatabaseWriter._is_sqlite_lock_error()` at `database.py:206-212` in structure and should live in the same file for co-location.

The module-level `_create_tables()` function at `database.py:106` gains a corruption-recovery block:

```
try:
    <existing engine.begin() block>
except <OperationalError or Exception> as e:
    if _is_sqlite_corruption_error(e, config):
        _rename_corrupt_sqlite(sqlite_path)   # renames to sqlite.db.corrupt.YYYYMMDDTHHMMSS
        # retry once with a fresh engine
        retry_engine = _create_async_engine_from_config(config, sqlite_path)
        try:
            async with retry_engine.begin() as conn:
                <same table creation block>
        finally:
            await retry_engine.dispose()
    else:
        raise
```

`_rename_corrupt_sqlite(path: Path) -> None` is a module-level function (5 lines) that calls `path.rename(...)` with a timestamp suffix and logs the old and new names. It does not delete the file.

The `finally: await engine.dispose()` in the original must still run on corruption — this is handled by the exception being caught before the `finally` runs in the corrupted-file path, then the `try/finally` on the retry engine handles cleanup of the retry engine.

**Call path after change:**

```
DatabaseWriter.init() (database.py:170)
  → DatabaseWriter._create_tables() (database.py:193)
      → _create_tables(exp_id, config, sqlite_path) (database.py:106)
          → engine.begin() raises OperationalError("file is not a database")
          → _is_sqlite_corruption_error → True
          → _rename_corrupt_sqlite(sqlite_path)  [logs rename]
          → retry with fresh engine
              → engine.begin() succeeds on fresh file
              → tables created normally
```

## Trade-Offs

**Step 2 (strip `home_dir`):** Any config field stripped from comparison reduces the safety guarantee. Stripping `home_dir` is low risk because `home_dir` has no impact on agent behavior. However, if two different experiments were inadvertently given the same `exp_id` with different `home_dir` values pointing to different datasets, the mismatch would no longer be caught. This is an unlikely scenario (exp IDs are UUIDs) and the trade-off is acceptable.

**Step 3 (`warn` mode):** The `"warn"` action lets an operator deliberately resume from a config that changed — e.g., after adding a new LLM provider or changing routing. The operator accepts responsibility for any resulting state inconsistency. The plan does not try to validate whether the specific changed fields are semantically harmless; that is too complex and would require domain knowledge baked into the engine. The structured diff log gives the operator the information they need to make that call.

**Step 4 (rename-and-retry):** Renaming without checking whether the corrupt file contains data from a previous experiment means any data in that file is preserved (good) but not usable without manual intervention. This is the right trade-off: automated deletion of a corrupt file that might contain partial experiment data would be worse. The retry creates a fresh file, which means the current run starts with a clean SQLite state — experiment data from prior runs (if any was in the corrupt file) is not merged. This is consistent with the existing behavior where each new experiment creates its own tables with `DROP TABLE IF EXISTS` at `database.py:133`.

## Rejected Approaches

**Approach: Automatically detect and strip all fields that changed between source and current config**
Why rejected: This would require heuristic knowledge of which fields are "safe" to differ (e.g., `home_dir`, `monitoring_enabled`) vs. semantically significant (e.g., `agents.citizens[0].count`, `exp.environment.start_tick`). The set of safe fields is not stable — it changes as the config schema evolves. The `"warn"` mode with a structured diff gives the operator visibility without the engine making assumptions about field semantics.

**Approach: Delete the corrupt SQLite file instead of renaming it**
Why rejected: The corrupt file may contain partial data from a previous experiment that the user wants to inspect or recover manually. A rename is reversible; a delete is not. The performance cost of renaming vs. deleting is negligible.

**Approach: Suppress the config mismatch check entirely when in `warn` mode**
Why rejected: The check should still run and the diff should still be logged even in `warn` mode. The distinction is only in whether to raise or continue. Suppressing the check would remove useful diagnostic information from the logs.

**Approach: Add a `force_resume: bool` flag to `Config` or `EnvConfig` that skips all resume validation**
Why rejected: A boolean skip is an all-or-nothing escape hatch. The `warn` mode is more surgical — it still logs the diff, still validates agent counts, still checks experiment status. A `force_resume` flag would bypass too much and make debugging harder.

**Approach: Detect SQLite corruption in `_create_async_engine_from_config` rather than in `_create_tables`**
Why rejected: `_create_async_engine_from_config` is a synchronous factory that only constructs the engine object; it does not open the file. The corruption is not detectable at engine-creation time — it only surfaces when the first connection is made inside `engine.begin()`. The detection must happen where the connection is attempted.

**Approach: Use SQLite's `PRAGMA integrity_check` as a pre-flight before `_create_tables`**
Why rejected: `PRAGMA integrity_check` on a non-database file also raises `sqlite3.DatabaseError`, so it provides no benefit over catching the error from the first attempted statement. It adds an extra round-trip with no upside.

## Assumptions & Open Questions

1. **`home_dir` stripping**: It is assumed that `home_dir` is always an operational detail, never a semantic one. If there is a case where two experiments with the same ID legitimately have different data under different `home_dir` values and one should not resume into the other, this assumption is wrong. Validate with the team.

2. **`exclude_defaults=True` in `yaml_config`**: The current YAML serialization at `simulationengine.py:90-104` uses `exclude_defaults=True`. This means if a config field had a default of `False` originally and the user did not set it, it won't appear in the stored YAML. If a new config version changes the default to `True`, the field now appears in the current YAML but not the stored one, causing a spurious mismatch. The `warn` mode addresses the symptom; the root fix would be to use `exclude_defaults=False` when serializing `yaml_config`, but that changes the stored format and is out of scope here. This should be tracked as a separate cleanup.

3. **Multiple writers on the same SQLite file**: The `sqlite.db` path is shared across all experiments within the same `home_dir`. If two simulation runs start simultaneously with the same `home_dir`, both will attempt `DROP TABLE IF EXISTS` and `CREATE TABLE` for their exp-id-prefixed tables. The WAL pragmas and `busy_timeout=30000` at `database.py:96-98` should handle concurrent access, but this has not been tested. The rename-and-retry in the corruption case assumes single-writer access to the file; concurrent rename could corrupt the second writer's view.

4. **PostgreSQL path**: Failure mode 2 is only addressed for SQLite. The `_is_sqlite_corruption_error` guard explicitly checks `config.db_type == "sqlite"`. PostgreSQL connection failures on startup are a different class of problem (network, credentials, schema version) and are out of scope.

## Code That Could Be Refactored *(informational)*

- `infrastructuremanager.py:89-104` — `yaml_config` in `SimulationEngine.__init__` uses `exclude_defaults=True`. This is the root cause of false-positive mismatches from newly-added config fields. Switching to `exclude_defaults=False` with the same exclusions would produce a more stable stored config, but it changes the stored format (stored YAMLs would become larger and denser) and requires the normalization step to become more aggressive about stripping known-irrelevant fields. A separate plan should address this trade-off.

- `database.py:106-141` — `_create_tables()` is a module-level function that creates a throw-away engine, uses it, and disposes it. Meanwhile `DatabaseWriter.__init__` creates a second permanent engine at `database.py:159`. Both engines point at the same file. A single engine lifecycle would be cleaner, but the current pattern predates this work and refactoring it is not a blocker.

- `infrastructuremanager.py:154-188` — `_normalize_resume_config` and `_normalize_config_value` are `@staticmethod` methods but are called only from `load_resume_state`. If a future test wants to verify normalization behavior, it must import `InfrastructureManager` just for the static methods. These could be module-level functions. Not a blocker.

## Proposed Next Steps

1. Add `resume_config_mismatch_action: Literal["error", "warn"] = "error"` to `EnvConfig` at `configs/env.py:59`.

2. In `_normalize_resume_config` at `infrastructuremanager.py:175-183`, add `env_config.pop("home_dir", None)` alongside the existing six pops.

3. Add `_compute_config_diff(a: dict, b: dict, path: str = "") -> list[str]` as a `@staticmethod` on `InfrastructureManager`, after `_normalize_resume_config`. The function recursively walks both dicts and returns a list of human-readable diff lines.

4. Replace the `if source_config != current_config: raise ValueError(...)` block at `infrastructuremanager.py:275-279` with: compute the diff, format it, then branch on `self._config.env.resume_config_mismatch_action`.

5. Add `_is_sqlite_corruption_error(error: Exception, config: DatabaseConfig) -> bool` as a module-level function in `storage/database.py`, after `_is_sqlite_lock_error`-like logic (mirror the existing `DatabaseWriter._is_sqlite_lock_error` pattern at `database.py:206-212`).

6. Add `_rename_corrupt_sqlite(sqlite_path: Path) -> None` as a module-level function in `storage/database.py`.

7. Wrap the `async with engine.begin()` block in `_create_tables()` at `database.py:110-141` with the corruption-detect → rename → retry-once pattern.

8. Run `sh tests/run_e2e_tests.sh` from `packages/agentsociety/` to verify no regressions.
