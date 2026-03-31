# ClickHouse Checkpoint and Resume System — Run Tracking

Plan: `docs/features/clickhouse-checkpoint.md`
Test command: `ruff check agentsociety/ && ruff format agentsociety/`
Branch: `sim/citysim`

## Progress

### Pre-existing (already committed)
- [x] Step 1 — Add `ClickHouseConfig` to `EnvConfig` (`configs/env.py`) — done in commit eb384fa area; also adds `monitoring_enabled`, `database_enabled` flags and wires config values through `_init_clickhouse_actor()`

### Uncommitted (in working tree, need commit)
- [x] Infra/agentmanager cleanup — `_validate_resume_agent_count` moved to `InfrastructureManager`, `_start_monitoring_services` refactor, `_resume_state` check fix in simulationengine

### Steps remaining
- [ ] Step 2 — Add migration SQL files (0009–0013) for new checkpoint tables + alter experiment_info
- [ ] Step 3 — Add TypedDicts to `database/schema.py`
- [ ] Step 4 — Add write methods to `ClickHouseDatabase` and `DatabaseActor`
- [ ] Step 5 — Add new event types and handlers in `DataRecorder`
- [ ] Step 6 — Hook checkpoint writes into `SimulationEngine.step()` + `_save_checkpoint()`
- [ ] Step 6b — Detect mobility-safe step and checkpoint economy state
- [ ] Step 10 — Mark experiment COMPLETED on clean exit + guard in `load_resume_state()`
- [ ] Step 7 — Extend `fetch_resume_data()` to load new tables
- [ ] Step 8 — Extend `AgentManager.initialize_agents()` resume path (KV/stream/spatial restore)
- [ ] Step 8b — Rehydrate mobility and economy simulators on resume
- [ ] Step 9 — Rehydrate `Messager` pending messages on resume

## Commits
(to be filled as each step is committed)
