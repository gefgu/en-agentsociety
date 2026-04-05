# Fault-Tolerant Resume — Economy Checkpoint Check Fix
> Remove the economy file existence gate from checkpoint candidate selection, enforce a minimum resume step of 1, and soften the economy restore error in `simulationengine.py` to a warning.

## Purpose & Motivation

When a simulation is aborted mid-run, the resume path iterates candidate KV snapshots in descending step order and picks the first one that passes all integrity checks. The current code couples two unrelated concerns in that gate: (1) KV completeness (all expected agent IDs present) and (2) economy binary file existence on disk.

The economy binary file check is the wrong gate for two reasons. First, `_restore_external_simulator_state()` in `simulationengine.py` already handles a missing or failed economy load gracefully via `try/except` — the check in the database layer is therefore redundant and stricter than the consumer. Second, in practice the economy `.bin` files may not exist on the machine running the resume (e.g., written to a different node, not yet flushed to shared storage, or the experiment simply never reached a checkpoint-write point). This causes all candidates to be rejected, yielding a `step=-1` resume, which is functionally identical to starting fresh and discards all agent memory.

Additionally, step 0 is the pre-simulation initialization snapshot, not a meaningful resume point. Accepting it as a candidate is semantically wrong and can produce confusing "resumed from step 0" behavior.

Finally, the `RuntimeError` guard in `_restore_external_simulator_state()` that fires when `economy_checkpoint_path` is empty and `latest_step > 0` is too aggressive. If the economy file path is absent, the correct behavior is to warn and let the economy simulator start fresh, not crash the resume.

## Success Criteria

- A simulation that ran steps 1–N, was aborted, and whose economy `.bin` files are missing resumes successfully at the highest valid KV snapshot step (not step -1).
- A simulation that ran steps 1–N resumes at a step >= 1, never at step 0.
- If the economy `.bin` file path is set but the file does not exist, `_restore_external_simulator_state()` logs a WARNING and continues (economy starts fresh). No `RuntimeError` is raised.
- If the economy `.bin` file path is empty and `latest_step > 0`, the same warning-and-continue behavior applies.
- KV completeness remains the sole gate for candidate rejection.

## Scope

**In scope:**
- `agentsociety/database/clickhouse.py` — `_fetch_checkpoint_snapshots()` and `fetch_resume_data()`
- `agentsociety/database/duckdb.py` — `_fetch_checkpoint_snapshots()` and `fetch_resume_data()`
- `agentsociety/simulation/simulationengine.py` — `_restore_external_simulator_state()`

**Out of scope:**
- `database_actor.py` — no changes
- `infrastructuremanager.py` — no changes
- `configs/env.py` — no changes
- KV integrity check logic — keep as-is
- `rollback_depth` machinery — keep as-is
- The schema for `economy_checkpoint_path` in `experiment_info` — no changes; the column continues to be written and read as before

## Constraints

- The fix must be symmetric: both `clickhouse.py` and `duckdb.py` implement `_fetch_checkpoint_snapshots()` independently and must receive identical logical changes.
- No new public API surface; the return type of `_fetch_checkpoint_snapshots()` stays as a 6-tuple.
- The `economy_checkpoint_path` value returned from `_fetch_checkpoint_snapshots()` must always be the derived path for the selected step (even if the file does not exist), so `simulationengine.py` can log it and attempt load.

## Architecture & Integration Points

The resume data flow is a sequential pipeline:

1. `simulationengine.py:_setup_resume()` (~line 155) calls `self._db_actor.fetch_resume_data.remote(source_exp_id, rollback_depth)`.
2. The `DatabaseActor` delegates to either `ClickHouseDatabase.fetch_resume_data()` (`clickhouse.py:227`) or `DuckDBDatabase.fetch_resume_data()` (`duckdb.py:274`).
3. Each `fetch_resume_data()` reads `last_mobility_safe_step` from `experiment_info`, then calls `_fetch_checkpoint_snapshots()` to pick a valid candidate step and load its KV/stream/spatial/message data.
4. The result dict (including `economy_checkpoint_path` and `last_mobility_safe_step`) is stored in `self._resume_state`.
5. `simulationengine.py:_restore_runtime_state()` (~line 185) reads `self._resume_state` and sets `self._total_steps`.
6. `simulationengine.py:_restore_external_simulator_state()` (~line 212) reads `economy_checkpoint_path` from `self._resume_state` and attempts to load the economy binary.

Specific integration points:

- `agentsociety/database/clickhouse.py:356–497` — `_fetch_checkpoint_snapshots()`: candidate discovery query, KV integrity loop, economy file guard (to be removed), success return.
- `agentsociety/database/clickhouse.py:366–368` — `candidate_rows` query at line ~366: `simulation_step <= {resume_step}` (add `AND simulation_step >= 1`).
- `agentsociety/database/clickhouse.py:362` — `has_economy=bool(economy_checkpoint_path)` in the call site inside `fetch_resume_data()` (parameter to be removed).
- `agentsociety/database/duckdb.py:386–507` — `_fetch_checkpoint_snapshots()`: mirrors clickhouse exactly, same structural changes required.
- `agentsociety/database/duckdb.py:361–368` — call site in `fetch_resume_data()`, same `has_economy=` argument to be removed.
- `agentsociety/simulation/simulationengine.py:212–243` — `_restore_external_simulator_state()`: the `if economy_checkpoint_path:` branch (line 226) and the `RuntimeError` guard (lines 233–239).

## Similar Patterns & Reuse

- **KV integrity check**: `clickhouse.py:397–407` and `duckdb.py:420–429` — the existing `expected_agent_ids.issubset(kv_agent_ids)` check is the correct pattern for candidate rejection. Economy existence must not become a second `continue` trigger; it must be modeled differently (derive the path and pass it through, let the consumer handle absence).
- **Warning-and-continue pattern**: `simulationengine.py:227–231` — the existing `try/except` block around `economy_client.load()` is exactly the right pattern. The fix to the `else` branch (lines 232–243) should match this same structure: log WARNING, do not raise.

## Implementation Strategy

The changes are small, localized, and independent. They can be implemented in any order.

### Change 1 — `clickhouse.py:_fetch_checkpoint_snapshots()`: remove `has_economy`, add step >= 1 filter, always derive `econ_path`

**Before** (`clickhouse.py:356–363`):
```python
def _fetch_checkpoint_snapshots(
    self,
    source_exp_id: str,
    resume_step: int,
    rollback_depth: int,
    expected_agent_ids: set[int],
    has_economy: bool = False,
) -> tuple[int, dict[int, list], dict[int, list], dict[int, list], list[dict], str]:
```

**After**: Remove the `has_economy: bool = False` parameter entirely.

**Before** (candidate query, `clickhouse.py:366–378`):
```sql
SELECT DISTINCT simulation_step FROM agent_kv_snapshot
WHERE exp_id = {source_exp_id:String} AND simulation_step <= {resume_step:Int32}
ORDER BY simulation_step DESC
LIMIT {rollback_depth:Int32}
```

**After**: Add `AND simulation_step >= 1` to the WHERE clause:
```sql
SELECT DISTINCT simulation_step FROM agent_kv_snapshot
WHERE exp_id = {source_exp_id:String}
  AND simulation_step <= {resume_step:Int32}
  AND simulation_step >= 1
ORDER BY simulation_step DESC
LIMIT {rollback_depth:Int32}
```

**Before** (`clickhouse.py:409–421`, the economy file guard inside the candidate loop):
```python
# If economy is used, verify checkpoint file exists on disk
econ_path = ""
if has_economy:
    econ_path = str(self.home_dir / "checkpoints" / source_exp_id / f"econ_step_{attempt_step}.bin")
    from pathlib import Path as _Path
    if not _Path(econ_path).is_file():
        reason = f"Economy checkpoint missing at step {attempt_step}: {econ_path}"
        if first_failure_reason is None:
            first_failure_reason = reason
        get_logger().warning(
            reason + (f". Trying older step ({remaining} remaining)." if remaining > 0 else ". No more candidates.")
        )
        continue
```

**After**: Replace the entire block with unconditional path derivation; no file existence check; no `continue`:
```python
econ_path = str(self.home_dir / "checkpoints" / source_exp_id / f"econ_step_{attempt_step}.bin")
```

### Change 2 — `clickhouse.py:fetch_resume_data()`: remove `has_economy=` argument

**Before** (`clickhouse.py:333–339`):
```python
) = self._fetch_checkpoint_snapshots(
    source_exp_id=source_exp_id,
    resume_step=resume_step,
    rollback_depth=rollback_depth,
    expected_agent_ids={int(r["agent_id"]) for r in static_rows},
    has_economy=bool(economy_checkpoint_path),
)
```

**After**: Remove the `has_economy=bool(economy_checkpoint_path)` line.

### Change 3 — `duckdb.py:_fetch_checkpoint_snapshots()`: mirror Change 1

Same three sub-changes as Change 1, applied to `duckdb.py:386–507`:
- Remove `has_economy: bool = False` parameter from signature (`duckdb.py:392`).
- Add `AND simulation_step >= 1` to the candidate query WHERE clause (`duckdb.py:398–404`).
- Replace the economy file guard block (`duckdb.py:431–443`) with unconditional `econ_path = str(self.home_dir / "checkpoints" / source_exp_id / f"econ_step_{attempt_step}.bin")`.

### Change 4 — `duckdb.py:fetch_resume_data()`: mirror Change 2

Remove `has_economy=bool(economy_checkpoint_path)` from the call at `duckdb.py:367`.

### Change 5 — `simulationengine.py:_restore_external_simulator_state()`: soften economy restore

**Before** (`simulationengine.py:225–243`):
```python
economy_checkpoint_path = self._resume_state.get("economy_checkpoint_path", "")
if economy_checkpoint_path:
    try:
        await self._environment.economy_client.load(economy_checkpoint_path)
        get_logger().info(f"Economy state restored from {economy_checkpoint_path}")
    except Exception as e:
        get_logger().warning(f"Failed to restore economy state: {e}")
else:
    if latest_step > 0:
        raise RuntimeError(
            f"Resume at step {latest_step} has no economy checkpoint path. "
            "The economy simulator cannot be restored. "
            "This indicates a checkpoint write failure or incomplete flush. "
            "Cannot continue resume safely - the economy state would be corrupted."
        )
    get_logger().info(
        "No economy checkpoint (latest_step == 0, no checkpoint was ever written); "
        "economy starts fresh. Expected for experiments that crashed before their first safe step."
    )
```

**After**: The `else` branch drops the `RuntimeError` entirely. Both branches (path set but load fails; path empty) converge on warn-and-continue:
```python
economy_checkpoint_path = self._resume_state.get("economy_checkpoint_path", "")
if economy_checkpoint_path:
    try:
        await self._environment.economy_client.load(economy_checkpoint_path)
        get_logger().info(f"Economy state restored from {economy_checkpoint_path}")
    except Exception as e:
        get_logger().warning(
            f"Failed to restore economy state from {economy_checkpoint_path}: {e}. "
            "Economy simulator will start fresh."
        )
else:
    get_logger().warning(
        f"No economy checkpoint path recorded (latest_step={latest_step}). "
        "Economy simulator will start fresh."
    )
```

The warning message in the non-empty path case is slightly expanded to include the path and the consequence, making logs actionable.

## Trade-Offs

| Gain | Cost |
|---|---|
| Resume succeeds when economy `.bin` files are absent, preserving all agent KV/stream memory | Economy simulator state is not restored when the file is missing; it starts fresh. This is an acceptable loss because the alternative is discarding all agent memory entirely. |
| Simpler candidate selection: one gate (KV completeness), one concern | The `economy_checkpoint_path` value returned from `_fetch_checkpoint_snapshots()` no longer indicates whether the file actually exists; callers must treat it as "the expected path, may or may not be on disk." |
| No step-0 false resume | Experiments that somehow only wrote a step-0 KV snapshot will now fail to find a valid candidate (correctly), rather than resuming from a semantically-empty state. |
| Removes the `RuntimeError` in `simulationengine.py` | A corrupt or diverged economy state goes undetected at startup. The operator must check logs manually to know whether economy was restored or restarted. |

## Rejected Approaches

**Approach: Keep the file check but make it non-fatal (log and continue inside the loop without `continue`)**
- Why rejected: This conflates file absence detection with the candidate selection loop. If the file is absent at step N but present at step N-1, the current loop would skip N for a reason that `simulationengine.py` would handle anyway. The correct ownership boundary is: the database layer selects the best KV-complete snapshot; `simulationengine.py` handles economy file absence at restore time. Mixing them produces confusing rollback behavior driven by economy file availability rather than KV data integrity.

**Approach: Copy or sync economy `.bin` files as part of resume setup**
- Why rejected: Out of scope and architecturally complex. The economy binary format is opaque (C++ gRPC binary); the simulation engine does not own the write path. Attempting to sync files introduces distributed storage concerns that do not belong in the Python layer.

**Approach: Store a "economy checkpoint written" boolean flag separately from the path**
- Why rejected: Unnecessary indirection. The `economy_checkpoint_path` column already encodes presence/absence (empty string = never written). The downstream `load()` call is the correct place to discover whether the file still exists at restore time.

**Approach: Raise a more informative error instead of warn-and-continue in `simulationengine.py`**
- Why rejected: The original `RuntimeError` guard was added as a safety net against silent economy corruption. However, the actual risk is low: if economy starts fresh, subsequent economic activity simply proceeds from the simulator's default state rather than the checkpointed state. This is observable in output data and is far preferable to a crash that forces a full restart. The warn-and-continue pattern matches how mobility checkpoint failures are already handled elsewhere in the same function (`simulationengine.py:246–253`).

## Assumptions & Open Questions

- It is assumed that `self.home_dir` is the same `Path` object in both `ClickHouseDatabase` and `DuckDBDatabase` instances and resolves to the correct experiment data root. If `home_dir` differs between the machine that wrote checkpoints and the machine that resumes, `econ_path` will be wrong regardless — but this is a pre-existing problem outside the scope of this fix.
- It is assumed that `economy_client.load()` raises a catchable Python exception (not `SystemExit` or a signal) when the file is missing. The existing `except Exception` clause in `simulationengine.py:231` is consistent with this assumption.
- The `simulation_step >= 1` lower bound is correct. Verify that step 0 KV snapshots are written during agent initialization (before any simulation tick), and that no legitimate resume scenario requires returning to step 0.

## Code That Could Be Refactored *(informational)*

- `clickhouse.py:413` and `duckdb.py:433` — Both files do `from pathlib import Path as _Path` inside a loop body. After the economy guard is removed entirely, this import disappears. If a Path import is still needed elsewhere in the function after the fix, it should be moved to the top of the file.
- `clickhouse.py:325` and `duckdb.py:360` — The `if resume_step >= 0:` guard before calling `_fetch_checkpoint_snapshots()` will now be `if resume_step >= 1:` implicitly via the query filter, but the outer `if` still uses `>= 0`. After this fix, `resume_step` from `last_mobility_safe_step` can still be 0 and will pass the outer guard, but `_fetch_checkpoint_snapshots()` will return no candidates (because the query filters `>= 1`). This is not incorrect, but it is slightly wasteful — the outer guard could be tightened to `if resume_step >= 1:` to skip the DB round-trip entirely. Left as informational since it does not affect correctness.

## Proposed Next Steps

1. Apply Change 1 to `agentsociety/database/clickhouse.py:_fetch_checkpoint_snapshots()` (remove `has_economy` parameter, add `AND simulation_step >= 1` to the candidate query, replace economy guard block with single `econ_path = str(...)` assignment).
2. Apply Change 2 to `agentsociety/database/clickhouse.py:fetch_resume_data()` (remove `has_economy=` keyword argument from the call).
3. Apply Change 3 to `agentsociety/database/duckdb.py:_fetch_checkpoint_snapshots()` (identical logical changes to step 1).
4. Apply Change 4 to `agentsociety/database/duckdb.py:fetch_resume_data()` (identical to step 2).
5. Apply Change 5 to `agentsociety/simulation/simulationengine.py:_restore_external_simulator_state()` (drop `RuntimeError`, replace with WARNING log in the `else` branch; expand warning message in the `except` branch).
6. Validate against the scenario from the run log: simulate steps 1–4, abort at step 5, delete the `econ_step_*.bin` files, resume — confirm logs show successful KV restore at step 4 and a WARNING about economy starting fresh, with `step=4` (not `-1`) in the resume info line.
