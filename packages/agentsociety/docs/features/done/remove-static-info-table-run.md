# Remove Static Info Table — Run Tracking

Plan: `docs/features/remove-static-info-table.md`
Test command: `sh tests/run_e2e_tests`

## Steps

- [ ] Step 1 — Simplify `Memory.resume_from_snapshots()` (`agentsociety/memory/memory.py`)
  - Remove the `static_updates` parameter and `skip_keys` logic
  - New body calls `await self._status.resume(kv_entries)` directly (no skip_keys)

- [ ] Step 2 — Simplify `prepare_agents()` in `AgentManager` (`agentsociety/simulation/agentmanager.py`)
  - Remove `resume_static_by_agent_id` lookup dict and `_static_record_to_memory_updates()` calls
  - Pass `kv_entries` directly to `resume_from_snapshots()` (now first positional arg)
  - Delete the `_static_record_to_memory_updates()` static method

- [ ] Step 3 — Update `_validate_resume_agent_count()` (`agentsociety/simulation/infrastructuremanager.py`)
  - Replace `len(resume_state["static_records"])` with `len(resume_state.get("kv_snapshots", {}))`
  - Update error message accordingly

- [ ] Step 4 — Strip static queries from `fetch_resume_data()` (`agentsociety/database/base_database.py`)
  - Delete the two query calls for `"latest_static_step"` and `"static_rows"`
  - Remove `"static_step"` and `"static_records"` from the returned dict
  - Remove `_postprocess_static_rows()` call

- [ ] Step 5 — Remove query implementations from both backends
  - `agentsociety/database/duckdb.py` — delete `_postprocess_static_rows()` override and `"latest_static_step"` / `"static_rows"` branches
  - `agentsociety/database/clickhouse.py` — delete same two branches

- [ ] Step 6 — Remove the write path
  - `agentsociety/simulation/agentmanager.py` — delete `save_agent_static_info()` entirely
  - `agentsociety/simulation/simulationengine.py` — remove the call site

- [ ] Step 7 — Remove table registration and schema type
  - `agentsociety/database/base_database.py` — remove `"static_agent_attributes"` entry and `StaticAgentAttributesRecord` import/union entry
  - `agentsociety/database/database_actor.py` — remove `insert_static_agent_attributes_record()` method and import
  - `agentsociety/database/schema.py` — delete `StaticAgentAttributesRecord` TypedDict
