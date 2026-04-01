# ClickHouse Checkpoint and Resume System
> Continuously snapshot all simulation state into ClickHouse at every step so that an interrupted simulation can be automatically resumed from the last valid step without manual intervention.

## Purpose & Motivation

The simulation runs for many CPU-hours and is vulnerable to crashes, preemptions, and manual pauses. Today there is no way to resume: the only recoverable state is the agent profile in SQLite/PostgreSQL (static attributes, demographics). Dynamic state — agent memory, in-flight messages, and economic/mobility simulator state — is entirely in-process and lost on restart.

The ClickHouse telemetry pipeline already exists (`database/clickhouse.py`, `database/database_actor.py`). The `DatabaseActor` Ray actor is already fire-and-forget, schema migrations already run at startup, and a partial resume path exists (`fetch_resume_data` at `database/clickhouse.py:540`, used by `infrastructuremanager.py:193`). This feature extends that partial skeleton into a full checkpoint-and-resume system.

The timing is right because: (1) the CitySim fork already diverged enough to own this infrastructure, (2) ClickHouse is already running in the observability stack (`performance/clickhouse/`), and (3) the recent `DataRecorder` refactor (`simulation/datarecorder.py`) established the correct async queue pattern that this work should follow.

## Success Criteria

1. A simulation interrupted at step N restarts cleanly and produces the same outputs as if it had run continuously past step N.
2. Resume requires only changing `env.exp_id` in the config to the UUID of the original experiment; no other manual step is needed.
3. Per-step write latency added to the main simulation loop is zero (fire-and-forget via existing `DatabaseActor` pattern).
4. The ClickHouse schema validator can detect an incomplete checkpoint (missing rows for any active agent at step N) and automatically falls back to step N-1.
5. The `experiment_info.status` column correctly reflects `COMPLETED` when the workflow finishes, preventing re-entry into resume mode.

## Scope

**In scope:**
- New ClickHouse tables for `KVMemory` status snapshots, `StreamMemory` event logs, `SpatialMemory` location beliefs, and in-flight `Messager` pending messages
- Schema migrations (new `.sql` files in `database/migrations/`)
- New TypedDict schemas in `database/schema.py`
- New write methods in `ClickHouseDatabase` and corresponding pass-throughs in `DatabaseActor`
- New `DataRecorder` event types and handlers for the above tables
- Hook in `SimulationEngine.step()` at the existing `_save()` call site (`simulationengine.py:842`) to trigger checkpoint writes
- Extended `fetch_resume_data()` in `ClickHouseDatabase` to load memory snapshot, stream events, spatial beliefs, and pending messages
- `AgentManager.initialize_agents()` resume path to load KV/Stream/Spatial memory from checkpoint instead of defaults
- `Messager` rehydration: inject checkpoint pending messages before the first tick
- Checkpoint integrity validator and N-1 fallback logic in `InfrastructureManager.load_resume_state()`
- Config validation: ensure `experiment_info.status != COMPLETED` before entering resume mode
- Config field for ClickHouse connection in `EnvConfig` (host, port, username, password, database)
- **Mobility-safe step tracking:** at each step, check whether any agent has a `lane_position` in their `position` KV field (mid-trip); record `last_mobility_safe_step` in `experiment_info` whenever all agents are at AOI positions
- **Economy state file checkpoint:** call `economy_client.save()` at every mobility-safe step; file path stored in `experiment_info`; call `economy_client.load()` on resume
- **Mobility simulator resume:** on resume, restart the binary fresh and call `ResetPersonPosition` for each agent using their `aoi_position` from `step_agent_status` at `last_mobility_safe_step` (already persisted per-step in the existing ClickHouse table)
- **Resume step alignment:** all resume queries (KV/Stream/Spatial/Message snapshots) use `last_mobility_safe_step` instead of `max(simulation_step)`

**Out of scope:**
- Restoring in-flight mobility trips (agents mid-trip at crash time are teleported to their last AOI position at `last_mobility_safe_step`; this is a known limitation for now)
- `IndividualEngine` (the task-pipeline engine has no step loop and does not need checkpointing)
- Branching/forking experiments from a checkpoint (possible future feature)
- Encryption of checkpoint data at rest
- Cross-experiment diff or comparison tooling

## Constraints

- Writes must not block the asyncio event loop. The existing `DatabaseActor` (a Ray remote actor receiving fire-and-forget `.remote()` calls) is the correct write path; new writes follow the same pattern.
- Schema changes must be backward-compatible: existing experiments that never wrote checkpoint tables must still load normally.
- ClickHouse is already a hard dependency for telemetry; this feature consolidates it as a hard dependency for resume. The `db_actor` being `None` (ClickHouse unavailable) means checkpoint writes silently no-op, which is acceptable in that mode.
- The `KVMemory._data` dict values can be arbitrary Python objects (dicts, lists, floats, strings). Serialization must use JSON (all existing values in `SocietyAgent` are JSON-safe: see `cityagent/memory_config.py`).
- `StreamMemory` has a `deque(maxlen=1000)` at `memory/memory.py:312`. The checkpoint only needs to store the live window, not reconstruct the full historical log.
- `SpatialMemory._locations` is a `dict[str, SpatialMemoryNode]` where each node has five floats (`price`, `atmosphere`, `satisfaction`, `convenience`, `uncertainty`). This is compact and trivially serializable.
- The `Messager` pending message queue is in-process (`message/messager.py:72-73`). Messages are Pydantic `Message` objects with a `.model_dump()` method.

## Architecture & Integration Points

### Existing write path (fire-and-forget)
- `simulationengine.py:842` — `await self._save(day, t)` is the per-step status save; this is where the checkpoint write hook belongs
- `simulation/datarecorder.py:86-87` — `enqueue_clickhouse_status()` demonstrates the pattern: enqueue an event, the background worker calls `self._db_actor.insert_X.remote(...)` fire-and-forget
- `database/database_actor.py:11` — `@ray.remote class DatabaseActor` is the async sink; all new insert methods are added here
- `database/clickhouse.py:246` — `_queue_record()` / `_flush_table_batch()` handles batching and flushing; new tables register in `table_schemas` dict at `clickhouse.py:75`
- `database/migrations/` — SQL migration files, numbered sequentially; `_create_tables()` at `clickhouse.py:152` runs all of them in order at startup

### Existing resume path (read path)
- `configs/env.py:29` — `EnvConfig.exp_id: Optional[str]` — set this to resume from a prior experiment
- `simulationengine.py:67-69` — if `configured_resume_exp_id` is set, it is used as `self.exp_id`
- `infrastructuremanager.py:193` — `load_resume_state()` calls `db_actor.fetch_resume_data.remote()` and validates config hash
- `database/clickhouse.py:540` — `fetch_resume_data()` queries `experiment_info`, `step_agent_status`, `static_agent_attributes`; returns `{source_exp_id, config, latest_experiment_info, latest_step, static_step, static_records}`
- `simulationengine.py:169` — `_restore_resume_runtime_state()` restores `_total_steps`, `cur_day`, `cur_t`, token counts, and the environment tick
- `agentmanager.py:578` — `initialize_agents()` receives `resume_state` and calls `_static_record_to_memory_updates()` to preload static KV fields from ClickHouse rows

### Memory serialization surface
- `memory/memory.py:249` — `KVMemory.export(keys)` returns `dict[str, Any]` — this is the read surface for checkpoint writes
- `memory/memory.py:148` — `KVMemory.update(key, value, mode)` is the write surface for restore
- `memory/memory.py:556` — `StreamMemory.get_all()` returns `list[dict]` with keys `{id, cognition_id, topic, location, description, day, t}` — this is the exact serialization surface for stream memory
- `memory/memory.py:318` — `StreamMemory.add()` is the restore write surface (requires `_environment` to be initialized first; day/t come from environment)
- `memory/memory.py:596-660` — `SpatialMemory._locations: dict[str, SpatialMemoryNode]` with fields `{location_id, description, price, atmosphere, satisfaction, convenience, uncertainty}`

### Messager pending queue
- `message/messager.py:72` — `self._pending_messages: list[Message]` — the in-flight messages to serialize
- `message/messager.py:103` — `fetch_pending_messages()` drains the queue (used at `simulationengine.py:853`); checkpoint must capture the queue _before_ this drain
- `message/messager.py:115` — `set_received_messages()` is the corresponding restore write surface

### Mobility-safe step detection
- `simulation/datarecorder.py:120-127` — `save_statuses()` already reads `position["aoi_position"]` vs `position["lane_position"]` for every agent at every step. An agent with `lane_position` is mid-trip (on a road); an agent with `aoi_position` is stationary at a location.
- A mobility-safe step is any step where **all** active agents have `aoi_position`. This check requires no additional gRPC calls — the data is already in `memory.status["position"]`.
- `last_mobility_safe_step` will be stored as a new column on `experiment_info` (updated each time a safe step is detected, fire-and-forget via `DatabaseActor`).
- **Proto confirmation** (from `cityproto/v2` at `go/pkg/mod/github.com/tsinghua-fib-lab/cityproto/v2@v2.0.7/pycityproto/city/person/v2/motion_pb2.py`): `PersonMotion.status` is a `Status` enum with `STATUS_SLEEP=1` (at AOI, not moving), `STATUS_DRIVING=2`, `STATUS_WALKING=3`, `STATUS_CROWD=4`, `STATUS_PASSENGER=5`, `STATUS_WAIT_ROUTE=6`, `STATUS_WAIT_BUS=7`, `STATUS_RAIL_TRANSIT=8`, `STATUS_WAIT_TAXI=9`. Any status other than `STATUS_SLEEP` and `STATUS_UNSPECIFIED` (0) means the agent is in transit. This is the ground truth from the simulator; the Python-side `aoi_position`/`lane_position` distinction in KV memory is the proxy. If the proxy is ever found unreliable, fall back to calling `GetPerson` on all agents and checking `motion.status == STATUS_SLEEP`.

### Economy simulator checkpoint
- `environment/economy/econ_client.py` — `save(file_path)` calls `SaveEconomyEntities` RPC; the binary writes all economic entity state to a file on the local filesystem.
- `load(file_path)` calls `LoadEconomyEntities` RPC to restore that state.
- Economy checkpoint files will be named `econ_step_{step_number}_{exp_id}.bin` and stored in a configurable local directory (default: `~/.agentsociety/checkpoints/{exp_id}/`). The path of the latest valid economy checkpoint file is stored as a new column `economy_checkpoint_path` on `experiment_info`.
- Economy `save()` is called only at mobility-safe steps (aligned with `last_mobility_safe_step`), since there is no value in saving economy state at a step we cannot resume mobility from.

### Mobility simulator resume
- The mobility binary (`agentsociety-sim-oss`) has no native snapshot/restore API.
- On resume: restart the binary fresh (existing `EnvironmentStarter.init()` path), then for each agent call `environment.city_client.person_service.ResetPersonPosition` with the agent's `aoi_position` at `last_mobility_safe_step` (already available in `step_agent_status` in ClickHouse).
- In-flight trips at crash time are dropped — the agent is teleported to their last safe AOI position. This is the intentional, documented limitation of this approach.

### Step loop anatomy (the write hook location)
```
SimulationEngine.step()  [simulationengine.py:741]
  ├─ _message_dispatch()                            [line 780]
  ├─ _agent_manager.run_all_agents()                [line 783]
  ├─ _save_exp_info()                               [line 829]
  ├─ _save(day, t)          ← status + ClickHouse   [line 842]
  ├─ _save_global_prompt()                          [line 844]
  ├─ messager.fetch_pending_messages()              [line 853]  ← drain happens HERE
  ├─ messager.set_received_messages(all_messages)   [line 884]
  └─ _flush_data_recorder()                         [line 934]
```
The message queue must be snapshotted **before** `fetch_pending_messages()` at line 853, and the checkpoint flush must happen **before** `_flush_data_recorder()` at line 934.

## Similar Patterns & Reuse

- **`DataRecorder._enqueue()` / event queue pattern** — `simulation/datarecorder.py:298` — `async def _enqueue(event)` — the background asyncio queue that decouples writes from the step loop. New checkpoint events (`"kv_snapshot"`, `"stream_snapshot"`, `"spatial_snapshot"`, `"message_snapshot"`) should be added as new `RecorderEventType` literals at `datarecorder.py:21` and handled in `_process_event_once()` at `datarecorder.py:353`.

- **`_queue_record()` + `table_schemas` registration** — `database/clickhouse.py:75` / `database/clickhouse.py:246` — the existing pattern for registering a table and queueing records. New tables follow this exactly: add to `table_schemas`, add column list to `table_columns`, add a `TableBatchState` entry in `table_batches`, write an `insert_X()` method.

- **`StreamMemory.get_all()`** — `memory/memory.py:556` — already returns a serialization-ready `list[dict]`. No new export method needed.

- **`KVMemory.export(keys)`** — `memory/memory.py:249` — already serializes a subset of keys. For checkpoint purposes, pass all keys (the `_data` dict keys).

- **SQL migration file pattern** — `database/migrations/0001_create_adjust_needs_table.sql` through `0008_create_experiment_info_table.sql` — numbered `.sql` files; `_create_tables()` at `clickhouse.py:152` auto-discovers and applies them in sorted order.

- **`fetch_resume_data()` query structure** — `database/clickhouse.py:540-621` — shows the correct pattern for querying the latest step's data using `max(simulation_step)` then a WHERE clause on that step. New queries follow the same two-query pattern.

- **`_static_record_to_memory_updates()`** — `agentmanager.py:168` — shows how a flat ClickHouse row is converted into nested memory key-value updates. The KV snapshot restore follows this same pattern.

## Implementation Strategy

### Step 1 — Extend the Config to expose ClickHouse connection settings

**Before:** `ClickHouseDatabase.__init__()` (`database/clickhouse.py:45`) hard-codes defaults (`host="localhost"`, `password="clickhouse"`, `database="fastsociety"`). These are passed through `InfrastructureManager._init_clickhouse_actor()` at `infrastructuremanager.py:286` with no config fields.

**After:** Add a `ClickHouseConfig` Pydantic model to `configs/env.py` (alongside `DatabaseConfig`). Add it as an optional field to `EnvConfig`. `_init_clickhouse_actor()` passes config values through to `DatabaseActor.remote()`. This is a non-breaking change since all fields have defaults.

### Step 2 — Add new ClickHouse tables and alter `experiment_info` via migration files

New files in `database/migrations/`:
- `0009_create_agent_kv_snapshot.sql` — `(exp_id, simulation_step, agent_id, key, value_json)` using `MergeTree ORDER BY (exp_id, simulation_step, agent_id, key)`. This table stores one row per KV key per agent per step. Use `CODEC(ZSTD(3))` on `value_json`.
- `0010_create_agent_stream_snapshot.sql` — `(exp_id, simulation_step, agent_id, memory_id, cognition_id Nullable, topic, location, description, day, t)`. One row per stream memory node per agent per step.
- `0011_create_agent_spatial_snapshot.sql` — `(exp_id, simulation_step, agent_id, location_id, description, price, atmosphere, satisfaction, convenience, uncertainty)`. One row per known location per agent per step.
- `0012_create_pending_messages_snapshot.sql` — `(exp_id, simulation_step, from_id Nullable, to_id Nullable, day, t, kind, payload_json, created_at, extra_json Nullable)`. One row per in-flight message per step.
- `0013_alter_experiment_info_checkpoint_cols.sql` — `ALTER TABLE experiment_info ADD COLUMN IF NOT EXISTS last_mobility_safe_step Int32 DEFAULT -1`, `ADD COLUMN IF NOT EXISTS prev_mobility_safe_step Int32 DEFAULT -1`, `ADD COLUMN IF NOT EXISTS economy_checkpoint_path String DEFAULT ''`. ClickHouse `ALTER TABLE ADD COLUMN` is non-destructive and backward-compatible.

All new tables use `PARTITION BY exp_id`.

### Step 3 — Add TypedDicts to `database/schema.py`

Add `AgentKVSnapshotRecord`, `AgentStreamSnapshotRecord`, `AgentSpatialSnapshotRecord`, `PendingMessageSnapshotRecord` to `database/schema.py`. Follow the exact structure of existing TypedDicts like `StepAgentStatusRecord` at `schema.py:49`.

### Step 4 — Add write methods to `ClickHouseDatabase` and `DatabaseActor`

**In `ClickHouseDatabase`:**
- Register the four new tables in `table_schemas` at `clickhouse.py:75` and `table_columns` at `clickhouse.py:86`
- Add `insert_kv_snapshot_batch()`, `insert_stream_snapshot_batch()`, `insert_spatial_snapshot_batch()`, `insert_pending_messages_snapshot()` — each follows the `_queue_record()` pattern

**In `DatabaseActor`:**
- Mirror all four methods as Ray-remote pass-throughs (same pattern as `insert_step_agent_status_record` at `database_actor.py:91`)

### Step 5 — Add new event types and handlers in `DataRecorder`

**Before:** `RecorderEventType` at `datarecorder.py:21` has 7 literals.

**After:** Add `"kv_snapshot"`, `"stream_snapshot"`, `"spatial_snapshot"`, `"message_snapshot"` as new literals. Add four `enqueue_*` methods. Add handling in `_process_event_once()` at `datarecorder.py:353` for each new type — each calls the corresponding `self._db_actor.insert_X_batch.remote(...)` fire-and-forget.

### Step 6 — Hook checkpoint writes into `SimulationEngine.step()`

**Before:** `simulationengine.py:842` calls `await self._save(day, t)` which writes `StorageStatus` rows and `StepAgentStatusRecord` rows. The message queue is not captured.

**After:** Add a `_save_checkpoint(day, t)` method to `SimulationEngine` that:
1. Iterates `self._agent_manager.agents`; for each agent calls `KVMemory.export(list(agent.status._data.keys()))` and `StreamMemory.get_all()` and `SpatialMemory._locations` (direct attribute read)
2. Enqueues batched `kv_snapshot`, `stream_snapshot`, `spatial_snapshot` events via `self._data_recorder.enqueue_*`
3. Reads `self._messager._pending_messages` (snapshot, not drain) and enqueues a `message_snapshot` event

Call `await self._save_checkpoint(day, t)` just before `await messager.fetch_pending_messages()` at line 853.

**Note on accessing `_data`:** `KVMemory._data` is a private dict with no lock-free read. The step loop is single-threaded (agents run sequentially within a tick), so reading `_data` directly after `run_all_agents()` completes is safe. Alternatively, expose a `KVMemory.export_all()` convenience method that calls `export(list(self._data.keys()))`.

### Step 6b — Detect mobility-safe step and checkpoint economy state

Within `_save_checkpoint(day, t)` (or as a separate `_update_mobility_safe_step()` call immediately after), add:
1. Iterate all agents; read `agent.status.get("position")` (already fetched in step 6 above)
2. Check if any agent has `"lane_position"` in their position dict — if so, this step is **not** mobility-safe, skip economy checkpoint
3. If all agents have `"aoi_position"` (or no position at all, for institution agents), this step **is** mobility-safe:
   a. Call `await self.environment.economy_client.save(f"{checkpoint_dir}/econ_step_{step}.bin")` — fire-and-forget is fine since the binary handles the write
   b. Fire-and-forget update `experiment_info.last_mobility_safe_step = step` and `experiment_info.economy_checkpoint_path = <path>` via `DatabaseActor`

The `checkpoint_dir` defaults to `~/.agentsociety/checkpoints/{exp_id}/` and is a new field in `EnvConfig` (or derived from it).

### Step 7 — Extend `fetch_resume_data()` to load the new tables

**Before:** `database/clickhouse.py:540` queries `experiment_info`, `step_agent_status` (for latest step), and `static_agent_attributes`.

**After:** Add queries to `fetch_resume_data()`:
1. Read `last_mobility_safe_step` and `economy_checkpoint_path` from `experiment_info` — this is the canonical resume step (not `max(simulation_step)`)
2. Query `agent_kv_snapshot WHERE simulation_step = last_mobility_safe_step` — grouped by `agent_id`
3. Query `agent_stream_snapshot WHERE simulation_step = last_mobility_safe_step`
4. Query `agent_spatial_snapshot WHERE simulation_step = last_mobility_safe_step`
5. Query `pending_messages_snapshot WHERE simulation_step = last_mobility_safe_step`

Return these in the `resume_data` dict alongside existing keys.

**Integrity validation (N-1 fallback):** Because `last_mobility_safe_step` is written fire-and-forget, a crash could leave it pointing to a step whose KV snapshot was never completed. The validator checks that the set of `agent_id` values in `agent_kv_snapshot` at `last_mobility_safe_step` equals the full set of expected agent IDs (from `static_agent_attributes`). If any agent is missing, the previous mobility-safe step must be used. Since we only know the previous value if it was stored, add a `prev_mobility_safe_step` column to `experiment_info` (written before overwriting `last_mobility_safe_step`). The fallback uses `prev_mobility_safe_step`. If that also fails, raise a `ValueError`. This logic lives in `InfrastructureManager.load_resume_state()` at `infrastructuremanager.py:193`.

### Step 8 — Extend `AgentManager.initialize_agents()` resume path

**Before:** `agentmanager.py:626-635` — when `resume_state` is not `None`, applies only `static_record_to_memory_updates` (demographics). Dynamic memory starts from defaults.

**After:** After applying static updates, check if `resume_state["kv_snapshots"]` contains an entry for `agent_id`. If so:
1. For each `(key, value_json)` in the KV snapshot, call `await memory_init.status.update(key, json.loads(value_json), mode="replace")`
2. Skip keys that are in `static_keys` (already applied above) to avoid double-update
3. For stream memory: reconstruct `MemoryNode` objects from `resume_state["stream_snapshots"][agent_id]` and directly `append()` them to `memory_init.stream._memories`. Re-add their embeddings via `memory_init.stream._vectorstore.add_documents()`.
4. For spatial memory: reconstruct `SpatialMemoryNode` objects from `resume_state["spatial_snapshots"][agent_id]` and write them to `memory_init.spatial._locations`.

Stream embedding reconstruction is expensive. An optimization: rebuild embeddings from descriptions in a batch after all agents are initialized (similar to how `initialize_embeddings()` is already called at `agentmanager.py:707`).

### Step 8b — Rehydrate mobility and economy simulators on resume

This step runs inside `SimulationEngine._restore_resume_runtime_state()` or a new `_restore_external_simulator_state()` method called after the environment is started.

**Economy simulator:**
1. Read `economy_checkpoint_path` from `resume_data`
2. Call `await self.environment.economy_client.load(economy_checkpoint_path)` — restores all economic entities to their state at `last_mobility_safe_step`

**Mobility simulator:**
1. The binary was started fresh by `EnvironmentStarter.init()` (existing path)
2. For each citizen agent (not institution agents), read their `aoi_position` from `step_agent_status` at `last_mobility_safe_step` (already fetched in the existing `fetch_resume_data()` path as part of `static_records` — the `aoi_id` field is already stored)
3. Call `await self.environment.city_client.person_service.ResetPersonPosition({"person_id": agent_id, "position": {"aoi_position": {"aoi_id": last_aoi_id}}})` for each agent
4. Log clearly that in-flight trips at crash time were dropped and agents were repositioned to `last_mobility_safe_step`

**Note:** The `aoi_id` at `last_mobility_safe_step` is available from two sources: (a) the `step_agent_status` ClickHouse table (which stores `parent_id` = aoi_id when `aoi_position` is set), or (b) the `agent_kv_snapshot` table (which stores the full `position` JSON). Use `step_agent_status` since it's already queried.

### Step 9 — Rehydrate `Messager` pending messages

**Before:** `simulationengine.py:884` — `messager.set_received_messages(all_messages)` sets messages from the previous tick.

**After:** In `SimulationEngine._restore_resume_runtime_state()` at `simulationengine.py:169`, if `resume_state["pending_messages"]` is non-empty, deserialize each row as a `Message` Pydantic object and call `await self._messager.send_message(msg)` for each. This seeds the pending queue before the first tick runs, so messages are not silently dropped.

### Step 10 — Mark experiment COMPLETED on clean exit

**Before:** `ExperimentStatus.RUNNING` is written each tick (`simulationengine.py:823`). There is no code that writes `COMPLETED`.

**After:** In `SimulationEngine.run()` at `simulationengine.py:982`, after the workflow loop completes normally, set `self._exp_info.status = ExperimentStatus.COMPLETED.value` and call `await self._save_exp_info()`. In `InfrastructureManager.load_resume_state()`, after loading `experiment_info`, check `status == COMPLETED` and raise a clear `ValueError("Cannot resume a COMPLETED experiment")`. This prevents accidentally re-running a finished simulation.

## Trade-Offs

**Gained:**
- Full durability: crash recovery without losing agent cognitive state built over many simulation hours
- Unified sink: analytics + performance + checkpoint all go through the same ClickHouse actor
- No blocking: fire-and-forget writes mean zero wall-clock impact on the step loop

**Sacrificed / risked:**
- Storage volume: at each step, every agent's full KV memory (approximately 50 keys × agents), all stream memory entries (up to 1000 per agent), and all spatial beliefs are written. For 1000 agents, a 1000-node stream window, this is roughly 50M + 1B + Nspatial rows per full run. ClickHouse columnar compression (ZSTD) partially mitigates this, but storage cost is real. The PRD states terabyte-scale is acceptable.
- Stream embedding rebuilding on resume is CPU-intensive: reconstructing BM25 embeddings for up to 1000 × N_agents documents. This happens once at resume time and is bounded by the existing `initialize_embeddings()` code path.
- External simulator state (mobility + economy) is NOT captured. An agent resumed at step N will have the correct memory but the traffic/economy simulation starts fresh. The magnitude of this inconsistency depends on how much state diverges in one step — see Open Questions.
- The N-1 fallback silently skips one step of progress. For long runs, this is acceptable, but it should be logged clearly.

## Rejected Approaches

**Approach: Serialize memory to JSON files on disk (e.g., in `home_dir`)**
Why rejected: Breaks the "unified data layer" objective, requires bespoke file lifecycle management, is not queryable for analytics, does not reuse the existing ClickHouse actor, and introduces filesystem coupling that the rest of the codebase avoids.

**Approach: Store full pickled Ray actor state via `ray.get_actor()` / `ray.kill()` + snapshot**
Why rejected: Ray does not provide a general checkpoint/restore API for actors. Pickling agent state is fragile across library version changes. The actor-level approach would also require changes to the architecture (remote actor vs. in-process agent), which is a major refactor.

**Approach: Use PostgreSQL (the existing `DatabaseWriter`) for checkpoint tables**
Why rejected: The existing `DatabaseWriter` writes via SQLAlchemy to SQLite or PostgreSQL. Per-step per-agent KV snapshots at scale (1000 agents × 50 keys × many steps) would create a very large append-only table in a row-store database. PostgreSQL is not optimized for this write pattern or for the `argMax()`-style latest-state queries needed for resume. ClickHouse is already present and purpose-built for this.

**Approach: Write KV memory as a single JSON blob per agent per step rather than one row per key**
Why rejected: A JSON blob is opaque to ClickHouse queries. Storing individual keys allows future analytics (e.g., "how did `hunger_satisfaction` evolve across agents?") and allows targeted resume queries (fetch only the keys that changed). The per-key design also allows future partial checkpointing if only specific keys need recovery.

**Approach: Checkpoint only at day boundaries, not every step**
Why rejected: The PRD explicitly requires every step. Day-boundary checkpoints mean up to 24+ hours of re-simulation after a crash, which defeats the purpose.

**Approach: Add a `SpatialMemory.export_all()` method and checkpoint only keys that changed (delta checkpoint)**
Why rejected: Delta checkpointing requires tracking dirty flags on each key, which adds complexity to the hot path in `KVMemory.update()`. Given ClickHouse's columnar compression, full snapshots are almost as storage-efficient as deltas for the value types used (mostly floats and short strings). A future optimization can add dirty tracking if storage pressure warrants it.

## Assumptions & Open Questions

**Assumptions:**
- All values in `KVMemory._data` for `SocietyAgent` (citizen, firm, bank, government, NBS) are JSON-serializable. This is true today for all values in `cityagent/memory_config.py` (dicts of floats, strings, lists of strings, ints). If a custom agent stores a non-serializable value, the checkpoint will raise a `json.JSONEncodeError` which will be caught and logged but will not crash the simulation.
- The `Messager` pending queue is always small (tens of messages per tick, not thousands). No special chunking is needed.
- `MemoryNode.cognition_id` back-references are safe to serialize as integers; the referenced node will also be in the stream window and will be restored.

**Resolved questions:**

1. ~~External mobility simulator state~~ — **RESOLVED.** The mobility binary has no snapshot API. Resume strategy: detect "mobility-safe steps" using the Python-side `position` KV field (agents at `aoi_position` = stationary, agents at `lane_position` = mid-trip). At a safe step, all agents are at known AOI locations. On resume, restart the binary fresh and call `ResetPersonPosition` per agent to restore their last-safe-step AOI. In-flight trips at crash time are intentionally dropped. This requires no new gRPC API surface.

2. ~~External economy simulator state~~ — **RESOLVED.** `econ_client.py` already exposes `save(file_path)` → `SaveEconomyEntities` RPC and `load(file_path)` → `LoadEconomyEntities` RPC. These do a full binary state dump/restore on the simulator host. Economy checkpoints are written at each mobility-safe step and their paths stored in `experiment_info.economy_checkpoint_path`.

3. ~~`StreamMemory` embedding reconstruction cost~~ — **RESOLVED.** Always reconstruct all stream memory embeddings on resume; add a progress indicator (e.g., `tqdm` or logged progress via `get_logger()`) to the `initialize_embeddings()` call path during resume. Reconstruction is cheaper than restarting the simulation from scratch, so no skip/partial-restore optimization is needed.

4. ~~`SpatialMemory` on resume vs. re-initialization~~ — **RESOLVED.** Restore all known locations. In practice spatial memory stays small (fewer than ~10 locations per agent over a typical run), so there is no performance concern.

5. ~~ClickHouse availability as a hard vs. soft dependency~~ — **RESOLVED.** When `env.exp_id` is set (resume mode) and `db_actor` is `None` (ClickHouse unavailable), raise a fatal `RuntimeError` immediately. No silent degradation. Normal runs without `exp_id` continue to treat ClickHouse as optional.

6. ~~Config hash comparison during resume~~ — **RESOLVED.** Resume validation should compare only `exp.id` (the experiment UUID). Strip all observability/infrastructure config from the comparison (Prometheus settings, ClickHouse connection params, S3 credentials, log levels, etc.). Only changes to simulation-semantic config (agent definitions, workflow steps, map, economy params) should block resume. Update `_normalize_resume_config()` at `infrastructuremanager.py:138` to strip the entire `env.db`, `env.clickhouse`, `env.s3`, and `exp.logging` subtrees before hashing.

## Code That Could Be Refactored *(informational)*

- `database/clickhouse.py:75-98` — The `table_schemas`, `table_columns`, and `table_batches` dicts are manually kept in sync. Adding a new table requires touching three places. A helper method or a `@dataclass` descriptor for table registration would reduce the error surface.

- `agentmanager.py:167` — `_static_record_to_memory_updates()` is a long flat function mapping 30+ ClickHouse column names to nested dict keys. The inverse (memory → ClickHouse record) in `save_agent_static_info()` at `agentmanager.py:856` is equally long. These could be replaced by a declarative field mapping, similar to how the Pydantic models in `storage/type.py` define their fields.

- `simulationengine.py:697-716` — `_save()` and `_save_checkpoint()` (proposed) will be adjacent; they could be merged into a single `_persist_step_state()` method that handles both analytics writes and checkpoint writes, making the step loop easier to reason about.

- `database/database_actor.py` — The `DatabaseActor` is a thin pass-through wrapper around `ClickHouseDatabase`. Each new insert method requires an identical duplicate in both files. A code generation step or a metaclass could eliminate this duplication.

- `simulationengine.py:169` — `_restore_resume_runtime_state()` accesses `self._resume_state` directly rather than receiving it as a parameter. Adding the new memory restoration logic here would make this method very long. The message rehydration (step 9 above) could instead live in a dedicated `_restore_messager_state()` private method.

## Proposed Next Steps

1. **Step 1 — Add `ClickHouseConfig` to `EnvConfig`** (`configs/env.py`). This is a pure additive config change with no behavior change; it unblocks everything that follows.

3. **Steps 2 and 3 — Write migration SQL files and TypedDicts.** Four new migrations (`0009`–`0012`) and four new TypedDicts in `database/schema.py`. This is purely additive and does not break existing tests.

4. **Step 4 — Add write methods to `ClickHouseDatabase` and `DatabaseActor`.** Register new tables in `table_schemas`, add `insert_*_batch()` methods. Still no behavior change in the step loop.

5. **Step 5 — Add event types and handlers in `DataRecorder`.** Add `"kv_snapshot"`, `"stream_snapshot"`, `"spatial_snapshot"`, `"message_snapshot"` event types and their `_process_event_once()` handlers.

6. **Step 6 — Hook checkpoint writes in `SimulationEngine.step()`.** Add `_save_checkpoint()` and call it before `fetch_pending_messages()`. At this point, new experiments start writing checkpoint data.

7. **Step 10 — Mark experiment COMPLETED.** Add the status write in `run()` and the guard in `load_resume_state()`. This prevents broken resume attempts before the read path is ready.

8. **Steps 7, 8, 9 — Implement the full resume read path.** Extend `fetch_resume_data()`, extend `initialize_agents()` to load KV/stream/spatial, extend `_restore_resume_runtime_state()` to seed the Messager. This is the most complex step and should be validated end-to-end with a small (10-agent) example simulation.

9. **Validate N-1 fallback** by running a simulation, sending SIGKILL mid-step, and verifying that resume lands cleanly at the last complete step.
