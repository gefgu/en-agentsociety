# Fault-Tolerant Resume — Economy Checkpoint Check Fix
> Remove the economy file existence gate from checkpoint candidate selection, enforce a minimum resume step of 1, and raise a hard error (not warn-and-continue) when all candidates fail during resume.

## Purpose & Motivation

When a simulation is aborted mid-run, the resume path iterates candidate KV snapshots in descending step order and picks the first one that passes all integrity checks. The current code couples two unrelated concerns in that gate: (1) KV completeness (all expected agent IDs present) and (2) economy binary file existence on disk.

The economy binary file check is the wrong gate for two reasons. First, `CheckpointManager.restore_external_simulator_state()` in `checkpointmanager.py` already handles a missing or failed economy load — the check in the database layer is therefore redundant and stricter than the consumer. Second, the economy `.bin` files may not exist on the machine running the resume (written to a different node, not yet flushed to shared storage, etc.). This causes all candidates to be rejected, yielding a `step=-1` resume and the silent "No valid checkpoint snapshots found; memory will start from defaults" warning — which discards all agent memory and continues as if no resume was requested.

The user has confirmed: all three failure modes (all candidates fail, no KV snapshots found, economy path missing at `latest_step > 0`) are **fatal** when resuming. There is no "fresh start from defaults" fallback. The fix direction is to keep file-existence checking where it belongs — but propagate it as a hard error when all candidates fail, not a silent fallback.

Additionally, step 0 is the pre-simulation initialization snapshot, not a meaningful resume point. Accepting it as a candidate is semantically wrong and produces confusing "resumed from step 0" behavior.

## Success Criteria

- A simulation that ran steps 1–N, was aborted, and whose economy `.bin` files are missing causes resume to **raise a descriptive `RuntimeError`** (not silently start from defaults).
- A simulation that ran steps 1–N and whose economy `.bin` files are present resumes correctly at the highest valid KV snapshot step.
- A simulation that ran steps 1–N resumes at a step >= 1, never at step 0.
- KV completeness remains the sole gate for candidate rejection within the selection loop.
- The `RuntimeError` in `CheckpointManager.restore_external_simulator_state()` at `checkpointmanager.py:97` (economy path empty at `latest_step > 0`) is **preserved**, not softened.
- `_validate_resume_agent_count` in `infrastructuremanager.py:188` is preserved; it guards a distinct misconfiguration (wrong number of agents configured).

## Scope

**In scope:**
- `agentsociety/database/base_database.py` — `_fetch_checkpoint_snapshots()` and `fetch_resume_data()`

**Out of scope:**
- `agentsociety/simulation/checkpointmanager.py` — `restore_external_simulator_state()` RuntimeError guard is **kept as-is**
- `agentsociety/simulation/infrastructuremanager.py` — `_validate_resume_agent_count()` is **kept as-is**
- `agentsociety/database/clickhouse.py` — `_fetch_checkpoint_snapshots()` no longer exists here; consolidated into base class
- `agentsociety/database/duckdb.py` — same, no `_fetch_checkpoint_snapshots()` to change
- `database_actor.py` — no changes
- `infrastructuremanager.py` — no changes beyond what is noted above
- `configs/env.py` — no changes
- KV integrity check logic — keep as-is
- `rollback_depth` machinery — keep as-is
- The schema for `economy_checkpoint_path` in `experiment_info` — no changes

## Constraints

- The fix is entirely within `base_database.py`. No other file needs changes.
- No new public API surface; the return type of `_fetch_checkpoint_snapshots()` stays as a 6-tuple.
- The `economy_checkpoint_path` value returned from `_fetch_checkpoint_snapshots()` must always be the derived path for the selected step (even if the file does not exist on disk), so `CheckpointManager.restore_external_simulator_state()` can attempt load and raise its own error if missing.

## Architecture & Integration Points

The codebase has been refactored since this plan was originally written. The key architectural facts now are:

1. `_fetch_checkpoint_snapshots()` is consolidated into `base_database.py:465–602`. It is **no longer duplicated** in `clickhouse.py` or `duckdb.py`.
2. Checkpoint save/restore logic lives in `CheckpointManager` (`simulation/checkpointmanager.py`), extracted from `simulationengine.py`.
3. `SimulationEngine.init()` calls `self._checkpoint_manager.restore_external_simulator_state()` at `simulationengine.py:257`.

The resume data flow is a sequential pipeline:

1. `simulationengine.py:224` — `self._infrastructure_manager.load_resume_state()` triggers DB fetch.
2. `infrastructuremanager.py:205` — `load_resume_state()` calls `self._db_actor.fetch_resume_data.remote(source_exp_id, rollback_depth)`.
3. `DatabaseActor` delegates to `BaseSimulationDatabase.fetch_resume_data()` (`base_database.py:389`).
4. `fetch_resume_data()` reads `last_mobility_safe_step` and `economy_checkpoint_path` from `experiment_info`, then calls `_fetch_checkpoint_snapshots()` (`base_database.py:443`).
5. Inside `_fetch_checkpoint_snapshots()` (`base_database.py:465`): candidate steps are queried, each is checked for KV completeness, and the economy file gate (currently) rejects candidates where the `.bin` file is missing.
6. If all candidates fail, `_fetch_checkpoint_snapshots()` returns `(-1, {}, {}, {}, [], "")` silently (`base_database.py:602`).
7. `fetch_resume_data()` returns a dict with `economy_checkpoint_path=""` and `last_mobility_safe_step=-1`.
8. `simulationengine.py:226` — `self._checkpoint_manager.restore_runtime_state()` sets `self._total_steps`.
9. `simulationengine.py:257` — `self._checkpoint_manager.restore_external_simulator_state()` reads `economy_checkpoint_path` and raises `RuntimeError` at `checkpointmanager.py:97` if path is empty and `latest_step > 0`.

The problem: step 6 silently discards data rather than raising. Step 9 then raises a misleading error about "no economy checkpoint path" when the real cause is "all economy `.bin` files were missing during candidate selection." The fix is to raise the descriptive error at step 6 instead of returning a silent sentinel.

Specific integration points:

- `agentsociety/database/base_database.py:465–602` — `_fetch_checkpoint_snapshots()`: the full candidate selection loop including the economy file guard (lines 519–541) to be replaced.
- `agentsociety/database/base_database.py:435` — `if resume_step >= 0:` outer guard before calling `_fetch_checkpoint_snapshots()`.
- `agentsociety/database/base_database.py:443–450` — call site: `has_economy=bool(economy_checkpoint_path)` argument to be removed.
- `agentsociety/database/base_database.py:472` — `_fetch_checkpoint_snapshots()` signature: `has_economy: bool = False` parameter to be removed.
- `agentsociety/database/base_database.py:594–602` — all-candidates-failed fallback: currently logs WARNING and returns `(-1, {}, {}, {}, [], "")`. Must become a hard `RuntimeError`.
- `agentsociety/simulation/checkpointmanager.py:89–107` — `restore_external_simulator_state()`: the `RuntimeError` at line 97 is **kept unchanged**. It becomes unreachable for the "all `.bin` files missing" scenario because the error will now be raised upstream. It remains correct for the distinct scenario where `economy_checkpoint_path` was never written (experiment crashed before first checkpoint).
- `agentsociety/simulation/infrastructuremanager.py:188–203` — `_validate_resume_agent_count()`: kept unchanged; guards a distinct scenario (wrong agent count configured for resume).

## Similar Patterns & Reuse

- **KV integrity check**: `base_database.py:501–517` — the existing `expected_agent_ids.issubset(kv_agent_ids)` pattern is the correct model for candidate rejection. Economy file existence should not become a second `continue` trigger; it should not gate the loop at all. The path is derived unconditionally and passed through to the consumer.
- **Hard-error pattern on all-candidates-fail**: The existing KV mismatch `continue` already collects `first_failure_reason`. The all-candidates-fail block at `base_database.py:594–602` should reuse this collected reason in the raised `RuntimeError` message.

## Implementation Strategy

The changes are confined to a single method in a single file. They can be applied in one pass.

### Change 1 — `base_database.py:_fetch_checkpoint_snapshots()`: remove `has_economy`, add step >= 1 filter, always derive `econ_path`, raise on all-candidates-fail

**Before** (`base_database.py:472`):
```python
def _fetch_checkpoint_snapshots(
    self,
    source_exp_id: str,
    source_uuid: str,
    resume_step: int,
    rollback_depth: int,
    expected_agent_ids: set[int],
    has_economy: bool = False,
) -> tuple[int, dict[int, list], dict[int, list], dict[int, list], list[dict], str]:
```

**After**: Remove the `has_economy: bool = False` parameter entirely.

**Before** (candidate query call, `base_database.py:475–481`): the `_run_resume_query("candidate_steps", ...)` call. The underlying query (defined in each backend's `_resume_query()` via `"candidate_steps"`) currently filters `simulation_step <= resume_step` only.

**After**: The query must also filter `simulation_step >= 1`. This is enforced by updating the `"candidate_steps"` query string in each backend's `_resume_query()` implementation — `clickhouse.py` and `duckdb.py` — to add `AND simulation_step >= 1` to the WHERE clause.

**Before** (`base_database.py:519–541`, the economy file guard inside the candidate loop):
```python
econ_path = ""
if has_economy:
    econ_path = str(
        self.home_dir
        / "checkpoints"
        / source_exp_id
        / f"econ_step_{attempt_step}.bin"
    )
    if not Path(econ_path).is_file():
        reason = (
            f"Economy checkpoint missing at step {attempt_step}: {econ_path}"
        )
        if first_failure_reason is None:
            first_failure_reason = reason
        get_logger().warning(
            reason
            + (
                f". Trying older step ({remaining} remaining)."
                if remaining > 0
                else ". No more candidates."
            )
        )
        continue
```

**After**: Replace the entire block with unconditional path derivation; no file existence check; no `continue`:
```python
econ_path = str(
    self.home_dir
    / "checkpoints"
    / source_exp_id
    / f"econ_step_{attempt_step}.bin"
)
```

**Before** (`base_database.py:594–602`, the all-candidates-failed fallback):
```python
if first_failure_reason:
    get_logger().warning(
        f"All {len(candidate_steps)} checkpoint candidate(s) failed. "
        f"First error: {first_failure_reason}"
    )
get_logger().warning(
    "No valid checkpoint snapshots found; memory will start from defaults"
)
return -1, {}, {}, {}, [], ""
```

**After**: Replace the silent fallback with a hard `RuntimeError`:
```python
n = len(candidate_steps)
detail = f" First error: {first_failure_reason}" if first_failure_reason else ""
raise RuntimeError(
    f"Resume failed: no valid checkpoint found for experiment '{source_exp_id}'. "
    f"All {n} candidate step(s) were rejected.{detail}"
)
```

### Change 2 — `base_database.py:fetch_resume_data()`: remove `has_economy=` argument

**Before** (`base_database.py:443–450`):
```python
) = self._fetch_checkpoint_snapshots(
    source_exp_id=source_exp_id,
    source_uuid=source_uuid,
    resume_step=resume_step,
    rollback_depth=rollback_depth,
    expected_agent_ids=set(),
    has_economy=bool(economy_checkpoint_path),
)
```

**After**: Remove the `has_economy=bool(economy_checkpoint_path)` line.

### Change 3 — `clickhouse.py` and `duckdb.py`: add `AND simulation_step >= 1` to `"candidate_steps"` query

These files implement `_resume_query()` which returns the backend-specific SQL for each named query. The `"candidate_steps"` query currently filters `simulation_step <= resume_step` only. Add `AND simulation_step >= 1` to the WHERE clause in both files.

This is the only change needed in `clickhouse.py` and `duckdb.py` — no signature changes, no other logic changes.

## Trade-Offs

| Gain | Cost |
|---|---|
| Resume fails loudly and descriptively when economy `.bin` files are absent, rather than silently restarting from scratch | Economy-file-missing scenarios that previously "worked" (by restarting silently) now crash. Operators must ensure checkpoint files are accessible before resuming. |
| The error message names the actual cause ("all N candidates missing economy file") not a downstream symptom ("no economy checkpoint path") | None — this is a strict improvement in error quality. |
| Simpler candidate selection: one gate (KV completeness), one concern | The `economy_checkpoint_path` value returned from `_fetch_checkpoint_snapshots()` no longer indicates whether the file exists on disk; callers treat it as "the expected path, verify existence during restore." |
| No step-0 false resume | Experiments that somehow only wrote a step-0 KV snapshot now correctly raise, rather than resuming from a semantically-empty state. |
| `CheckpointManager.restore_external_simulator_state()` RuntimeError at `checkpointmanager.py:97` is preserved | The `checkpointmanager.py:97` guard becomes unreachable for the "economy files missing" scenario — it is now only reachable for "economy path was never recorded." This is correct behavior: two distinct failure modes, two distinct error sites. |

## Rejected Approaches

**Approach: Warn and continue (the original plan's Change 5)**
- Why rejected: The user explicitly confirmed all failure modes are fatal during resume. A "warn and continue" path that restores agent KV/stream memory but starts the economy simulator fresh produces a silently corrupted simulation state. The original plan's rationale ("preferable to a crash that forces a full restart") was wrong because the full restart was already happening silently via the `-1` sentinel return.

**Approach: Keep the file check but make it non-fatal (log and continue inside the loop without `continue`)**
- Why rejected: This conflates file absence detection with candidate selection. The correct ownership boundary is: the database layer selects the best KV-complete snapshot; `CheckpointManager` handles economy file absence at restore time. The database layer does not own economy file lifecycle.

**Approach: Copy or sync economy `.bin` files as part of resume setup**
- Why rejected: Out of scope and architecturally complex. The economy binary format is opaque (C++ gRPC binary); the Python layer does not own the write path.

**Approach: Store a "economy checkpoint written" boolean flag separately from the path**
- Why rejected: Unnecessary indirection. The `economy_checkpoint_path` column already encodes presence (empty string = never written). The downstream `load()` call is the correct place to discover whether the file still exists at restore time.

**Approach: Add `AND simulation_step >= 1` only to `base_database.py` rather than the backend queries**
- Why rejected: The filter belongs in the SQL query, not in Python post-processing of results. The `_run_resume_query()` abstraction is specifically designed so that filter logic lives in the backend-specific SQL returned by `_resume_query()`. Post-filtering in Python would bypass the `LIMIT {rollback_depth}` semantics — step 0 would consume a rollback slot.

## Assumptions & Open Questions

- It is assumed that `self.home_dir` resolves to the correct experiment data root on the resume machine. If `home_dir` differs between checkpoint write and resume, `econ_path` will be wrong regardless — pre-existing problem outside this scope.
- It is assumed that `economy_client.load()` raises a catchable Python exception when the file is missing. The existing `except Exception` clause in `checkpointmanager.py:94` is consistent with this assumption.
- The `simulation_step >= 1` lower bound is correct. Step 0 KV snapshots are written during agent initialization (before any simulation tick). No legitimate resume scenario requires returning to step 0.
- It is assumed that when `candidate_steps` is empty (no KV snapshot rows at all), the loop body never executes, `first_failure_reason` remains `None`, and the error message should still be raised. The proposed `RuntimeError` text handles this: "All 0 candidate step(s) were rejected." with no `First error:` suffix.

## Code That Could Be Refactored *(informational)*

- `base_database.py:435` — `if resume_step >= 0:` outer guard before calling `_fetch_checkpoint_snapshots()`. After this fix, `resume_step == 0` passes the outer guard but `_fetch_checkpoint_snapshots()` will find no candidates (filtered by `>= 1`) and raise. The outer guard could be tightened to `if resume_step >= 1:` to skip the DB round-trip entirely. Not a correctness issue — the raised error message would be slightly less specific ("All 0 candidates rejected" vs. not even querying). Left informational since correctness is unaffected.
- `base_database.py:519` — After the economy guard is removed, the `Path` import at the top of the file may become unused within `_fetch_checkpoint_snapshots()`. Check whether `Path` is still used elsewhere in the method or class before removing the import.

## Proposed Next Steps

1. Apply Change 1 to `agentsociety/database/base_database.py:_fetch_checkpoint_snapshots()`:
   - Remove `has_economy: bool = False` from the signature (`base_database.py:472`).
   - Replace the economy file guard block (`base_database.py:519–541`) with the single unconditional `econ_path = str(...)` assignment.
   - Replace the silent fallback (`base_database.py:594–602`) with a `RuntimeError`.

2. Apply Change 2 to `agentsociety/database/base_database.py:fetch_resume_data()`:
   - Remove `has_economy=bool(economy_checkpoint_path)` from the call at `base_database.py:449`.

3. Apply Change 3 to `agentsociety/database/clickhouse.py` and `agentsociety/database/duckdb.py`:
   - In each file's `_resume_query()` implementation, add `AND simulation_step >= 1` to the `"candidate_steps"` query WHERE clause.

4. Validate against the target scenario: simulate steps 1–4, abort at step 5, delete the `econ_step_*.bin` files, attempt resume — confirm logs show a descriptive `RuntimeError` naming the missing economy files, not a silent restart from defaults.
