# Fix SQLite "file is not a database" Crash
> Prevent the `sqlite3.DatabaseError: file is not a database` error from crashing the simulation by correctly detecting it in all write paths and recovering or skipping storage gracefully.

## Purpose & Motivation

During long simulations, writes to the SQLite database (particularly to `agent_dialog` via `save_agent_thought`) begin failing with `sqlite3.DatabaseError: file is not a database`. The first failures appear as logged warnings, but eventually an unhandled exception propagates through the agent call chain and kills the entire simulation. This is a data-durability failure that terminates otherwise-healthy runs.

The existing corruption detection code (`_is_sqlite_corruption_error`) was added specifically to handle this case, but it has a type mismatch bug that prevents it from ever firing in write paths.

## Success Criteria

1. `sqlite3.DatabaseError: file is not a database` no longer crashes the simulation.
2. When the error is detected during a write, the simulation logs it and continues (storage becomes degraded but the simulation itself survives).
3. The detection code catches the error whether SQLAlchemy wraps it as `DatabaseError` or `OperationalError`.
4. All write methods in `DatabaseWriter` share the same detection logic; none re-implements it differently.
5. The existing `_create_tables` recovery path (rename + retry) is preserved and not regressed.

## Scope

**In scope:**
- Fix the type check in `_is_sqlite_corruption_error` to match `sqlalchemy.exc.DatabaseError` (not just `OperationalError`).
- Add corruption detection and soft-failure handling to all write methods in `DatabaseWriter` (`write_dialogs`, `write_statuses`, `write_surveys`, `write_global_prompt`, `write_profiles`, `write_task_result`, `log_metric`, `update_exp_info`).
- Prevent the write-path exception from propagating out of `save_agent_thought` and crashing `run_all_agents`.

**Out of scope:**
- Read methods (`read_dialogs`, `read_statuses`, etc.) — these are not on the crash path.
- PostgreSQL path — this bug is SQLite-specific.
- Full database reconnection / self-heal at write time — the file cannot be recovered in-process once an async engine has been poisoned by a corrupt file. A soft-skip with logging is the correct runtime behaviour.
- Changing when or whether the database file is renamed (the `_rename_corrupt_sqlite` logic is correct for `init` time).

## Constraints

- The simulation must not be stopped or its state corrupted when storage is skipped.
- The fix must not regress the lock-retry logic for `SQLITE_BUSY` (`_is_sqlite_lock_error`).
- The fix must not affect the PostgreSQL code path.
- No new dependencies.

## Architecture & Integration Points

The crash call chain is:

```
societyagent.py:422  forward()
  → agent.py:554     save_agent_thought()
      → database.py:800  DatabaseWriter.write_dialogs()   [raises uncaught]
          ← propagates through
agentmanager.py:621  asyncio.gather(*tasks)               [re-raises first exception]
simulationengine.py:767  step()                           [re-raises as RuntimeError]
```

Key file anchors:

- `agentsociety/storage/database.py:105-126` — `_is_sqlite_corruption_error()` (module-level): the detection function that is broken. Checks `isinstance(error, OperationalError)` but the actual exception is `sqlalchemy.exc.DatabaseError`.
- `agentsociety/storage/database.py:268-274` — `DatabaseWriter._is_sqlite_corruption_error()` (instance method): a second, identical copy of the broken detection code, redundantly duplicated on the class.
- `agentsociety/storage/database.py:778-808` — `DatabaseWriter.write_dialogs()`: the first write method on the direct crash path. It `raise`s on all exceptions without distinguishing corruption.
- `agentsociety/storage/database.py:810-842` — `DatabaseWriter.write_statuses()`: same pattern.
- `agentsociety/storage/database.py:959-991` — `DatabaseWriter.log_metric()`: same pattern.
- `agentsociety/storage/database.py:993-1062` — `DatabaseWriter.update_exp_info()`: same pattern.
- `agentsociety/storage/database.py:212` — `DatabaseWriter.__init__`: assigns `self._sqlite_path = Path(home_dir) / "sqlite.db"`.
- `agentsociety/agent/agent.py:529-554` — `save_agent_thought()`: calls `write_dialogs` with no error handling.
- `agentsociety/simulation/agentmanager.py:620-621` — `run_all_agents()`: `asyncio.gather(*tasks, return_exceptions=False)` (the default), so the first raised exception terminates the gather.
- `agentsociety/simulation/simulationengine.py:767` — `step()`: calls `run_all_agents()`, re-raises as `RuntimeError` at line 942.

## Root Cause: The Type Mismatch

The key finding (verified by testing against aiosqlite 0.x + SQLAlchemy 2.x):

When a file at the SQLite path is not a valid database, the aiosqlite driver raises `sqlite3.DatabaseError` directly (not `sqlite3.OperationalError`). SQLAlchemy wraps this as `sqlalchemy.exc.DatabaseError`. The existing check at `database.py:115` is:

```python
if not isinstance(error, OperationalError):   # OperationalError = sqlalchemy.exc.OperationalError
    return False
```

`sqlalchemy.exc.OperationalError` is a **subclass** of `sqlalchemy.exc.DatabaseError`, but `sqlalchemy.exc.DatabaseError` is **not** a subclass of `sqlalchemy.exc.OperationalError`. When the error arrives as `sqlalchemy.exc.DatabaseError`, the `isinstance` check returns `False` and the function returns `False`. The corruption is therefore never detected in write paths.

Why the error is intermittent: SQLite with WAL mode (`PRAGMA journal_mode=WAL`, set at `database.py:95`) creates `-wal` and `-shm` sidecar files. If the main `.db` file is damaged or replaced (e.g., mid-write failure, filesystem issue, or by an external process writing the checkpoint/resume data directory), subsequent connections may succeed for a time using WAL recovery before hitting the corrupt header. This explains why earlier writes to other tables succeed before `agent_dialog` writes start failing.

## Similar Patterns & Reuse

- **`DatabaseWriter._is_sqlite_lock_error()`** at `database.py:260-266`: This is the pattern to follow. It checks `isinstance(error, OperationalError)` and then does a string match. The corruption detector should mirror this structure but check against `sqlalchemy.exc.DatabaseError` (not `OperationalError`), since that is the actual supertype the driver uses.
- **`fetch_pending_dialogs` lock retry** at `database.py:1074-1098`: Demonstrates a clean retry loop with per-error-type branching. Write methods should use the same branching pattern but with a "skip and warn" action instead of retry.
- **Module-level `_is_sqlite_corruption_error`** at `database.py:105-126`: Used only by `_create_tables`. Fix it too for correctness, but the main impact is on the instance method copy.

## Implementation Strategy

### Step 1: Fix the type check in both copies of `_is_sqlite_corruption_error`

**Before** (`database.py:115`):
```python
if not isinstance(error, OperationalError):
    return False
```

**After**: Change to accept either `OperationalError` or `DatabaseError`. `DatabaseError` is the correct supertype:
```python
from sqlalchemy.exc import OperationalError, DatabaseError as SADatabaseError
...
if not isinstance(error, (OperationalError, SADatabaseError)):
    return False
```

This applies to both the module-level function at line 105 and the instance method at line 268. The import for `DatabaseError` needs to be added alongside the existing `OperationalError` import at `database.py:8`.

### Step 2: Add soft-failure handling to write methods

All `@lock_decorator`-wrapped write methods share this pattern:

```python
except Exception as e:
    await session.rollback()
    get_logger().error(f"Error writing <X> to {self._config.db_type}: {e}")
    raise
```

For SQLite-only, add a branch before `raise`:

```python
except Exception as e:
    await session.rollback()
    if self._is_sqlite_corruption_error(e, self._config):
        get_logger().warning(
            f"SQLite file appears corrupt or invalid; skipping <X> write: {e}"
        )
        return   # soft-skip: simulation continues
    get_logger().error(f"Error writing <X> to {self._config.db_type}: {e}")
    raise
```

This applies to all 8 write methods:
- `write_dialogs` (`database.py:778`)
- `write_statuses` (`database.py:810`)
- `write_profiles` (`database.py:844`)
- `write_surveys` (`database.py:872`)
- `write_global_prompt` (`database.py:903`)
- `write_task_result` (`database.py:928`)
- `log_metric` (`database.py:959`)
- `update_exp_info` (`database.py:993`)

The important one for the crash path is `write_dialogs`, since that is what `save_agent_thought` calls. But all write methods should be hardened for consistency.

### Step 3: Confirm `save_agent_thought` does not need its own try/except

With Step 2 in place, `DatabaseWriter.write_dialogs()` will swallow the corruption error and return normally. `save_agent_thought` at `agent.py:553-554` calls `write_dialogs` but does not need its own try/except, because the corruption is now handled at the storage layer.

No changes are needed to `agent.py` or `agentmanager.py`.

### Ordering

Steps 1 and 2 can be done together in a single commit as they touch only `database.py`.

## Trade-Offs

| What is gained | What is sacrificed |
|---|---|
| Simulation survives SQLite file corruption mid-run | Agent thoughts and dialogs are silently lost after the corrupt state begins |
| Consistent error classification in `_is_sqlite_corruption_error` | No active recovery at write time (once the engine is poisoned, no writes to that connection will succeed) |
| Write path protection for all 8 methods | Operator may not notice the database is degraded without monitoring the warning log |

The trade-off of silent data loss is acceptable because: (a) the corruption is already logged as a warning, (b) the alternative is a full simulation crash which loses all future data, and (c) the corruption is a pre-existing filesystem-level problem that cannot be resolved in-process.

## Rejected Approaches

**Approach: Reconnect / re-initialize the engine mid-simulation on corruption**
Why rejected: The `DatabaseWriter` is shared across all agents via the `AgentToolbox`. Re-initializing the engine in the middle of a simulation run would require coordinating across all concurrently-executing agents, disposing the old connection pool (while other agents may be mid-transaction), and recreating tables that may or may not exist. The `_create_tables` function also does `DROP TABLE IF EXISTS` before creating, which would destroy any data written so far. This is more complex and risky than a soft-skip and does not provide a meaningfully better outcome.

**Approach: Catch `sqlite3.DatabaseError` directly (unwrap the SQLAlchemy wrapper)**
Why rejected: Relying on the raw `sqlite3` exception requires inspecting the `orig` attribute of `sqlalchemy.exc.DBAPIError`, which is an implementation detail. Using `isinstance(error, SADatabaseError)` is the correct, public-API approach.

**Approach: Wrap `save_agent_thought` in a try/except instead of fixing the write method**
Why rejected: This would be a band-aid on one call site. There are multiple places in `agent.py` that call `database_writer.write_dialogs` and other write methods (e.g. `_handle_agent_chat_with_storage` at line 567, `_handle_interview_with_storage` at line 488). Fixing the write method itself is the durable, single-point fix.

**Approach: Use `return_exceptions=True` in `asyncio.gather` inside `run_all_agents`**
Why rejected: This would suppress exceptions from _all_ agent failures, not just storage ones. Storage writes are non-critical data recording operations; actual agent logic failures (LLM errors, invalid state, etc.) should still propagate and be visible.

## Assumptions & Open Questions

1. **Why does the file become invalid mid-simulation?** The root cause of how `sqlite.db` becomes an invalid database file is not identified. Candidates include: (a) an external process writing to the same `home_dir` path, (b) a filesystem-level fault (RAID write error on the test machine), (c) a WAL checkpoint race when the simulation crashes and restarts. This plan fixes the handling of the symptom. Investigating the root cause is a separate concern.

2. **Is the `_create_tables` DROP TABLE safe during resume?** `_create_tables` at `database.py:168` does `DROP TABLE IF EXISTS` unconditionally. This means calling `DatabaseWriter.init()` on a resume (with the same `exp_id`) would drop all previously-written tables. However, the simulation uses a fresh `exp_id` for each run (line 71 of `simulationengine.py` generates a new UUID unless `env.exp_id` is set), so this is not the source of the current bug. But it is a latent hazard for the resume workflow and should be noted.

3. **Can the `_engine` be marked "dead" to fail fast on future writes?** A `_db_corrupted: bool` flag on `DatabaseWriter` could be set on first corruption detection, causing all subsequent write calls to skip immediately without touching the engine. This avoids repeated error logs and pool contention. This is not required for correctness but would be a cleaner production behavior.

## Code That Could Be Refactored *(informational)*

- `database.py:105-126` and `database.py:268-274` — `_is_sqlite_corruption_error` exists as both a module-level function (used only in `_create_tables`) and an instance method. They are identical. The instance method could delegate to the module-level one, or both could be replaced by a single utility. Not a blocker.

- `database.py:168` — `DROP TABLE IF EXISTS` in `_create_tables` makes it non-idempotent for resume scenarios. If the same `exp_id` is reused (i.e., `env.exp_id` is set), this silently deletes all experiment data. A `CREATE TABLE IF NOT EXISTS` (removing the DROP) would be safer, but requires testing that the schema hasn't changed.

- `agentmanager.py:620-621` — `asyncio.gather(*tasks)` with default `return_exceptions=False` means one agent crashing stops all others at their next `await`. For robustness, individual agent errors could be caught inside `agent_base.run()` with `return_exceptions=True` in gather. Not in scope for this fix.

## Proposed Next Steps

1. **Fix `_is_sqlite_corruption_error` type check** in `database.py` at lines 115 and 271: change `isinstance(error, OperationalError)` to `isinstance(error, (OperationalError, SADatabaseError))` and add `DatabaseError` to the import at line 7.

2. **Add soft-skip in all write method exception handlers**: in all 8 `@lock_decorator` write methods, add `if self._is_sqlite_corruption_error(e, self._config): get_logger().warning(...); return` before the `raise`.

3. **Optionally add a `_db_corrupted` flag** to `DatabaseWriter` to fail-fast on subsequent writes after corruption is first detected, avoiding repeated pool contention and log noise.

4. **Test** by running `sh tests/run_e2e_tests.sh` and manually verifying by replacing `sqlite.db` with a garbage file mid-simulation and observing that warnings are logged but the simulation continues.
