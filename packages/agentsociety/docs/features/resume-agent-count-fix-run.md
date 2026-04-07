# Resume Agent Count Fix — Run Tracking

Plan: `docs/features/resume-agent-count-fix.md`
Test command: `sh tests/run_e2e_tests.sh`

## Steps

- [ ] Change 1 — `infrastructuremanager.py`: Fix `_validate_resume_agent_count` to accept `kv_snapshots` parameter and compare total agents vs snapshot count with backward-compat warning
- [ ] Change 2 — `infrastructuremanager.py`: Fix `_normalize_resume_config` to also pop `logging_level` from top-level and `monitoring_enabled` from env sub-dict
- [ ] Change 3a — `agentmanager.py`: Remove `issubclass(agent_class, CitizenAgentBase)` type guard in `initialize_agents` so all agents restore KV memory from snapshots
- [ ] Change 3b — `agentmanager.py`: Delete the dead `_count_citizen_agents` static method from `AgentManager`
- [ ] Change 4 — `checkpointmanager.py`: Await `db_actor.update_experiment_info_checkpoint.remote(...)` in `save_checkpoint`
- [ ] Change 5a — `base_database.py`: Add `expected_agent_ids: set[int] = set()` parameter to `fetch_resume_data` and pass it to `_fetch_checkpoint_snapshots`
- [ ] Change 5b — `database_actor.py`: Add `expected_agent_ids: set[int] = set()` parameter to `fetch_resume_data` and pass it to the `BaseSimulationDatabase` call
- [ ] Change 6 — `simulationengine.py`: Reorder `init` so `prepare_agents` runs before `load_resume_state`; update `load_resume_state` signature and `_validate_resume_agent_count` call
- [ ] Change 7 — `base_database.py`: Better step-0 error message in `_fetch_checkpoint_snapshots`
