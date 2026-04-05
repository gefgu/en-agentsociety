# Remove Static Info Table
> Remove the `static_agent_attributes` ClickHouse table and all code that writes and reads it; rely exclusively on the `agent_kv_snapshot` table for resume.

## Purpose & Motivation

During simulation init, citizen agent attributes are saved twice: once as a flattened, schema-bound row in `static_agent_attributes`, and once as generic key-value pairs in `agent_kv_snapshot`. On resume, the code reads both tables and merges them, giving static attributes priority over the KV snapshot for keys they share.

The KV snapshot already contains every key that the static table stores — it is a full dump of `agent.status` (i.e., `KVMemory`). The static table adds no information that the KV snapshot does not already provide. Removing it simplifies the write path, the resume path, the schema, and the validation logic.

## Success Criteria

- The simulation writes no records to `static_agent_attributes`.
- Resume works correctly: all citizen agent attributes are restored from the KV snapshot alone.
- The validation in `infrastructuremanager.py` that counted static records to confirm agent count is replaced by an equivalent check against the KV snapshot.
- The `static_agent_attributes` table definition, schema type, and all query strings that reference it are deleted.
- All existing tests pass with `sh tests/run_e2e_tests`.

## Scope

**In scope:**
- Delete the write path: `AgentManager.save_agent_static_info()` and its call site.
- Delete the read path from `fetch_resume_data` in both `DuckDBDatabase` and `ClickHouseDatabase`.
- Remove `StaticAgentAttributesRecord` from `schema.py` and all imports.
- Remove the `static_agent_attributes` entry from the table registry in `base_database.py`.
- Remove the `_postprocess_static_rows` override in `duckdb.py`.
- Remove `_static_record_to_memory_updates()` from `AgentManager`.
- Simplify `Memory.resume_from_snapshots()` to drop the `static_updates` argument; call `self._status.resume(kv_entries)` directly.
- Replace the `static_records`-based agent-count check in `InfrastructureManager._validate_resume_agent_count()` with a count derived from the KV snapshot.
- Remove `static_step` and `static_records` keys from the dict returned by `fetch_resume_data`.

**Out of scope:**
- The `agent_profile` SQLite/PostgreSQL table (`storage/model.py:agent_profile`) — this is a separate, unrelated table used by the web UI to display profiles. It is written by `DatabaseWriter.write_profiles()` and read by web API routes. It is not the same system.
- Any changes to the KV snapshot format or frequency.
- Any changes to the stream, spatial, or pending-messages snapshots.

## Constraints

- No external consumers of `static_agent_attributes` are known within this repository. Verify before merging if there are downstream consumers (dashboards, analytics scripts) that query this table by name.
- The agent-count validation logic must be preserved — only its data source changes.

## Architecture & Integration Points

### Write path (to be removed)

`agentsociety/simulation/simulationengine.py:608–613` — `_setup_agents()` calls `self._agent_manager.save_agent_static_info(self._total_steps)` only when `self._resume_state is None`.

`agentsociety/simulation/agentmanager.py:839–988` — `save_agent_static_info(step)` iterates all `CitizenAgentBase` agents, exports `static`-class keys from `agent.status`, constructs a `StaticAgentAttributesRecord`, and calls `self._db_actor.insert_static_agent_attributes_record.remote(record=record)`.

`agentsociety/database/database_actor.py:215–219` — `insert_static_agent_attributes_record()` forwards the record to `self._db.insert_record("static_agent_attributes", record)`.

`agentsociety/database/base_database.py:85` — `"static_agent_attributes": StaticAgentAttributesRecord` in the table registry.

### Read path (to be removed)

`agentsociety/database/base_database.py:441–457` — `fetch_resume_data()` calls `_run_resume_query("latest_static_step")` then `_run_resume_query("static_rows")`, then calls `_postprocess_static_rows()`.

`agentsociety/database/duckdb.py:308–334` — `_resume_query()` implementations for `"latest_static_step"` and `"static_rows"` against `static_agent_attributes`.

`agentsociety/database/clickhouse.py:259–288` — Same two query implementations for ClickHouse.

`agentsociety/database/duckdb.py:271–276` — `_postprocess_static_rows()` override that JSON-decodes the `hobbies` array field.

`agentsociety/database/base_database.py:482–494` — `fetch_resume_data()` return dict includes keys `"static_step"` and `"static_records"`.

### Resume consumer (to be simplified)

`agentsociety/simulation/agentmanager.py:572–618` — `prepare_agents()` builds `resume_static_by_agent_id` from `resume_state["static_records"]`, then for each citizen agent calls `_static_record_to_memory_updates(static_record)` and passes the result as `static_updates` to `memory_init.resume_from_snapshots()`.

`agentsociety/simulation/agentmanager.py:140–192` — `_static_record_to_memory_updates()` — the mapping function that translates flat DB columns back into the nested memory dict format. This is entirely replaced by the KV snapshot: the KV entries already carry these keys in their native nested form.

`agentsociety/memory/memory.py:162–178` — `resume_from_snapshots(static_updates, kv_entries, ...)` — applies static updates first, then calls `self._status.resume(kv_entries, skip_keys=static_keys)`. After the change, `static_updates` is removed: the method signature becomes `resume_from_snapshots(kv_entries, stream_entries, spatial_entries)` and calls `self._status.resume(kv_entries)` with no skip list.

### Validation (to be updated)

`agentsociety/simulation/infrastructuremanager.py:188–203` — `_validate_resume_agent_count()` compares `len(resume_state["static_records"])` against configured citizen count. After the change, it should compare against `len(resume_state.get("kv_snapshots", {}))` — the number of distinct agent IDs in the KV snapshot dict.

### Schema (to be deleted)

`agentsociety/database/schema.py:82–123` — `StaticAgentAttributesRecord` TypedDict with 30 typed fields.

## Similar Patterns & Reuse

- **`AgentKVSnapshotRecord`** at `agentsociety/database/schema.py:126–131` — the KV snapshot record type. The resume reader at `agentsociety/database/base_database.py:575–580` already builds a `dict[int, list[dict]]` keyed by `agent_id`. This exact structure is what the simplified `prepare_agents()` will use directly, with no translation layer needed.

- **`KVMemory.resume()`** at `agentsociety/memory/kv_memory.py:260–284` — already accepts `kv_entries: list[dict]` with `key` and `value_json` fields. No changes needed here; removing `skip_keys` from the call is the only change at the call site.

## Implementation Strategy

**Step 1 — Simplify `Memory.resume_from_snapshots()`**

Before: `agentsociety/memory/memory.py:162–178` takes `static_updates` as first arg, applies it first, and passes `static_keys` as `skip_keys` to `self._status.resume()`.

After: Remove the `static_updates` parameter and the `skip_keys` logic. The new body is two lines:
```python
await self._status.resume(kv_entries)
await self._stream.resume(stream_entries)
await self._spatial.resume(spatial_entries)
```

**Step 2 — Simplify `prepare_agents()` in `AgentManager`**

Before: `agentsociety/simulation/agentmanager.py:572–618` fetches `static_records`, builds a lookup dict, then for each citizen agent calls `_static_record_to_memory_updates()` and passes the result to `resume_from_snapshots()`.

After: Remove the `resume_static_by_agent_id` lookup and the `static_record is None` guard. Pass `kv_entries` directly as the first positional argument to `resume_from_snapshots()`. Remove the `_static_record_to_memory_updates()` static method entirely.

**Step 3 — Update `_validate_resume_agent_count()`**

Before: `agentsociety/simulation/infrastructuremanager.py:195–197` counts `len(static_records)`.

After: Count `len(resume_state.get("kv_snapshots", {}))`. Update the error message accordingly.

**Step 4 — Strip the static queries from `fetch_resume_data()`**

Before: `agentsociety/database/base_database.py:441–457` runs two queries against `static_agent_attributes` and returns `"static_step"` and `"static_records"` in the result dict.

After: Delete those query calls. Remove `"static_step"` and `"static_records"` from the returned dict. Remove the `static_step` parameter from `_run_resume_query()` and the abstract `_resume_query()` signature.

**Step 5 — Remove query implementations from both backends**

Before: `agentsociety/database/duckdb.py:308–334` and `agentsociety/database/clickhouse.py:259–288` each have `"latest_static_step"` and `"static_rows"` branches.

After: Delete those branches. Delete `_postprocess_static_rows()` override in `agentsociety/database/duckdb.py:271–276` and its call site in `base_database.py:457`.

**Step 6 — Remove the write path**

Before: `agentsociety/simulation/agentmanager.py:839–988` contains `save_agent_static_info()`. Called from `agentsociety/simulation/simulationengine.py:608–613`.

After: Delete `save_agent_static_info()`. Remove the call site in `simulationengine.py` (the entire `if self._resume_state is None:` block around it, or just the method call and the log line).

**Step 7 — Remove table registration and schema type**

- `agentsociety/database/base_database.py:85` — remove the `"static_agent_attributes": StaticAgentAttributesRecord` entry.
- `agentsociety/database/database_actor.py:215–219` — remove `insert_static_agent_attributes_record()`.
- `agentsociety/database/database_actor.py:23` — remove the `StaticAgentAttributesRecord` import.
- `agentsociety/database/base_database.py:28,39` — remove `StaticAgentAttributesRecord` import and union entry.
- `agentsociety/database/schema.py:82–123` — delete `StaticAgentAttributesRecord`.

## Trade-Offs

**Gained:** Simpler code. The resume path loses a translation layer (`_static_record_to_memory_updates`) and a priority-override mechanism (`skip_keys`). The write path loses a 30-field serialization loop. The DB schema loses a table with ~30 columns.

**Sacrificed:** The static table was the only source that preserved the original (step-0) values of attributes marked `storage_class == "static"` independently of whatever the KV snapshot captured. If a KV snapshot is corrupted or truncated for a given agent, the static fallback no longer exists. This risk is accepted given that the KV snapshot is already the primary resume source.

**Sacrificed:** Any external tooling (dashboards, analytics queries) that reads `static_agent_attributes` directly will break. This is an ops concern, not a code concern.

## Rejected Approaches

- **Keep static table as write-only analytics artifact, not used for resume.** Rejected: if it's not needed for resume and not part of the web UI read path, it has no remaining consumer. Keeping dead write paths for potential future analytics use adds complexity with no current benefit.

- **Replace static table with a dedicated "initial KV snapshot" at step 0.** Rejected: the first full KV snapshot is already written at step 0 (or the first checkpoint step). There is no need to introduce a separate concept.

## Assumptions & Open Questions

1. The KV snapshot written at the first checkpoint captures all keys that the static table currently stores, including nested structures (`preferences`, `big5`, `home`, `work`). This should be verified by inspecting the keys in `agent.status` at checkpoint time before the first call to `save_agent_static_info`.

2. No downstream system outside this repository queries `static_agent_attributes`. Confirm before deploying.

3. The agent-count validation replacement using `len(kv_snapshots)` is valid only if every citizen agent always produces at least one KV entry in the snapshot. If an agent has no status keys, it will not appear in the KV dict. This edge case should be confirmed to be impossible by the current initialization flow.

## Code That Could Be Refactored *(informational)*

- `agentsociety/simulation/agentmanager.py:839–988` — `save_agent_static_info()` also contains the helper lambdas `_as_str`, `_as_int`, `_as_float`. These disappear with the method; no action needed.
- `agentsociety/database/base_database.py:395–399` — `_postprocess_static_rows()` is a no-op in the base class, overridden only in DuckDB. Removing it also removes a minor inheritance complexity.

## Proposed Next Steps

1. Verify assumption 1 above: add a temporary debug log or test that prints the KV keys captured at the first checkpoint and confirms the static-table keys are present.
2. Execute steps 1–7 in the implementation strategy above, in that order (start from the consumer end, work back to the write end).
3. Run `sh tests/run_e2e_tests` after each step to catch regressions early.
4. Remove `StaticAgentAttributesRecord` last, after all imports are confirmed gone.
