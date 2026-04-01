# Checkpoint Resume: Mobility Reconstruction and Economy Crash Guard
> Fix silent failure modes in the checkpoint resume system and extend it to support trip
> reconstruction from per-agent KV state, replacing the "last safe step" teleport approach with
> a re-submission approach that works at any simulation step.

---

## Revision History

**v1** (original): Fix FINAL bug in `fetch_resume_data()` and add economy crash guard.

**v2**: Extends the plan with three new requirements from the user:
1. Replace the "last mobility safe step" approach with trip reconstruction from KV snapshots.
2. Replace `ALTER TABLE ... UPDATE` mutations with `INSERT` for writing checkpoint columns.
3. Hard crash (not a log) if mobility or economy cannot be fully restored on resume.

**v3** (this version): Closes all open questions. Makes implementation spec fully concrete and
actionable. Removes speculative language; plan is ready to hand to an implementer.

---

## Purpose & Motivation

The checkpoint/resume system was built and fully implemented per
`docs/features/done/clickhouse-checkpoint.md`. The implementation is functionally correct in its
data capture path, but the restore path for mobility and economy has two bugs and one design
limitation that surface on every real resume:

**Bug 1 — Mobility position never restored.**
The resume log consistently shows:
```
No mobility-safe step found; skipping mobility position reset
```
This happens because `_restore_external_simulator_state()` receives `last_mobility_safe_step = -1`
from `fetch_resume_data()`. The value is -1 because the SELECT query that reads
`experiment_info` does not include the `FINAL` keyword, which is required on a
`ReplacingMergeTree` table to collapse duplicate rows and surface mutations. The
`update_experiment_info_checkpoint()` path uses `ALTER TABLE ... UPDATE` (a ClickHouse mutation),
which writes its result as a new row version rather than modifying in place. Without `FINAL`, the
query sees the original row (with `last_mobility_safe_step DEFAULT -1`) alongside the mutated row
and returns whichever ClickHouse picks based on merge state — almost always the original.

**Bug 2 — Economy starts fresh silently.**
The resume log consistently shows:
```
No economy checkpoint path found; economy starts fresh
```
This path at `simulationengine.py:224` is a silent `get_logger().info(...)` followed by no error.
The economy simulator is a stateful C++ binary. If an agent was hired, paid taxes, or accumulated
savings before the crash, those are all lost. This must be a hard crash, not an informational log.

**Design limitation — "Last safe step" teleport is too restrictive.**
The original approach only checkpoints mobility state when ALL citizen agents are simultaneously
at AOI positions (`all_at_aoi = True` in `_save_checkpoint()`). In large-scale simulations with
thousands of agents, there is almost always at least one agent in transit, so mobility checkpoints
are rare or never happen in practice. The user requires a more general approach: reconstruct
each agent's trip from the KV snapshot of their `current_plan`, regardless of where agents were
when the snapshot was taken.

---

## Success Criteria

1. After a resume of any experiment that ran for N steps, each citizen agent whose KV snapshot
   shows a non-SLEEP status and a non-empty `current_plan` has their trip re-submitted to the
   mobility simulator, targeting the same destination AOI recorded in `current_plan`.
2. Each citizen agent whose KV snapshot shows an `aoi_position` is placed at that AOI via
   `ResetPersonPosition`.
3. Each citizen agent whose KV snapshot shows a `lane_position` is placed at their last known
   AOI (from the `position` KV entry's `aoi_id` — see Resolved Decisions) via
   `ResetPersonPosition`, then has their in-progress trip re-submitted.
4. Attempting to resume an experiment where `resume_step > 0` but `economy_checkpoint_path` is
   empty raises a `RuntimeError` immediately. No silent economy fresh-start.
5. `update_experiment_info_checkpoint()` writes checkpoint columns via `INSERT` instead of
   `ALTER TABLE ... UPDATE`, eliminating the mutation race without requiring `FINAL` on reads.

---

## Scope

**In scope:**
- Replace `ALTER TABLE ... UPDATE` in `update_experiment_info_checkpoint()` with an INSERT of a
  full `experiment_info` row (requires updating `ExperimentInfoRecord` TypedDict and the
  insert normalization method)
- Extend `_restore_external_simulator_state()` to: (a) reset each agent to their last known AOI
  position from KV, then (b) re-submit in-progress trips for agents that were mid-trip
- Change the economy missing-path branch from `get_logger().info(...)` to `raise RuntimeError`
  when `resume_step > 0`
- Reset `current_plan["index"]` back to the in-progress step index before resuming, so agents
  replay from that step
- Add a hard crash guard for mobility reconstruction failures exceeding a threshold
- Add `FINAL` to the `fetch_resume_data()` SELECT as defense-in-depth

**Out of scope:**
- Fast-forwarding trips to the exact position the agent was at when the simulation crashed.
  The approach is: re-submit from last known AOI, not mid-road position.
- Changing snapshot table schemas or migration files (the migration for the checkpoint columns
  already exists in `0013_alter_experiment_info_checkpoint_cols.sql`)
- Removing the `all_at_aoi` check in `_save_checkpoint()`: the economy checkpoint still only
  fires when all agents are at AOI. Trip reconstruction handles the case of agents mid-trip.
- Blocking the checkpoint INSERT flush (fire-and-forget is acceptable; see Resolved Decisions)

---

## Constraints

- The `set_aoi_schedules()` gRPC call (`environment/environment.py:406`) creates a new schedule
  starting from the agent's current position at the current tick. It does NOT fast-forward the
  agent along the route to where they were before the crash. This is an inherent limitation of
  the C++ simulator's exposed API — there is no "set mid-trip state" call in the proto schema.
- `ReplacingMergeTree` FINAL on reads is a safe fallback and low cost for startup-time queries.
  Keep it in the read query even after migrating to INSERT writes, as defense in depth.
- The `ExperimentInfoRecord` TypedDict at `agentsociety/database/schema.py:173` does not
  include the three checkpoint columns (`last_mobility_safe_step`, `prev_mobility_safe_step`,
  `economy_checkpoint_path`). The INSERT approach requires extending this TypedDict and the
  normalization in `insert_experiment_info_record()`.

---

## Architecture & Integration Points

### The broken read path

- `agentsociety/database/clickhouse.py:617-627` — `fetch_resume_data()` queries `experiment_info`
  without `FINAL`. Must add `FINAL`.
- `agentsociety/database/clickhouse.py:644-646` — `last_safe_step` receives -1.
- `agentsociety/simulation/simulationengine.py:227-229` — triggers "No mobility-safe step" log.

Full call chain:
```
SimulationEngine.init()  [simulationengine.py:344]
  → await self._infrastructure_manager.load_resume_state()  [infrastructuremanager.py:206]
    → resume_data = await self._db_actor.fetch_resume_data.remote(...)
      → ClickHouseDatabase.fetch_resume_data()  [clickhouse.py:600]
        → self._query_rows("SELECT ... FROM experiment_info ...")  [clickhouse.py:617]
          ← returns row with last_mobility_safe_step = -1  (BUG: stale row, no FINAL)
  → self._restore_resume_runtime_state()  [simulationengine.py:346]
  → await self._restore_external_simulator_state()  [simulationengine.py:371]
    → resume_step = self._resume_state.get("last_mobility_safe_step", -1)  [simulationengine.py:227]
    → if resume_step < 0: log "No mobility-safe step found"  [simulationengine.py:229]  ← triggered
```

### The broken write path (mutation race)

- `agentsociety/database/clickhouse.py:812-832` — `update_experiment_info_checkpoint()` uses
  `ALTER TABLE experiment_info UPDATE ...`. ClickHouse executes this asynchronously; the new
  column values coexist with the original row until compaction.
- `agentsociety/database/schema.py:173-186` — `ExperimentInfoRecord` TypedDict does not include
  the three checkpoint columns, so they cannot be written via the existing
  `insert_experiment_info_record()` path without extending the TypedDict first.
- `agentsociety/database/migrations/0013_alter_experiment_info_checkpoint_cols.sql:1-4` — adds
  `last_mobility_safe_step Int32 DEFAULT -1`, `prev_mobility_safe_step Int32 DEFAULT -1`,
  `economy_checkpoint_path String DEFAULT ''`.

### The silent economy fresh-start

- `agentsociety/simulation/simulationengine.py:216-224` — `_restore_external_simulator_state()`:
  the `else` branch when `economy_checkpoint_path` is empty logs at INFO and continues. This
  must become a hard crash when `resume_step > 0`.

### The KV snapshot — what is stored for trip reconstruction

At `agentsociety/simulation/simulationengine.py:825-836`, `_save_checkpoint()` exports ALL keys
from each agent's KV memory via `agent.status.export(list(agent.status._data.keys()))`. This
means the following keys are always in the KV snapshot:

- `position` — a dict of the form `{"aoi_position": {"aoi_id": int}}` (when at AOI) or
  `{"lane_position": {"lane_id": int, "s": float}}` (when in transit). This is set by
  `update_motion()` at `agent/agent.py:162`, which iterates `resp_dict.get("motion", {}).items()`
  and writes each field.
- `status` — the `PersonMotion.status` enum integer (1=SLEEP, 2=DRIVING, 3=WALKING, etc.) written
  by the same `update_motion()` loop.
- `current_plan` — a dict with keys `steps` (list), `index` (int), `completed` (bool), etc.
  Each step dict has `to_place`, `start_time`, `intention`, and `evaluation`. Written in
  `societyagent.py:759-761` after each `step_execution()` call.

The `all_at_aoi` check at `simulationengine.py:843-844` ensures a full checkpoint (with economy
save) only fires when `"lane_position" not in position` for all citizen agents. But the KV
snapshot is written at EVERY step regardless (`simulationengine.py:899-900` enqueues it
unconditionally). This means even at steps where agents are mid-trip, their `current_plan` with
the target destination is preserved.

### The gRPC mobility API

Two relevant calls exist:

1. `environment.reset_person_position(person_id, aoi_id)` — teleports agent to an AOI, stops
   any current trip. Implemented via `person_service.ResetPersonPosition`. Per
   `person_service.py:198-211`, this "stops the current trip and switches to sleep status."

2. `environment.set_aoi_schedules(person_id, target_positions, departure_times, modes)` —
   submits a new schedule (one or more trips). Departure time defaults to current tick if not
   provided. This is what `MoveBlock._execute_movement()` uses at `mobility_block.py:698-713`.

There is no "set mid-trip position" or "restore route state" API in the person service proto.
Trip reconstruction via re-submission from a reset position is the only possible approach.

---

## Resolved Decisions

The following questions were open in v2 and have been answered by the user.

**Q1: When a mid-trip agent is reset for reconstruction, should they be placed at home or at
their last known AOI position?**
Decision: Always reset to the **last known AOI position** stored in the agent's KV memory at the
checkpoint step. For an agent with `"lane_position"` in their `position` KV entry, the position
dict also carries an `aoi_id` field representing the last AOI the simulator reported — use that.
Do NOT use home as the fallback. If `aoi_id` cannot be extracted from the position entry, log a
WARNING and skip that agent (they will re-plan on the next tick from wherever the simulator places
them).

**Q2: Should `current_plan["index"]` be reset after reconstruction?**
Decision: Reset `current_plan["step_index"]` (the `index` field inside the `current_plan` dict
in KV memory) back to the step that was in progress when the checkpoint was taken. The agent
replays from that step. Do NOT leave the index at whatever value it had — the intent is explicit
replay from the in-progress step. Concretely: after writing back the restored `current_plan` to
agent KV, `current_plan["index"]` must equal the index of the step that was executing at
checkpoint time (which is the value already stored in the snapshot; no arithmetic required —
just preserve it rather than advancing it).

**Q3: What is the crash condition for a missing economy checkpoint?**
Decision: Crash whenever `resume_step > 0`. The exact guard is:
```python
if resume_step > 0 and not economy_checkpoint_path:
    raise RuntimeError(...)
```
No tolerance for broken state at any step after step 0. Only when `resume_step == 0` (experiment
crashed before any checkpoint was written) is a fresh economy start acceptable.

**Q4: Does the C++ mobility simulator clock mismatch matter for trip re-submission?**
Decision: Not a concern. The mobility simulator handles trip reconstruction correctly when given
the right checkpoint state. Trust the simulator and move forward. No special handling of
`departure_time` is needed — use the default (current tick).

**Q5: Must the checkpoint INSERT be flushed synchronously?**
Decision: The existing fire-and-forget pattern on `update_experiment_info_checkpoint.remote(...)`
is acceptable. Do not block on the flush. Leave the call site at `simulationengine.py:917`
unchanged.

**Q6: Should ClickHouse writes use INSERT or mutation (ALTER TABLE UPDATE)?**
Decision: Use INSERT (as planned in v2). The INSERT path eliminates the mutation race. This is
confirmed and in scope. The `ALTER TABLE ... UPDATE` call at `clickhouse.py:812-832` is removed
and replaced with a SELECT-then-INSERT.

---

## Implementation Strategy

### Fix 1 — Extend `ExperimentInfoRecord` and replace mutation with INSERT

**Before:**
- `agentsociety/database/schema.py:173-186` — `ExperimentInfoRecord` has 12 fields, none of
  the checkpoint columns.
- `agentsociety/database/clickhouse.py:812-832` — `update_experiment_info_checkpoint()` uses
  `ALTER TABLE experiment_info UPDATE ...`.

**After:**

Step 1a — Extend `ExperimentInfoRecord` at `schema.py:173` to add three new optional fields
using a split TypedDict or `total=False` for the additions:
```python
last_mobility_safe_step: int   # optional, default -1
prev_mobility_safe_step: int   # optional, default -1
economy_checkpoint_path: str   # optional, default ''
```

Step 1b — In `insert_experiment_info_record()` at `clickhouse.py:552`, extend the normalization
block to fill in the three checkpoint columns with defaults if absent:
```python
normalized_record["last_mobility_safe_step"] = record.get("last_mobility_safe_step", -1)
normalized_record["prev_mobility_safe_step"] = record.get("prev_mobility_safe_step", -1)
normalized_record["economy_checkpoint_path"] = record.get("economy_checkpoint_path", "")
```
The `_queue_record` → `_flush_table_batch` path already writes all columns from the dict;
no change to the flush logic is needed.

Step 1c — Replace `update_experiment_info_checkpoint()` at `clickhouse.py:812-832`.

The method must read the current row values for the non-checkpoint columns, then INSERT a new
row with the same non-checkpoint values plus the new checkpoint values. The `ReplacingMergeTree`
will deduplicate on the next FINAL read, preferring the row with the highest `updated_at`.

The method signature stays the same. Internally it will:
1. Read current `experiment_info` row: `SELECT * FROM experiment_info FINAL WHERE id = ...`
2. Build a new `ExperimentInfoRecord` from the read row, overwriting the three checkpoint fields.
3. Call `self.insert_experiment_info_record(new_record)`.

This eliminates the async mutation entirely. The call site at `simulationengine.py:917` remains
fire-and-forget (see Resolved Decisions Q5); no change to the call site.

### Fix 2 — Add `FINAL` to the read query in `fetch_resume_data()`

**Before (`clickhouse.py:623`):**
```python
"FROM experiment_info "
```

**After:**
```python
"FROM experiment_info FINAL "
```

This is now defense-in-depth rather than the primary fix. Once Fix 1 eliminates the mutation race,
`FINAL` is no longer strictly necessary but costs nothing for a startup-time query.

### Fix 3 — Replace teleport-only restore with trip reconstruction

**Before:** `agentsociety/simulation/simulationengine.py:226-259` —
`_restore_external_simulator_state()` does a `reset_person_position` only for agents whose KV
position shows `"aoi_position"`. Agents mid-trip (with `"lane_position"`) are silently skipped.

**After:** The method implements two sequential phases.

**Phase A — Position reset for ALL agents (at AOI and mid-trip alike):**

For every citizen agent in `kv_snapshots`:
- Parse `position` from the KV entry.
- If `"aoi_position"` is present: call `reset_person_position(agent_id, aoi_id=position["aoi_position"]["aoi_id"])`.
- If `"lane_position"` is present: extract `aoi_id` from the `position` dict (the last AOI the
  simulator reported, stored alongside the lane position). Call
  `reset_person_position(agent_id, aoi_id=aoi_id)`. If `aoi_id` cannot be extracted, log a
  WARNING and skip — the agent will re-plan from wherever the simulator places them.

**Phase B — Trip re-submission for agents that were in motion:**

After Phase A, for every citizen agent whose `status` KV value is not SLEEP (not 1) and not
UNSPECIFIED (not 0):
- Read `current_plan` from KV.
- If `current_plan` is non-empty, not `completed`, and not `failed`:
  - `step_index = current_plan["index"]`
  - `current_step = current_plan["steps"][step_index]`
  - Extract `target_aoi_id`: try `current_step.get("evaluation", {}).get("to_place")`, then
    try `current_step.get("to_place")`.
  - If `target_aoi_id` is not None:
    - Call `await environment.set_aoi_schedules(agent_id, [target_aoi_id], modes=[TripMode.TRIP_MODE_DRIVE_ONLY])`
    - Log `f"Agent {agent_id}: trip re-submitted to AOI {target_aoi_id}"` at DEBUG.
    - Increment `reconstructed_count`.
  - If `target_aoi_id` is None: log WARNING, increment `failed_reconstructions`.
    The agent is now at their last known AOI and will re-plan naturally on the next tick.

**Plan index preservation:** The `current_plan["index"]` stored in the KV snapshot already
points to the in-progress step. No modification to the index is needed during reconstruction —
it is preserved as-is when the agent's memory is reloaded from the snapshot. This satisfies the
Resolved Decision Q2 requirement that agents replay from the in-progress step.

**Call site unchanged:** `simulationengine.py:371` calls
`await self._restore_external_simulator_state()`. No change.

**Integration note:** `reset_person_position` must happen before `set_aoi_schedules` so the trip
departs from a valid AOI position. The person must already exist in the simulator (added by
`AgentManager` during `init`).

**Status value mapping from `motion_pb2.pyi:8-29`:**
- `STATUS_UNSPECIFIED = 0`
- `STATUS_SLEEP = 1` — at AOI, no active trip
- `STATUS_DRIVING = 2` — in a vehicle
- `STATUS_WALKING = 3` — on foot
- `STATUS_CROWD = 4` — crowd simulation
- `STATUS_PASSENGER = 5` — transit passenger
- `STATUS_WAIT_ROUTE = 6` — awaiting route calculation
- `STATUS_WAIT_BUS = 7` — waiting for bus
- `STATUS_RAIL_TRANSIT = 8` — on rail
- `STATUS_WAIT_TAXI = 9` — waiting for taxi

All values except 0 and 1 indicate the agent was in motion or waiting for transport; all are
eligible for trip re-submission.

### Fix 4 — Hard crash guards

**Economy crash guard.**

At `simulationengine.py:223-224`, replace:
```python
else:
    get_logger().info("No economy checkpoint path found; economy starts fresh")
```
with:
```python
else:
    if resume_step > 0:
        raise RuntimeError(
            f"Resume at step {resume_step} has no economy checkpoint path. "
            "The economy simulator cannot be restored. "
            "This indicates a checkpoint write failure or incomplete flush. "
            "Cannot continue resume safely — the economy state would be corrupted."
        )
    get_logger().info(
        "No economy checkpoint (resume_step == 0, no checkpoint was ever written); "
        "economy starts fresh. Expected for experiments that crashed before their first safe step."
    )
```

The `resume_step` variable is already read at `simulationengine.py:227` in the existing code.
Pull it up to before the economy branch so it is in scope:
```python
resume_step = self._resume_state.get("last_mobility_safe_step", -1)
```

**Mobility reconstruction crash guard.**

After Phase B of Fix 3, add:
```python
if total_in_motion > 0:
    failure_rate = failed_reconstructions / total_in_motion
    if failure_rate > MOBILITY_RECONSTRUCTION_FAILURE_THRESHOLD:
        raise RuntimeError(
            f"Mobility reconstruction failed for {failed_reconstructions}/{total_in_motion} "
            "in-motion agents. This indicates a corrupt or incomplete KV snapshot. "
            "Cannot continue — simulation state would be inconsistent."
        )
```

`MOBILITY_RECONSTRUCTION_FAILURE_THRESHOLD = 0.5` — module-level constant in
`simulationengine.py`. Crash if more than 50% of in-motion agents cannot have their trip
reconstructed. Individual agent failures (malformed plan dict from an LLM edge case at crash
time) are tolerated; systemic failures are not.

---

## Trade-Offs

**Gained:**
- Mobility resume now works at any simulation step, not just steps where all agents were at AOI.
  This is the fundamental correctness fix.
- Economy inconsistency is surfaced immediately rather than silently corrupting multi-day runs.
- The `INSERT` write eliminates the mutation race without requiring application-level polling.
- `FINAL` on reads becomes defense-in-depth rather than the only line of defense.
- Agents resume from their last known AOI — not home — which minimizes route distortion.

**Sacrificed / risked:**
- **Agents resume at their last known AOI, not their exact mid-road position.** An agent 1.3 km
  along a route to a shopping center will be reset to their last AOI and re-submitted. The route
  will be the same destination but from a different origin. Travel time statistics across resume
  will be inconsistent. This is inherent — the C++ simulator API exposes no mid-trip restore call.
- **Trip departure time is current tick, not original departure time.** Agents arrive later than
  they would have without the crash. No way to specify a backfilled departure time.
- **Agents waiting for transit (STATUS_WAIT_BUS, etc.) are re-submitted as drive-only.** Transit
  modes are already disabled in `MoveBlock._execute_movement()` at `mobility_block.py:690-695`.
  Re-submission uses the same default.
- **INSERT + FINAL is redundant once INSERT is stable.** `FINAL` adds a small in-memory merge
  overhead at read time. For a startup-time query over a single UUID, this is negligible.
- **`update_experiment_info_checkpoint()` now does a read before write.** One additional SELECT
  per checkpoint event. Checkpoints are infrequent (only at mobility-safe steps); negligible cost.
- **Economy crash guard fires on `resume_step > 0` with no economy file.** If the economy
  checkpoint file was written but then deleted externally (e.g., disk cleanup), the resume will
  crash with a clear error rather than silently proceeding. This is the correct behavior.

---

## Rejected Approaches

**Approach: Keep ALTER TABLE UPDATE + fix only FINAL on reads (v1 plan)**
Why rejected: The v1 plan was a minimal fix for Bug 1. The deeper problem is: (a) the "last safe
step" requirement means mobility checkpoints are too infrequent in large simulations; and (b) the
mutation approach is inherently racy. The INSERT approach is the correct long-term fix; v1 is
superseded.

**Approach: Fast-forward agents to their exact mid-trip position**
Why rejected: The mobility C++ simulator gRPC API (`person_service_pb2.pyi`) does not expose any
"set mid-trip route state" call. The only position-setting calls are `ResetPersonPosition` (places
agent at an AOI, stops the trip) and `SetSchedule` (submits a new schedule from current position).
There is no way to say "this agent is currently 1.3km along route X, resume from there."
Implementing this would require changes to the C++ simulator binary, which is out of scope.

**Approach: Reset mid-trip agents to home rather than last known AOI**
Why rejected: The user explicitly chose last known AOI (Resolved Decision Q1). Home reset was
considered as a simpler fallback but increases route distortion unnecessarily when the last known
AOI is available in the position KV entry.

**Approach: Store planned route in KV snapshot for reconstruction**
Why rejected: The route computed by the C++ simulator is not exposed in the gRPC response.
`GetPerson` returns `PersonMotion` fields (position, status, v, direction, activity — no route).
Storing the route would require a separate gRPC call that does not exist.

**Approach: Save mobility state as a separate binary checkpoint (analogous to economy)**
Why rejected: The economy simulator exposes `save(path)` / `load(path)` gRPC calls. The mobility
simulator (`EnvironmentStarter`) does not. Its state is fully in-memory in the C++ binary and is
not serializable via the exposed API.

**Approach: Log a warning instead of crashing for missing economy checkpoint**
Why rejected: The existing behavior already logs at INFO. A warning means users run multi-step
simulations with corrupted economy state without knowing it. The economy state diverges silently
across many simulation steps — this is worse than a clean crash with a clear error message.

**Approach: Crash immediately if any single in-motion agent fails reconstruction**
Why rejected: In large simulations, a single agent may have a malformed `current_plan` due to an
LLM returning truncated JSON at the exact moment of crash. Crashing the resume for thousands of
other agents because of one is disproportionate. The 50% threshold tolerates individual failures
while catching systemic failures.

**Approach: Advance `current_plan["index"]` past the in-progress step on resume**
Why rejected: The user explicitly decided agents should replay from the in-progress step
(Resolved Decision Q2). Advancing the index would skip an unfinished step, leaving the agent
with an incomplete plan and potentially broken state (e.g., a move step that never completed
but is marked as done).

---

## Assumptions

- The `status` field in KV memory is always the integer value of `PersonMotion.Status` (written
  by `update_motion()` at `agent.py:162`). Values: 0=UNSPECIFIED, 1=SLEEP, 2=DRIVING, 3=WALKING,
  etc. from `motion_pb2.pyi:8-29`.
- The `current_plan["steps"][index]["evaluation"]["to_place"]` pattern is populated for steps
  where the block was `MoveBlock` and the trip was successfully submitted. This is set in
  `_execute_movement()` at `mobility_block.py:739-764` where `result["to_place"] = target_place_id`.
- `set_aoi_schedules()` called immediately after `reset_person_position()` will succeed because
  the person is at a valid AOI position. The mobility simulator handles this correctly (Resolved
  Decision Q4).
- ClickHouse `ReplacingMergeTree FINAL` returns the row with the highest `updated_at`, which is
  the most recently inserted row, since all INSERTs use `datetime.now()` for `updated_at`.
- The `position` KV entry for a mid-trip agent includes a resolvable `aoi_id` field. If the
  proto only stores `lane_position` (no `aoi_id`), the agent is skipped with a WARNING. The
  implementer must verify which fields `update_motion()` at `agent.py:162` actually writes for
  the lane-position case — if `aoi_id` is not present, an alternative extraction from the last
  completed plan step must be used.

---

## Code That Could Be Refactored *(informational)*

- `agentsociety/database/clickhouse.py:586-598` — `_query_rows()` does not support `FINAL`.
  A `final: bool = False` parameter that rewrites `FROM table_name` to `FROM table_name FINAL`
  would make this intent explicit and reusable.

- `agentsociety/simulation/simulationengine.py:210-259` — `_restore_external_simulator_state()`
  is doing economy + mobility. Splitting into `_restore_economy_state()` and
  `_restore_mobility_state()` would improve readability as both sections grow with new logic.

- `agentsociety/database/schema.py:173-186` — `ExperimentInfoRecord` uses `total=True` (all
  fields required). The three checkpoint columns added in migration 0013 are not in this TypedDict.
  Making the TypedDict consistent with the actual schema (all 15 columns) would prevent accidental
  omissions and make the INSERT helper robust.

---

## Proposed Next Steps

1. **Fix 1 (INSERT write path):** Extend `ExperimentInfoRecord` in `schema.py:173` to add the
   three checkpoint columns as optional fields. Update `insert_experiment_info_record()` at
   `clickhouse.py:552` to normalize them. Rewrite `update_experiment_info_checkpoint()` at
   `clickhouse.py:812` to do a SELECT-then-INSERT instead of ALTER TABLE UPDATE.

2. **Fix 2 (FINAL on read):** Add `FINAL` to the `FROM experiment_info` clause at
   `clickhouse.py:623`. One-word change.

3. **Fix 4 (economy crash guard):** At `simulationengine.py:227`, pull `resume_step` extraction
   above the economy branch. Replace the `else: get_logger().info(...)` branch with the
   `if resume_step > 0: raise RuntimeError(...)` guard.

4. **Verify `position` KV structure for mid-trip agents:** Before implementing Fix 3, read
   `agent/agent.py:162` and the `PersonMotion` proto to confirm whether `aoi_id` is present
   alongside `lane_position` in the KV entry. If it is not, update Phase A of Fix 3 to extract
   the last AOI from the last completed plan step's `evaluation["to_place"]` instead.

5. **Fix 3 (trip reconstruction):** Rewrite `_restore_external_simulator_state()` at
   `simulationengine.py:210` to implement Phase A (position reset to last known AOI) and Phase B
   (trip re-submission for in-motion agents). Add the `MOBILITY_RECONSTRUCTION_FAILURE_THRESHOLD`
   constant and the crash guard after Phase B.

6. **Verify all four fixes** with a test run:
   - 5 agents, 3 steps, interrupt at a step where agents are mid-trip.
   - Resume. Confirm logs show trip re-submissions, not "No mobility-safe step found."
   - Confirm economy is restored (not "starts fresh").
   - Manually delete the economy checkpoint file and confirm RuntimeError fires.
   - Confirm `resume_step == 0` with no economy file does NOT crash (logs "starts fresh").
