# Checkpoint Resume: Mobility Reconstruction and Economy Crash Guard — Run Tracking

Plan file: `docs/features/checkpoint-mobility-economy-fix.md`

## Steps

### Step 1 — Fix 1 (INSERT write path): Extend `ExperimentInfoRecord` and replace mutation

**1a** `[x]` Extend `ExperimentInfoRecord` in `schema.py` to add three optional checkpoint columns:
`last_mobility_safe_step`, `prev_mobility_safe_step`, `economy_checkpoint_path`.

**1b** `[x]` In `insert_experiment_info_record()` at `clickhouse.py:552`, normalize the three new
checkpoint columns with defaults (`-1`, `-1`, `""`) if absent.

**1c** `[x]` Replace `update_experiment_info_checkpoint()` at `clickhouse.py:812` with a
SELECT-then-INSERT approach (read current row, overwrite checkpoint fields, call
`insert_experiment_info_record()`). Remove the `ALTER TABLE ... UPDATE` call.

---

### Step 2 — Fix 2 (FINAL on read): Add `FINAL` to `fetch_resume_data()` SELECT

`[x]` Add `FINAL` keyword to `FROM experiment_info` in `fetch_resume_data()` at `clickhouse.py:623`.

---

### Step 3 — Fix 4 (economy crash guard): Hard crash when economy checkpoint is missing at resume_step > 0

`[x]` Pull `resume_step` extraction above the economy branch in
`_restore_external_simulator_state()`. Replace `get_logger().info("No economy checkpoint path found")` with a `raise RuntimeError(...)` when `resume_step > 0`.

---

### Step 4 — Verify `position` KV structure for mid-trip agents

`[x]` Read `agent/agent.py` around `update_motion()` and the `PersonMotion` proto to confirm
whether `aoi_id` is present alongside `lane_position` in the KV entry. Document findings in this
file before implementing Fix 3.

Findings:
- `update_motion()` writes all fields from `resp["person"]["motion"]` directly into KV status via `status.update(k, v, mode="replace")`, so the KV `position` value mirrors simulator payloads.
- In `pycityproto` v2 proto stubs (`motion_pb2.pyi` + `geo_pb2.pyi`), `PersonMotion.position` is `geo.Position` with oneof-style branches: `aoi_position` or `lane_position`.
- `LanePosition` only has `lane_id` and `s`; it does **not** include `aoi_id`.
- Conclusion for Fix 3: for mid-trip (`lane_position`) agents, AOI fallback must come from plan history (e.g., last completed/current plan step target), not from `position["aoi_id"]`.

---

### Step 5 — Fix 3 (trip reconstruction): Rewrite `_restore_external_simulator_state()`

`[x]` Implement Phase A (position reset to last known AOI for all citizen agents including mid-trip) and
Phase B (trip re-submission for agents not in SLEEP/UNSPECIFIED status). Enforce
hard crash semantics on any citizen mobility restore failure (no threshold tolerance).

---

## Progress

- [x] Step 1 (Fix 1: INSERT write path)
- [x] Step 2 (Fix 2: FINAL on read)
- [x] Step 3 (Fix 4: economy crash guard)
- [x] Step 4 (Verify position KV structure)
- [x] Step 5 (Fix 3: trip reconstruction)
