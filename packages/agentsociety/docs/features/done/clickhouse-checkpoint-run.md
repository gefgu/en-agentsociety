# ClickHouse Checkpoint and Resume System — Run Tracking

Plan: `docs/features/clickhouse-checkpoint.md`
Branch: `sim/citysim`

## Progress

### Completed

- [x] **Step 1** — Add `ClickHouseConfig` to `EnvConfig` (`configs/env.py`) — committed in early commits
- [x] **Infra/agentmanager cleanup** — `_validate_resume_agent_count` moved to `InfrastructureManager`, monitoring refactor, `_resume_state` check fix — commit `39ac358`
- [x] **Step 2** — Migration SQL files `0009`–`0013` for KV/stream/spatial/message snapshot tables + `experiment_info` checkpoint columns — commit `9b0e83f`
- [x] **Step 3** — TypedDicts in `database/schema.py`: `AgentKVSnapshotRecord`, `AgentStreamSnapshotRecord`, `AgentSpatialSnapshotRecord`, `PendingMessageSnapshotRecord` — commit `80861e2`
- [x] **Step 4** — Write methods in `ClickHouseDatabase` and `DatabaseActor`: `insert_kv_snapshot_batch`, `insert_stream_snapshot_batch`, `insert_spatial_snapshot_batch`, `insert_pending_messages_snapshot`, `update_experiment_info_checkpoint` — commit `7808c79`
- [x] **Step 5** — New event types in `DataRecorder`: `kv_snapshot`, `stream_snapshot`, `spatial_snapshot`, `message_snapshot` with `enqueue_*` methods and `_process_event_once` handlers — commit `5d41c77`
- [x] **Step 6 + 6b** — `_save_checkpoint(day, t)` in `SimulationEngine`: snapshots KV/stream/spatial/pending messages per-step, detects mobility-safe steps, checkpoints economy state — commit `9999353`
- [x] **Step 10** — Guard FINISHED experiments in `load_resume_state()`; strip infra config from `_normalize_resume_config` — commit `fd89732`
- [x] **Steps 7, 8, 8b, 9** — Full resume read path: `fetch_resume_data()` loads snapshots at `last_mobility_safe_step` with N-1 fallback; `initialize_agents()` restores KV/stream/spatial; `_restore_external_simulator_state()` loads economy + resets mobility positions; `_restore_messager_state()` seeds Messager — commit `e6f87e1`

## All Steps Complete

The feature is fully implemented. Validate end-to-end with a small (10-agent) simulation:
1. Run simulation, kill mid-step with SIGKILL
2. Set `env.exp_id` to the original experiment UUID in config
3. Re-run — should resume from `last_mobility_safe_step` with correct agent memory
