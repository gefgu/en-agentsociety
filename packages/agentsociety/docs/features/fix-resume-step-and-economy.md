# Fix Resume Step Counter and Economy Checkpoint Path
> Two surgical fixes to make resume start at the correct step and find the economy checkpoint file.

## Purpose & Motivation

Resume simulations currently exhibit two bugs that prevent a clean restart:

1. **Wrong starting step**: After resume, `_total_steps` is initialized to `-1` instead of `last_mobility_safe_step + 1`. The log reads `step=-1` and `Start simulation day 0 at 25201, step -1`. This violates the invariant that a resumed simulation must never start below step 1.

2. **Economy checkpoint not found**: The C++ gRPC sidecar (`agentsociety-sim-oss`) cannot open the economy checkpoint binary because the path stored in ClickHouse is relative (e.g., `data/checkpoints/{exp_id}/econ_step_12.bin`), and the sidecar resolves it relative to its own working directory (`data/`), producing `data/data/checkpoints/...`.

Both bugs are regressions introduced in the checkpoint refactor (`5b9bee9`). Fixing them unblocks the e2e test `005_resume_lane_position_state.py`.

## Success Criteria

- Resume log shows `step >= 1` (specifically `last_mobility_safe_step + 1`, e.g. `13` when the safe step was `12`).
- No `[WARNING] Failed to restore economy state` in resume logs.
- `tests/e2e/005_resume_lane_position_state.py` exits 0 within the 200-second budget.

## Scope

**In scope:**
- Fix `restore_runtime_state` in `checkpointmanager.py` to derive `total_steps` from `last_mobility_safe_step + 1`.
- Fix `save_checkpoint` in `checkpointmanager.py` to use an absolute path for the economy checkpoint.
- Add a `set_simulation_step` call on `self._database_writer` in `simulationengine.py` alongside the existing `db_actor` call, so agent-side records carry the correct step (root cause fix for why `latest_step` was `-1`).

**Out of scope:**
- Any other resume logic, rollback, snapshot validation, or mobility restoration changes.
- Changes to the ClickHouse schema or migrations.
- New features or refactors.

## Constraints

- The C++ sidecar must receive an absolute path. Using `Path.resolve()` on `self._home_dir` before constructing the checkpoint path is sufficient.
- The `_database_writer` attribute is `Optional[DatabaseWriter]` (`simulationengine.py:79`); the call must be guarded.
- The `set_simulation_step` method signature is `set_simulation_step(self, step: int) -> None` at `base_database.py:170`.
- Do not change the public interface of `CheckpointManager.__init__` or `restore_runtime_state`.

## Architecture & Integration Points

- `agentsociety/simulation/checkpointmanager.py:34` — `restore_runtime_state()`: reads `resume_state["latest_step"]` to derive `total_steps`; must switch to `last_mobility_safe_step + 1`.
- `agentsociety/simulation/checkpointmanager.py:518` — `save_checkpoint()`: builds `checkpoint_dir` as `Path(self._home_dir) / "checkpoints" / self._exp_id`; must use `Path(self._home_dir).resolve()` instead.
- `agentsociety/simulation/simulationengine.py:746-755` — `step()`: calls `db_actor.set_simulation_step.remote(step=self._total_steps)` on the Ray actor but never calls `self._database_writer.set_simulation_step()`; agent records therefore carry `simulation_step = -1` (the default at `base_database.py:105`).
- `agentsociety/database/base_database.py:105` — `self.simulation_step = -1`: the default that is never overwritten when only the actor path is used.
- `agentsociety/database/base_database.py:170` — `set_simulation_step(self, step: int) -> None`: the method to call on `_database_writer`.
- `agentsociety/database/base_database.py:524-529` — `_fetch_checkpoint_snapshots()`: constructs `econ_path` from `self.home_dir / "checkpoints" / ...`; this path is local to the database reader, not the sidecar. The sidecar uses the path stored in ClickHouse, which comes from `save_checkpoint`. This path in the database is what must be absolute.

## Similar Patterns & Reuse

- **`_last_mobility_safe_step` field**: `checkpointmanager.py:32` — already set by `restore_runtime_state` at line 66 from `resume_state.get("last_mobility_safe_step", -1)`. Fix 1 reuses this same key, just derives `total_steps` from it instead of from `latest_step`.
- **`Path.resolve()` pattern**: used in `base_database.py:18` (`Path(__file__).resolve()`) for the migrations directory. Same pattern applies to `home_dir` in `save_checkpoint`.
- **Guard pattern for `_database_writer`**: `simulationengine.py:682` already guards `_database_writer is None` before use; Fix 3 follows the same guard pattern.

## Implementation Strategy

### Fix 1 — Correct `total_steps` in `restore_runtime_state`

**File**: `agentsociety/simulation/checkpointmanager.py`

**Before** (lines 45-46):
```python
latest_step = resume_state.get("latest_step")
total_steps = int(latest_step) if latest_step is not None else 0
```

**After**:
```python
last_safe = int(resume_state.get("last_mobility_safe_step", -1) or -1)
total_steps = max(1, last_safe + 1)
```

Rationale: `last_mobility_safe_step` is written by `save_checkpoint` only after a successful economy checkpoint save (`checkpointmanager.py:524`), making it the authoritative record of the last durable simulation step. `latest_step` comes from `max(simulation_step) FROM step_agent_status`, which is unreliable because agent records have `simulation_step = -1` (see Fix 3). The `max(1, ...)` clamp enforces the invariant that resume never starts below step 1.

Note: the line at 66 that sets `self._last_mobility_safe_step` from `resume_state` is unchanged; only the `total_steps` derivation changes.

Also update the log message on line 70 to reflect `total_steps` correctly:
```python
get_logger().info(
    "Restored resume runtime state: "
    f"step={total_steps}, day={exp_info.cur_day}, "
    f"t={exp_info.cur_t}, input_tokens={exp_info.input_tokens}, "
    f"output_tokens={exp_info.output_tokens}"
)
```
This line is already correct in structure; no change needed there beyond the variable now carrying the right value.

### Fix 2 — Absolute economy checkpoint path in `save_checkpoint`

**File**: `agentsociety/simulation/checkpointmanager.py`

**Before** (lines 518-520):
```python
checkpoint_dir = Path(self._home_dir) / "checkpoints" / self._exp_id
checkpoint_dir.mkdir(parents=True, exist_ok=True)
econ_path = str(checkpoint_dir / f"econ_step_{step}.bin")
```

**After**:
```python
checkpoint_dir = Path(self._home_dir).resolve() / "checkpoints" / self._exp_id
checkpoint_dir.mkdir(parents=True, exist_ok=True)
econ_path = str(checkpoint_dir / f"econ_step_{step}.bin")
```

Rationale: `self._home_dir` is passed in as a relative path (e.g., `"data"`). The C++ sidecar's CWD is `data/`, so a relative path `data/checkpoints/...` becomes `data/data/checkpoints/...` from the sidecar's perspective. Resolving to an absolute path at write time makes the stored path unambiguous regardless of which process reads it.

### Fix 3 — Sync `_database_writer.simulation_step` on each step

**File**: `agentsociety/simulation/simulationengine.py`

**Before** (lines 746-755):
```python
# Add simulation step to ClickHouse
if self._db_actor is not None:
    try:
        await self._db_actor.set_simulation_step.remote(
            step=self._total_steps,
        )
    except Exception as e:
        get_logger().warning(
            f"Error adding simulation step to ClickHouse: {e}"
        )
```

**After**:
```python
# Add simulation step to ClickHouse
if self._db_actor is not None:
    try:
        await self._db_actor.set_simulation_step.remote(
            step=self._total_steps,
        )
    except Exception as e:
        get_logger().warning(
            f"Error adding simulation step to ClickHouse: {e}"
        )
if self._database_writer is not None:
    self._database_writer.set_simulation_step(self._total_steps)
```

Rationale: `DatabaseWriter` (a `BaseSimulationDatabase` subclass) maintains `self.simulation_step` (default `-1`, `base_database.py:105`). Agent records written via `insert_record` use this field when `simulation_step` is not in the record dict (`base_database.py:175-176`). Without this call, all agent-side rows land with `simulation_step = -1`, which is why `max(simulation_step) FROM step_agent_status` returned `-1` and `resume_state["latest_step"]` was `-1`. Fix 3 is the root cause fix; Fix 1 removes the dependency on that unreliable value entirely.

## Trade-Offs

- Fix 1 drops `latest_step` as the source of truth for `total_steps` on resume. `latest_step` was already meaningless (always `-1`), so this is a strict improvement. If in the future `latest_step` is repaired (e.g., via Fix 3), the value from `last_mobility_safe_step + 1` remains correct and takes precedence — it reflects the last safely checkpointed step, not the last step that merely started.
- Fix 2 makes the stored path absolute, which means the path is tied to the machine that ran the original simulation. Cross-machine resume (moving data between hosts) would require path translation. This is acceptable: the existing design already assumes the checkpoint binary files are local.
- Fix 3 adds a synchronous call on each step to keep `_database_writer.simulation_step` in sync. The method is `O(1)` (`base_database.py:170-171`), so there is no performance impact.

## Rejected Approaches

- **Repairing `latest_step` only and keeping it as the source of truth**: Rejected because `last_mobility_safe_step` is strictly more reliable — it is written atomically with the economy checkpoint and reflects a step whose full state was durably saved. `latest_step` reflects only that a step started, not that it completed safely.
- **Resolving the path in `_fetch_checkpoint_snapshots` (reader side)**: `base_database.py:524-529` constructs `econ_path` from `self.home_dir` for the KV snapshot query path, not for the economy load. The economy load uses the path stored in ClickHouse (`economy_checkpoint_path` column, read at `base_database.py:425`). The fix must be at write time in `save_checkpoint`, not at read time. Fixing only the reader would not change what the sidecar receives.
- **Passing `last_mobility_safe_step` as a constructor argument to `CheckpointManager`**: Unnecessary indirection. The value is already present in `resume_state` at call time in `restore_runtime_state`.

## Assumptions & Open Questions

- `self._home_dir` in `CheckpointManager` is the same directory that the simulation process runs from, so `Path(self._home_dir).resolve()` produces a valid absolute path on the host where the sidecar runs. If the sidecar runs in a container with a different mount, a different fix would be needed. Assumed: sidecar and Python process share the same filesystem namespace.
- `_database_writer` is initialized before `step()` is first called (`simulationengine.py:148`). The `is not None` guard handles the edge case where it was not initialized.
- The test `005_resume_lane_position_state.py` uses the config at `tests/e2e/configs/003_resume_10_agents_local.yaml`. That config must already set `home_dir` to a relative path (e.g., `"data"`) for Fix 2 to be triggered. This is assumed based on the error log showing `data/data/checkpoints/...`.

## Code That Could Be Refactored *(informational)*

- `base_database.py:524-529` — `_fetch_checkpoint_snapshots` rebuilds `econ_path` locally from `self.home_dir` rather than using the stored `economy_checkpoint_path`. The local rebuild and the stored path now both exist. After Fix 2, the stored path is authoritative and correct; the local rebuild (used for the KV snapshot query check) is redundant and could be removed in a follow-up.
- `checkpointmanager.py:45-46` — the `latest_step` variable and the `"latest_step"` key in `resume_state` (set at `base_database.py:421` and returned at `base_database.py:462`) are no longer used for `total_steps`. After Fix 3 repairs the underlying data, `latest_step` could be useful for diagnostics. For now it is unused by `restore_runtime_state`; a comment noting this would clarify intent.

## Proposed Next Steps

1. Apply Fix 2 first (absolute path in `save_checkpoint`, `checkpointmanager.py:518`): it is one-line and has no logical dependencies on the other fixes.
2. Apply Fix 1 (`restore_runtime_state`, `checkpointmanager.py:45-46`): change `total_steps` derivation to `max(1, last_safe + 1)`.
3. Apply Fix 3 (`simulationengine.py` after line 755): add `self._database_writer.set_simulation_step(self._total_steps)` call.
4. Run `sh tests/run_e2e_tests.sh` from `packages/agentsociety/` and confirm `005_resume_lane_position_state.py` exits 0 with no economy warning and `step >= 1` in the resume log.
