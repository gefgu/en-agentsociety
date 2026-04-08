# Fix Resume Step Counter and Economy Checkpoint Path — Run Tracking

Based on plan: fix-resume-step-and-economy.md

## Steps

- [x] Fix 1: `restore_runtime_state` in `checkpointmanager.py` — use `last_mobility_safe_step + 1` for `total_steps`
- [x] Fix 2: `save_checkpoint` in `checkpointmanager.py` — use `Path(self._home_dir).resolve()` for absolute economy checkpoint path
- [ ] Fix 3: `simulationengine.py` — add `_database_writer.set_simulation_step()` call alongside the Ray actor call
  - BLOCKED: `DatabaseWriter` (storage/database.py) has no `set_simulation_step` method. Plan was based on incorrect class assumption.

## Test Status

Run 1 fails: agents always choose bike transport for short distances (<3km), completing all trips within 600 ticks (10 min simulation time). `lane_position` never appears in `agent_kv_snapshot` because all journeys finish before the next checkpoint. This is a pre-existing test design issue unrelated to the 3 code fixes.
