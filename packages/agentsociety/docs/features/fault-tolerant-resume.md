# Fault-Tolerant Simulation Resume (Step Rollback)
> When resuming a simulation, automatically retry with progressively older checkpoints up to a configurable depth before raising an error.

## Purpose & Motivation

Resuming a simulation restores agent memory, economy simulator state, and mobility positions from a snapshot taken at the last "safe step". Snapshots can be incomplete or corrupt (e.g. a mid-write crash, a partial ClickHouse flush, a missing KV row for one agent). Today, the first sign of trouble — a missing agent row, a corrupted economy file, a failed position reset — raises a hard `RuntimeError` with no fallback, requiring manual intervention or a full restart from scratch.

The goal is to make the resume path self-healing: try the latest checkpoint first, silently fall back to the next-older one, and so on, up to N steps back. This directly addresses scenarios that have already appeared (see: `fix: resume not working with moving agents`, `fix: errors in duckdb conversion`).

## Success Criteria

- When the latest checkpoint is invalid (incomplete KV data, corrupt economy file, failed mobility restore), the engine automatically tries the previous checkpoint without raising to the caller.
- The number of fallback attempts is bounded by a configurable `resume_rollback_depth` parameter (default: 10).
- Each failed attempt is logged at WARNING level with the step number and reason, so operators know how many steps were lost.
- If all N attempts fail, the original error from the first (latest) attempt is re-raised, preserving the current error contract.
- The behavior for experiments with no checkpoint at all (step 0 / fresh start) is unchanged.

## Scope

**In scope:**
- Extend `_fetch_checkpoint_snapshots()` in `clickhouse.py` and `duckdb.py` to query and attempt all available checkpoint steps (descending), not just `[last, prev]`.
- Add `resume_rollback_depth: int` to `EnvConfig` with a default of 10.
- Pass the depth parameter through `InfrastructureManager.load_resume_state()` → `fetch_resume_data()` → `_fetch_checkpoint_snapshots()`.
- Extend the economy file path inference to derive `econ_step_{N}.bin` for any step N, since the filesystem path pattern is deterministic.
- Log a WARNING for each failed attempt and an INFO summary when a fallback succeeds.
- The rollback is purely at data-query time (before any agent is initialized), so no partial-initialization teardown is needed.

**Out of scope:**
- Rollback of already-initialized agents or live in-memory state (this runs during `init()`, before agents are running).
- Retry logic inside `_restore_external_simulator_state()` once a snapshot has been selected (that function gets cleaner data, not a retry loop itself).
- Rollback across different source experiment IDs.
- Any change to how checkpoints are written.

## Constraints

- Both database backends (ClickHouse, DuckDB) must implement the same fallback query.
- The economy checkpoint files (`econ_step_{N}.bin`) are on the local filesystem. Deep rollback requires those files to exist; the code must handle a missing file gracefully and continue to the next candidate step.
- The `resume_rollback_depth` parameter must be a non-negative integer; depth=0 means "no rollback, fail immediately on the first bad step" (current behavior).
- The change must not touch the checkpoint-write path or the existing `prev_mobility_safe_step` column — those remain as-is.

## Architecture & Integration Points

The resume pipeline is a linear sequence during `SimulationEngine.init()`:

```
SimulationEngine.init()                          simulationengine.py:622
  └─ InfrastructureManager.load_resume_state()   infrastructuremanager.py:205
       └─ DatabaseActor.fetch_resume_data.remote()  database_actor.py:220
            └─ ClickHouseDatabase.fetch_resume_data() OR DuckDBDatabase.fetch_resume_data()
                 └─ _fetch_checkpoint_snapshots()   clickhouse.py:744 / duckdb.py:757
  └─ _restore_resume_runtime_state()             simulationengine.py:173
  └─ AgentManager.initialize_agents(resume_state)  simulationengine.py:657
  └─ _restore_external_simulator_state()         simulationengine.py:212
  └─ _restore_messager_state()                   simulationengine.py:546
```

Specific integration points:

- `agentsociety/configs/env.py:43` — `EnvConfig` Pydantic model where `resume_rollback_depth: int = Field(default=10)` will be added.
- `agentsociety/simulation/infrastructuremanager.py:205` — `load_resume_state()` reads `self._config.env.resume_rollback_depth` and passes it to `fetch_resume_data`.
- `agentsociety/database/database_actor.py:220` — `fetch_resume_data(source_exp_id)` gains a `rollback_depth: int = 10` parameter, forwarded to `self._db.fetch_resume_data()`.
- `agentsociety/database/clickhouse.py:628` — `ClickHouseDatabase.fetch_resume_data()` gains `rollback_depth` parameter, passed to `_fetch_checkpoint_snapshots()`.
- `agentsociety/database/clickhouse.py:744` — `_fetch_checkpoint_snapshots()` currently iterates `[resume_step, prev_step]` — this becomes the main change site. It will query all available snapshot steps and iterate up to `rollback_depth` candidates.
- `agentsociety/database/duckdb.py:646` — `DuckDBDatabase.fetch_resume_data()` — same change as ClickHouse.
- `agentsociety/database/duckdb.py:757` — `DuckDBDatabase._fetch_checkpoint_snapshots()` — same change as ClickHouse.

Economy checkpoint paths are derived deterministically from:
```
{home_dir}/checkpoints/{exp_id}/econ_step_{step}.bin
```
This pattern is established at `simulationengine.py:1197-1199`. Since the path is deterministic, deeper rollback does not require querying the DB for the economy path — it can be inferred from the step number. The `economy_checkpoint_path` returned in `resume_data` will need to reflect the successfully selected step, not just the latest.

## Similar Patterns & Reuse

- **What it is**: `clickhouse.py:744 — _fetch_checkpoint_snapshots(escaped_exp_id, resume_step, prev_step, expected_agent_ids)`
  **What it does**: Tries exactly two hardcoded step candidates (`[resume_step, prev_step]`), checking KV integrity for each.
  **How this feature uses it**: The inner loop body (query, integrity check, grouping, return) is already correct. The change is to replace the hardcoded two-element candidate list with a dynamically-queried N-element list.

- **What it is**: `duckdb.py:757 — _fetch_checkpoint_snapshots(source_exp_id, resume_step, prev_step, expected_agent_ids)`
  **What it does**: Identical logic to the ClickHouse version, parameterized for DuckDB.
  **How this feature uses it**: Same change applies here; the two implementations are kept in sync.

- **What it is**: `infrastructuremanager.py:205 — load_resume_state()`
  **What it does**: Calls `self._db_actor.fetch_resume_data.remote(self._resume_exp_id)` and stores the result as `self._resume_state`.
  **How this feature uses it**: The depth parameter threads through here without requiring structural changes — just a pass-through of the config value.

## Implementation Strategy

### Step 1 — Add `resume_rollback_depth` to `EnvConfig`

**Before**: `agentsociety/configs/env.py:43` — `EnvConfig` has no rollback depth field.

**After**: Add `resume_rollback_depth: int = Field(default=10, ge=0)` to `EnvConfig`. This makes the parameter configurable via YAML config files without any other change to the config loading path (`load_config_from_file` uses Pydantic validation automatically).

### Step 2 — Add depth query to `_fetch_checkpoint_snapshots()` (ClickHouse)

**Before**: `clickhouse.py:752` — the candidate list is built as `[resume_step, prev_step]`, a hardcoded two-element sequence from `experiment_info` columns only.

**After**: Replace the hardcoded candidate list with a query that discovers all steps with KV snapshot data, sorted descending, capped at `rollback_depth`. New signature:

```python
def _fetch_checkpoint_snapshots(
    self,
    escaped_exp_id: str,
    resume_step: int,
    rollback_depth: int,
    expected_agent_ids: set[int],
    home_dir: str,       # needed to derive economy file path
    exp_id_raw: str,     # raw (unescaped) UUID for file path
) -> tuple[int, dict[int, list], dict[int, list], dict[int, list], list[dict], str]:
```

The candidate steps are collected as:
```sql
SELECT DISTINCT simulation_step FROM agent_kv_snapshot
WHERE exp_id = '{escaped_exp_id}' AND simulation_step <= {resume_step}
ORDER BY simulation_step DESC
LIMIT {rollback_depth}
```

This naturally includes `resume_step` as the first candidate. For each candidate:
1. Run the existing KV integrity check (all expected agents present).
2. If KV is complete, derive the economy file path as `{home_dir}/checkpoints/{exp_id_raw}/econ_step_{step}.bin` and verify it exists on disk with `os.path.isfile()`.
3. If economy file is missing, log a WARNING and continue to next candidate.
4. If both checks pass, load stream/spatial/messages for that step and return, now including the economy path as a 6th return value.

The WARNING log for each failure must include: step number attempted, reason (KV incomplete / economy file missing), and remaining candidates.

### Step 3 — Mirror the change in DuckDB

**Before**: `duckdb.py:764` — same hardcoded `[resume_step, prev_step]` pattern.

**After**: Same structural change as Step 2. The query uses `?` placeholders instead of f-string interpolation:
```sql
SELECT DISTINCT simulation_step FROM agent_kv_snapshot
WHERE exp_id = ? AND simulation_step <= ?
ORDER BY simulation_step DESC
LIMIT ?
```

### Step 4 — Thread `rollback_depth` and `home_dir` through the call chain

**Before**:
- `fetch_resume_data(source_exp_id: str)` at `clickhouse.py:628` and `duckdb.py:646`
- `DatabaseActor.fetch_resume_data(source_exp_id: str)` at `database_actor.py:220`
- `load_resume_state()` at `infrastructuremanager.py:205`

**After**: Each function gains `rollback_depth: int = 10` and (for the DB classes) `home_dir: str` parameters. `load_resume_state()` reads `self._config.env.resume_rollback_depth` and `self._config.env.home_dir` and passes them down. The returned `resume_data` dict now includes `"economy_checkpoint_path"` set to the path from the selected checkpoint step (replacing the old pattern of always taking it from `experiment_info`).

### Step 5 — Re-raise original error after all attempts exhausted

**Before**: `_fetch_checkpoint_snapshots()` returns `(-1, {}, {}, {}, [])` silently when no valid step is found (`clickhouse.py:806`, `duckdb.py:840`).

**After**: Capture the failure reason from the first (latest) attempt. After exhausting all candidates, the caller (`fetch_resume_data`) raises with the original failure message, not a generic "no checkpoint found" message. This preserves the current error contract expected by `load_resume_state()` callers.

No changes are needed to `_restore_external_simulator_state()` (`simulationengine.py:212`) — it already uses `self._resume_state["economy_checkpoint_path"]` and `self._resume_state["last_mobility_safe_step"]`, which will now reflect the successfully selected rollback step.

## Trade-Offs

**Gained:**
- Simulation resumes survive single or multiple corrupt/incomplete checkpoints automatically.
- Operators get clear log output showing exactly how many steps were rolled back and why.
- No change to the write path or checkpoint cadence.

**Sacrificed / Risked:**
- Deeper rollback means more simulation time is re-run. If N=10 and steps are 5 minutes apart, the simulation re-executes up to ~50 minutes of wall-clock simulation time. This is expected and acceptable — the alternative is a failed resume.
- The economy file existence check adds up to N filesystem `stat()` calls during init (negligible cost).
- The new `DISTINCT simulation_step` query scans the `agent_kv_snapshot` table. On ClickHouse this is indexed by `(exp_id, simulation_step, agent_id, key)` (`migrations/0009`), so the DISTINCT scan is efficient. On DuckDB (local dev), the table is small anyway.
- The `prev_mobility_safe_step` column in `experiment_info` becomes redundant once the new query is in place, but removing it would be a schema migration with no immediate payoff. It is left in place for now.

## Rejected Approaches

**Approach**: Keep `prev_mobility_safe_step` and add more "prev_prev", "prev_prev_prev" columns to `experiment_info` to store N historical steps.
**Why rejected**: Schema churn for each N increment. The step history is already fully stored in `agent_kv_snapshot` — a `DISTINCT simulation_step` query is the correct and scalable way to enumerate it without schema changes.

**Approach**: Add rollback logic to `_restore_external_simulator_state()` in `simulationengine.py` instead of to the DB layer.
**Why rejected**: By the time `_restore_external_simulator_state()` runs, agents have already been initialized with the (corrupt) memory snapshot (`simulationengine.py:657`). Rolling back at that point would require tearing down and re-initializing the agent manager — a far larger and riskier change. The DB layer is the correct place because the snapshot selection happens before any downstream initialization.

**Approach**: Always retry at the DB actor level by catching exceptions from `load_resume_state()` and calling it again with a decremented step.
**Why rejected**: `load_resume_state()` does multiple things (config validation, agent count check, metadata loading) before snapshot selection. Re-calling the full function for each rollback attempt would repeat expensive and side-effecting steps. Keeping the retry inside `_fetch_checkpoint_snapshots()` is surgical.

**Approach**: Expose `resume_rollback_depth` on `ExpConfig` instead of `EnvConfig`.
**Why rejected**: `ExpConfig` (`configs/exp.py`) models the experiment workflow — what happens during the run. Resume behavior is operational/infrastructure concern, consistent with other resume-related fields like `exp_id` which already live on `EnvConfig` (`configs/env.py:58`).

## Assumptions & Open Questions

- **Economy file co-location**: Economy checkpoint files (`econ_step_{N}.bin`) are written to the local filesystem at `{home_dir}/checkpoints/{exp_id}/`. This plan assumes the files for older steps still exist on disk (they are never deleted by the current code). If an operator has manually pruned them, the fallback for those steps will fail the economy-file check and continue to older steps. This is the correct behavior.

- **Step numbering**: A "step" is `self._total_steps` at write time (`simulationengine.py:1101`), incremented at `simulationengine.py:1438`. Checkpoints are written every step at `simulationengine.py:1348`. The `simulation_step` column in `agent_kv_snapshot` uses this same integer. This plan treats step numbers as the primary rollback key.

- **What "failure" means for KV completeness**: The existing integrity check (`expected_agent_ids.issubset(kv_agent_ids)`) only checks agent presence, not per-key completeness. This plan reuses the same check — a more granular validation (e.g. required keys per agent) is out of scope.

- **Default of 10**: The user specified "10 or 20". This plan uses 10. If checkpoints are written every step and a typical step is 5 minutes of simulation time, 10 steps represents ~50 minutes rolled back. This is conservative enough to handle crash scenarios without silently losing large amounts of simulation progress.

- **Ray remote call signature**: `DatabaseActor.fetch_resume_data.remote(source_exp_id)` is called via Ray. Adding keyword arguments with defaults to Ray remote methods works as standard Python, but the call site at `infrastructuremanager.py:213` must be updated to pass the new parameters explicitly.

## Code That Could Be Refactored *(informational)*

- `clickhouse.py:744` and `duckdb.py:757` — `_fetch_checkpoint_snapshots()` is duplicated across both backends with nearly identical logic. A shared base class or mixin could eliminate this duplication. Not a blocker for this feature, but the new rollback loop will be duplicated in both, making the case for consolidation stronger.

- `simulationengine.py:1202` — `getattr(self, "_last_mobility_safe_step", -1)` uses a dynamic attribute that is never declared in `__init__`. It should be declared as `self._last_mobility_safe_step: int = -1` in `__init__` for clarity.

- `infrastructuremanager.py:205` — `load_resume_state()` is a long method that mixes config validation, agent count validation, and snapshot fetching. Splitting these into sub-methods would make the rollback thread-through cleaner.

## Proposed Next Steps

1. Add `resume_rollback_depth: int = Field(default=10, ge=0)` to `EnvConfig` at `agentsociety/configs/env.py:43`.

2. Change `_fetch_checkpoint_snapshots()` signature and inner loop in `agentsociety/database/clickhouse.py:744` to query available steps via `DISTINCT simulation_step ... ORDER BY simulation_step DESC LIMIT rollback_depth`, check economy file existence per attempt, and capture the first-attempt error for re-raise.

3. Mirror the same change in `agentsociety/database/duckdb.py:757`.

4. Update `ClickHouseDatabase.fetch_resume_data()` at `clickhouse.py:628` and `DuckDBDatabase.fetch_resume_data()` at `duckdb.py:646` to accept and forward `rollback_depth` and `home_dir`, and to update `economy_checkpoint_path` in the returned dict with the path from the selected step.

5. Update `DatabaseActor.fetch_resume_data()` at `database_actor.py:220` to accept and forward `rollback_depth` and `home_dir`.

6. Update `InfrastructureManager.load_resume_state()` at `infrastructuremanager.py:205` to read `self._config.env.resume_rollback_depth` and `self._config.env.home_dir` and pass them to the Ray remote call.

7. Validate with an example script from `/mnt/raid5/gustavo/citysim/examples/` by running a simulation to step N, artificially corrupting the KV snapshot at step N in the database, and confirming resume succeeds from step N-1.
