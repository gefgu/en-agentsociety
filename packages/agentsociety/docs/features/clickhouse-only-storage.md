# ClickHouse-Only Storage

> Remove `DatabaseWriter` (SQLite/PostgreSQL) entirely and consolidate all simulation persistence onto `DatabaseActor` (ClickHouse), update the web API to read from ClickHouse, drop DuckDB fallback, and provide migration tooling for historical data.

---

## Purpose & Motivation

The codebase currently maintains two parallel persistence systems:

1. **`DatabaseWriter`** — SQLite or PostgreSQL via SQLAlchemy async. Stores agent dialogs, statuses, profiles, surveys, global prompts, metrics, and experiment info. Used by the web UI.
2. **`DatabaseActor`** — ClickHouse via `clickhouse_connect`, with DuckDB fallback. Stores simulation telemetry: agent status per step, block dispatches, needs adjustments, LLM prompt/response logs, memory snapshots, experiment info, static agent attributes.

These two systems write **overlapping data** (both write experiment info and agent status) but serve somewhat different masters: `DatabaseWriter` serves the web UI, `DatabaseActor` serves simulation analytics and checkpoint/resume. Maintaining both adds complexity: two sets of migration files, two schemas, two read paths in the web API, and a DuckDB fallback that doubles the DuckDB surface area.

The goal is a single durable store (ClickHouse) for all simulation data so the web UI, analytics, and checkpoint system all read and write the same place.

---

## Success Criteria

- A simulation run with `DatabaseWriter` disabled and no PostgreSQL/SQLite configured produces the same web UI behavior as today (experiment list, agent status, dialogs, surveys, profiles, prompts, metrics all visible).
- The `pending_dialog` and `pending_survey` injection path (web UI sends message → simulation picks it up next tick) works via ClickHouse.
- The `DatabaseActor` no longer accepts a DuckDB fallback — if ClickHouse is unreachable, initialization fails fast with a clear error.
- Historical SQLite/PostgreSQL data can be exported and imported into ClickHouse using provided scripts.
- The `agentsociety ui` CLI still works without needing `env.db` to point to PostgreSQL/SQLite.

---

## Scope

**In scope:**
- Delete `agentsociety/storage/database.py` (`DatabaseWriter`, `DatabaseConfig`, `_create_tables`).
- Delete or strip `agentsociety/storage/model.py`, `agentsociety/storage/type.py`, `agentsociety/storage/_base.py` of all content that is only used by `DatabaseWriter` (the per-experiment dynamic SQLAlchemy tables).
- Keep the SQLAlchemy `Experiment` ORM class and the `Base`, `TABLE_PREFIX` plumbing **only insofar as they serve the web API's own management tables** (`as_experiment`, `as_running_experiment`, `as_agent_profiles`, `as_survey`, etc.). These are web-UI-side config tables, not simulation telemetry.
- Add new ClickHouse tables to cover data that `DatabaseWriter` wrote but `DatabaseActor` does not: dialogs, global prompts, metrics, pending dialogs, pending surveys.
- Add migration SQL files (`0014_*` through `~0019_*`) for those new tables.
- Rewrite `DataRecorder` to remove all `DatabaseWriter` calls and route everything through `DatabaseActor`.
- Rewrite the web API endpoints that currently query per-experiment SQLAlchemy dynamic tables (e.g., `as_{exp_id}_agent_status`) to instead query ClickHouse.
- Update `AgentManager`, `AgentToolbox`, `Agent`, `SimulationEngine`, `IndividualEngine`, `InfrastructureManager` to remove the `database_writer` parameter and `DatabaseWriter` import.
- Remove DuckDB as a fallback from `DatabaseActor` — ClickHouse only.
- Provide a Python export/import script: `tools/migrate_sqlite_to_clickhouse.py`.
- Update `EnvConfig` to remove `db: DatabaseConfig` (or make it optional/deprecated).
- Update the `agentsociety ui` CLI and `agentsociety check` CLI to use ClickHouse DSN instead of SQLite/PostgreSQL DSN.

**Out of scope:**
- Changing the ClickHouse connection configuration shape beyond what is needed (the existing `ClickHouseConfig` in `configs/env.py` is kept as-is).
- Migrating the **web-UI management tables** (`as_experiment`, `as_survey`, `as_agent_profiles`, `as_agent_template`, `as_running_experiment`) out of SQLite/PostgreSQL — these are read/written exclusively by the web UI and are not simulation telemetry. They stay in SQLite/PostgreSQL for now, served by the existing SQLAlchemy session.
- Any frontend/JS changes.
- Changing the `IndividualEngine` checkpoint/resume system (it currently uses `DatabaseWriter`; this refactor covers it insofar as it uses the same `DatabaseWriter` APIs, but the individual engine task-result table needs ClickHouse equivalence).

---

## Constraints

- ClickHouse must be running before the simulation starts. No graceful degradation to a local file store.
- ClickHouse uses `ReplacingMergeTree` for experiment_info (deduplication on `updated_at`). All new tables must use appropriate engines.
- The web API's management-plane tables (experiments list, survey definitions, agent profile metadata, running experiments) stay in SQLite/PostgreSQL — the `create_app()` factory continues to receive a `db_dsn`.
- `fetch_pending_dialogs` and `mark_dialogs_as_processed` are synchronous from the simulation's perspective (called inside a step loop). ClickHouse is eventually consistent but mutations (`ALTER TABLE ... DELETE`) are expensive. A dedicated `pending_dialog` table must use a lightweight pattern (see Architecture section).

---

## Architecture & Integration Points

### Current dual-write architecture

```
SimulationEngine._step()
    └── DataRecorder (background async queue)
            ├── DatabaseWriter (SQLite / PostgreSQL)   <-- TO REMOVE
            │       write_statuses(), write_dialogs(), log_metric(),
            │       update_exp_info(), write_global_prompt(),
            │       fetch_pending_dialogs(), fetch_pending_surveys()
            └── DatabaseActor (Ray remote, ClickHouse)
                    insert_step_agent_status_record(),
                    insert_experiment_info_record(),
                    insert_kv_snapshot_batch(), ...

AgentManager.create_toolbox()
    └── AgentToolbox(database_writer=...)   <-- TO REMOVE field

Agent.write_dialog()
    └── self.database_writer.write_dialogs()  <-- TO REMOVE

Agent.send_survey() / process_survey_response()
    └── self.database_writer.write_surveys()  <-- TO REMOVE
```

### After refactor: single-write architecture

```
SimulationEngine._step()
    └── DataRecorder (background async queue)
            └── DatabaseActor (Ray remote, ClickHouse only)
                    All insert_*() methods, including new:
                    insert_dialog_batch(), insert_global_prompt(),
                    log_metric(), fetch_pending_dialogs(),
                    fetch_pending_surveys(), mark_dialogs_processed()

AgentToolbox — database_writer field removed

Agent.write_dialog()
    └── self._toolbox.get_tool("db_actor").insert_dialog_batch.remote(...)
```

### Key integration points

- `agentsociety/simulation/datarecorder.py:48–58` — `DataRecorder.__init__` receives both `database_writer` and `db_actor`. After refactor, only `db_actor`.
- `agentsociety/simulation/datarecorder.py:370–464` — `_process_event_once()` dispatches events to `DatabaseWriter` methods. These branches become ClickHouse-only calls.
- `agentsociety/simulation/infrastructuremanager.py:265–277` — `_init_database_writer_if_enabled()` creates `DatabaseWriter`. This method is deleted.
- `agentsociety/simulation/infrastructuremanager.py:392` — `initialize_all()` calls `_init_database_writer_if_enabled()`. That call is removed.
- `agentsociety/simulation/infrastructuremanager.py:413–415` — `close()` disposes `DatabaseWriter`. Removed.
- `agentsociety/simulation/agentmanager.py:64,87,126` — `database_writer` parameter passed to `AgentToolbox`. Removed.
- `agentsociety/agent/toolbox.py:175` — `database_writer: Optional[DatabaseWriter]` field. Removed.
- `agentsociety/agent/agent_base.py:214,301–302` — `self.database_writer` property and `write_dialogs()` call. Rerouted to `db_actor`.
- `agentsociety/agent/agent.py:411–599` — multiple `self.database_writer.write_surveys()`, `write_dialogs()`, `mark_surveys_as_processed()`, `mark_dialogs_as_processed()` calls. All rerouted to `db_actor`.
- `agentsociety/simulation/simulationengine.py:1346,1372` — `fetch_pending_dialogs()` and `fetch_pending_surveys()` called on `database_writer`. These become synchronous ClickHouse queries (see Pending Messages section below).
- `agentsociety/simulation/individualengine.py:144–153,446,508–509` — `DatabaseWriter` construction, `write_task_result()`, `update_exp_info()`. Rerouted to `db_actor`.
- `agentsociety/configs/env.py:7,46` — `EnvConfig.db: DatabaseConfig`. Made optional (defaults to `enabled=False`) or deprecated.
- `agentsociety/cli/cli.py:115` — `db_dsn = c.env.db.get_dsn(...)`. After refactor, the web UI connects to ClickHouse for experiment data.
- `agentsociety/webapi/app.py:94–106` — `create_app(db_dsn=...)` lifespan creates SQLAlchemy session. Stays for management tables, but the experiment telemetry queries move to ClickHouse.
- `agentsociety/webapi/api/experiment.py:107–399` — all dynamic table queries (`as_{exp_id}_agent_status`, `as_{exp_id}_agent_dialog`, etc.). Rewritten to query ClickHouse.
- `agentsociety/webapi/api/agent.py:38–599` — all queries on per-experiment SQLAlchemy tables. Rewritten to query ClickHouse.
- `agentsociety/webapi/clickhouse.py:1–15` — `get_clickhouse_client()` singleton. Already exists; the web API will use this for all telemetry reads.

---

## Similar Patterns & Reuse

- **`agentsociety/webapi/api/visits.py:105–163`** — `get_agent_visits()`: already queries `step_agent_status` and `agent_location_type` tables in ClickHouse directly via `get_clickhouse_client()`. This is the **exact pattern** all the migrated endpoints should follow.
- **`agentsociety/database/clickhouse.py:191–237`** — `_create_tables()`: reads `.sql` migration files from `agentsociety/database/migrations/` and runs them in order. New tables follow this same migration file convention.
- **`agentsociety/database/duckdb.py:202–228`** — `_to_duckdb_statements()`: translates ClickHouse DDL to DuckDB. Will be deleted.
- **`agentsociety/simulation/datarecorder.py:90–103`** — `enqueue_clickhouse_status()` and subsequent `_process_event_once()` dispatch show the pattern for routing new event types through the recorder to `db_actor`.

---

## The Pending Messages Problem

This is the most architecturally tricky part of the migration and must be designed carefully before implementation.

**Current flow:** The web UI writes a dialog request to the `pending_dialog` SQL table (via `POST /experiments/{exp_id}/agents/{agent_id}/dialog`). On each simulation tick, `SimulationEngine._step()` calls `await self._database_writer.fetch_pending_dialogs()` to retrieve unprocessed rows, converts them to `Message` objects, and then calls `mark_dialogs_as_processed()`.

**The ClickHouse problem:** ClickHouse does not support row-level mutable state efficiently. `UPDATE`/`DELETE` are heavyweight mutation operations, not transactional row updates.

**Recommended approach — Status-column pattern with `ReplacingMergeTree`:**

Use a `pending_messages` ClickHouse table with a `processed` column and `ReplacingMergeTree(processed)`. To mark a row as processed, insert a new row with `processed = 1`. ClickHouse deduplicates on the ORDER BY key during merges. Queries for unprocessed messages use `FINAL` to force deduplication at query time:

```sql
SELECT * FROM pending_messages FINAL WHERE exp_id = ? AND processed = 0
```

To insert a "processed" marker:
```sql
INSERT INTO pending_messages (..., processed) VALUES (..., 1)
```

The `FINAL` modifier forces merge-time deduplication at query time, so the result is correct. This is safe because pending message volume is low (user-driven).

Alternatively (simpler for writes, slightly heavier reads): keep the pending_dialog and pending_survey tables in the existing SQLite/PostgreSQL **only when the web UI needs to inject messages**. Since the web UI already has a SQLAlchemy session, the web UI writes to SQL, the simulation reads from SQL. This minimizes scope creep — the simulation just needs to keep its `fetch_pending_dialogs()` / `fetch_pending_surveys()` calls pointing to the SQL DB. Only the **read telemetry** (dialogs, statuses, surveys, etc.) moves to ClickHouse.

**Recommendation: use the hybrid approach.** Keep `pending_dialog` and `pending_survey` in the web UI's SQLite/PostgreSQL, delete them from `DatabaseWriter` only insofar as they're independent of the simulation telemetry write path. The simulation's `fetch_pending_dialogs()` / `fetch_pending_surveys()` calls move from `DatabaseWriter` to a lightweight `PendingMessageStore` that wraps a direct SQLAlchemy connection. This is a smaller change and avoids the ClickHouse mutation problem entirely.

This is an open question for the user — see Assumptions & Open Questions.

---

## New ClickHouse Tables Needed

These tables exist in SQLite/PostgreSQL today but not in ClickHouse. They need migration files:

### `0014_create_agent_dialog_table.sql`
```sql
CREATE TABLE IF NOT EXISTS agent_dialog (
    exp_id      LowCardinality(String),
    agent_id    Int32,
    simulation_step Int32,
    day         Int32,
    t           Float64,
    type        Int32,
    speaker     LowCardinality(String),
    content     String CODEC(ZSTD(3)),
    created_at  DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, created_at)
PARTITION BY exp_id;
```

### `0015_create_agent_survey_table.sql`
```sql
CREATE TABLE IF NOT EXISTS agent_survey (
    exp_id      LowCardinality(String),
    agent_id    Int32,
    simulation_step Int32,
    day         Int32,
    t           Float64,
    survey_id   UUID,
    result      String CODEC(ZSTD(3)),
    created_at  DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, created_at)
PARTITION BY exp_id;
```

### `0016_create_agent_profile_table.sql`
```sql
CREATE TABLE IF NOT EXISTS agent_profile (
    exp_id      LowCardinality(String),
    agent_id    Int32,
    name        String,
    profile     String CODEC(ZSTD(3))
)
ENGINE = ReplacingMergeTree()
ORDER BY (exp_id, agent_id)
PARTITION BY exp_id;
```

### `0017_create_global_prompt_table.sql`
```sql
CREATE TABLE IF NOT EXISTS global_prompt (
    exp_id      LowCardinality(String),
    simulation_step Int32,
    day         Int32,
    t           Float64,
    prompt      String CODEC(ZSTD(3)),
    created_at  DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY (exp_id, simulation_step)
PARTITION BY exp_id;
```

### `0018_create_metric_table.sql`
```sql
CREATE TABLE IF NOT EXISTS metric (
    exp_id      LowCardinality(String),
    key         LowCardinality(String),
    value       Float64,
    step        Int32,
    created_at  DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY (exp_id, key, step)
PARTITION BY exp_id;
```

### `0019_create_task_result_table.sql` (for `IndividualEngine`)
```sql
CREATE TABLE IF NOT EXISTS task_result (
    exp_id      LowCardinality(String),
    agent_id    Int32,
    context     String CODEC(ZSTD(3)),
    ground_truth String CODEC(ZSTD(3)),
    result      String CODEC(ZSTD(3)),
    created_at  DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, created_at)
PARTITION BY exp_id;
```

Note: `static_agent_attributes` already exists (`0007_create_static_agent_attributes.sql`) and covers much of what `agent_profile` stored. The new `agent_profile` table covers the name + JSON profile blob that the web UI displays. Whether to unify them is an open question.

---

## New `DatabaseActor` Methods Needed

The following methods must be added to `DatabaseActor` (and delegated to `ClickHouseDatabase`) to cover data currently only written by `DatabaseWriter`:

| Method | Table | Replaces |
|--------|-------|---------|
| `insert_dialog_batch(records)` | `agent_dialog` | `DatabaseWriter.write_dialogs()` |
| `insert_survey_batch(records)` | `agent_survey` | `DatabaseWriter.write_surveys()` |
| `insert_agent_profile_batch(records)` | `agent_profile` | `DatabaseWriter.write_profiles()` |
| `insert_global_prompt(record)` | `global_prompt` | `DatabaseWriter.write_global_prompt()` |
| `log_metric_batch(records)` | `metric` | `DatabaseWriter.log_metric()` |
| `insert_task_result_batch(records)` | `task_result` | `IndividualEngine` / `DatabaseWriter.write_task_result()` |
| `fetch_pending_dialogs(exp_id)` | (see below) | `DatabaseWriter.fetch_pending_dialogs()` |
| `mark_dialogs_processed(exp_id, ids)` | (see below) | `DatabaseWriter.mark_dialogs_as_processed()` |
| `fetch_pending_surveys(exp_id)` | (see below) | `DatabaseWriter.fetch_pending_surveys()` |
| `mark_surveys_processed(exp_id, ids)` | (see below) | `DatabaseWriter.mark_surveys_as_processed()` |

The pending_dialog/survey methods are only needed if the hybrid approach is **not** taken (see Assumptions & Open Questions).

---

## Web API Read Path Changes

### Endpoints that currently read per-experiment SQLAlchemy tables

All of these are in `agentsociety/webapi/api/` and query tables named `as_{exp_id}_agent_status`, `as_{exp_id}_agent_dialog`, etc. via the SQLAlchemy `db` session.

| Endpoint | File:Line | Current source | New source |
|----------|-----------|----------------|------------|
| `GET /experiments` | `experiment.py:55` | `as_experiment` (SQLAlchemy ORM) | Stays in SQL — this is a management table |
| `GET /experiments/{id}` | `experiment.py:80` | `as_experiment` (SQLAlchemy ORM) | Stays in SQL |
| `GET /experiments/{id}/timeline` | `experiment.py:106` | `as_{id}_agent_status` | ClickHouse: `SELECT DISTINCT day, t FROM step_agent_status WHERE exp_id=?` |
| `GET /experiments/{id}/metrics` | `experiment.py:293` | `as_{id}_metric` | ClickHouse: `SELECT key, value, step FROM metric WHERE exp_id=?` |
| `POST /experiments/{id}/export` | `experiment.py:319` | Multiple per-exp tables | ClickHouse queries per table |
| `DELETE /experiments/{id}` | `experiment.py:153` | Drops per-exp SQL tables | ClickHouse: `ALTER TABLE ... DELETE WHERE exp_id=?` |
| `GET /experiments/{id}/agents/-/status` | `agent.py:147` | `as_{id}_agent_status` | ClickHouse: `step_agent_status` |
| `GET /experiments/{id}/agents/{aid}/status` | `agent.py:184` | `as_{id}_agent_status` | ClickHouse: `step_agent_status` |
| `GET /experiments/{id}/agents/{aid}/dialog` | `agent.py:37` | `as_{id}_agent_dialog` | ClickHouse: `agent_dialog` |
| `GET /experiments/{id}/agents/-/profile` | `agent.py:91` | `as_{id}_agent_profile` | ClickHouse: `agent_profile` or `static_agent_attributes` |
| `GET /experiments/{id}/agents/{aid}/profile` | `agent.py:117` | `as_{id}_agent_profile` | ClickHouse: `agent_profile` or `static_agent_attributes` |
| `GET /experiments/{id}/agents/{aid}/survey` | `agent.py:217` | `as_{id}_agent_survey` | ClickHouse: `agent_survey` |
| `GET /experiments/{id}/prompt` | `agent.py:270` | `as_{id}_global_prompt` | ClickHouse: `global_prompt` |
| `POST /experiments/{id}/agents/{aid}/dialog` | `agent.py:308` | Writes to `as_{id}_pending_dialog` | Writes to SQL pending table OR ClickHouse |
| `POST /experiments/{id}/agents/{aid}/survey` | `agent.py:362` | Writes to `as_{id}_pending_survey` | Writes to SQL pending table OR ClickHouse |

The `visits.py` endpoints already query ClickHouse (`step_agent_status`, `agent_location_type`) and require no changes.

### Experiment info and list in ClickHouse

The `experiment_info` table already exists in ClickHouse (migration `0008`). The web API can read the experiment list from ClickHouse directly:

```sql
SELECT FINAL * FROM experiment_info ORDER BY updated_at DESC
```

This is the same data that `DatabaseWriter.update_exp_info()` wrote to the SQL `as_experiment` table. After the refactor the simulation only writes to ClickHouse, so the web API must read from ClickHouse for experiment state. The web UI's own management tables (`as_running_experiment`, `as_survey`, `as_agent_profiles`) remain in SQLite/PostgreSQL.

---

## Implementation Strategy

The work decomposes into five sequential phases. Each phase is independently deployable and testable.

### Phase 1: New ClickHouse tables and `DatabaseActor` methods

**Before:** `ClickHouseDatabase` has tables `NeedsBlock_adjust_needs`, `prompt_responses`, `agent_location_type`, `agent_transport_type`, `step_agent_status`, `block_dispatcher`, `static_agent_attributes`, `experiment_info`, `agent_kv_snapshot`, `agent_stream_snapshot`, `agent_spatial_snapshot`, `pending_messages_snapshot`.

**After:** Add migration files `0014` through `0019` in `agentsociety/database/migrations/`. Add insert methods to `ClickHouseDatabase` (in `agentsociety/database/clickhouse.py`), then add pass-through methods in `DatabaseActor` (`agentsociety/database/database_actor.py`).

New `TypedDict` schemas go in `agentsociety/database/schema.py`.

### Phase 2: Migrate `DataRecorder` to ClickHouse-only

**Before:** `DataRecorder.__init__` at `datarecorder.py:48` takes `database_writer: Optional[DatabaseWriter]`. `_process_event_once()` at `datarecorder.py:370` branches on `self._database_writer is not None`.

**After:**
- Remove `database_writer` parameter from `DataRecorder.__init__`.
- Remove all `if self._database_writer is not None:` branches in `_process_event_once()`.
- For each event type (`status`, `metrics`, `exp_info`, `global_prompt`), route to `self._db_actor`.
- New event types: `dialog`, `survey`, `profile`, `metric`, `task_result`.

### Phase 3: Remove `DatabaseWriter` from agents and agent manager

**Before:** `AgentToolbox` at `toolbox.py:175` has `database_writer: Optional[DatabaseWriter]`. Agents access it via `self.database_writer` at `agent_base.py:214`. Calls in `agent.py:411,508,523,557,598`.

**After:**
- Remove `database_writer` field from `AgentToolbox`.
- All `self.database_writer.write_dialogs()` calls in `agent.py` and `agent_base.py` become enqueue calls on the `DataRecorder` or direct `db_actor` remote calls.
- The `db_actor` handle must be accessible from agents. The existing `db_tool` (`CustomTool` with `name="db_actor"`) is already added to the toolbox via `AgentManager` — use `self._toolbox.get_tool_object("db_actor")`.
- Remove `database_writer` from `AgentManager.__init__` at `agentmanager.py:64` and `create_toolbox()` at `agentmanager.py:126`.

### Phase 4: Remove `DatabaseWriter` from `InfrastructureManager`, engines, and config

**Before:** `InfrastructureManager._init_database_writer_if_enabled()` at `infrastructuremanager.py:265`. `SimulationEngine._database_writer` at `simulationengine.py:80`. `IndividualEngine._database_writer` at `individualengine.py:70`.

**After:**
- Delete `_init_database_writer_if_enabled()`.
- Remove `database_writer` field from all engines.
- Remove `DatabaseWriter` import from `simulationengine.py`, `individualengine.py`, `infrastructuremanager.py`, `agentmanager.py`, `toolbox.py`, `agent_base.py`, `agent.py`.
- `EnvConfig.db` field becomes `Optional[DatabaseConfig]` defaulting to `None` (or keep it but ignore it). The `check` CLI command is updated to skip the SQL DB check if `db` is None.
- `DatabaseConfig` class in `storage/database.py` can be kept if the web UI still needs a DSN, but the rest of `database.py` is deleted.

The `SimulationEngine.enable_database` property at `simulationengine.py:1062` currently checks `self._database_writer is None and self._db_actor is None`. After refactor it checks `self._db_actor is None`.

The `pending_dialogs` fetch at `simulationengine.py:1346` and `pending_surveys` at `simulationengine.py:1372` need a resolution. With the hybrid approach these read from a small SQL table; with the full-ClickHouse approach they call `db_actor.fetch_pending_dialogs.remote()` synchronously (`await`).

### Phase 5: Rewrite web API to read from ClickHouse

**Before:** `create_app()` at `app.py:83` accepts `db_dsn` and creates a SQLAlchemy session. All agent/experiment telemetry endpoints query per-experiment SQL tables. `Experiment` ORM object from `storage/model.py` is used by web API routes.

**After:**
- `create_app()` still accepts a `db_dsn` for management tables (surveys, agent profiles, running experiments, etc.).
- A `get_clickhouse_client()` dependency (already at `webapi/clickhouse.py:6`) is injected into telemetry endpoints.
- Each telemetry endpoint is rewritten to issue a raw ClickHouse query with `exp_id` as filter instead of deriving a per-experiment table name. Example for agent status:

```python
# Before
table_name = experiment.agent_status_tablename
table, columns = agent_status(table_name)
stmt = select(table).where(table.c.day == day).where(table.c.t == t)

# After
query = "SELECT agent_id, simulation_step, lat, lng, parent_id, action, status FROM step_agent_status WHERE exp_id = {exp_id:String} AND ..."
result = clickhouse_client.query(query, parameters={"exp_id": str(exp_id), ...})
```

- `GET /experiments` reads from `experiment_info` ClickHouse table (using `FINAL`) rather than `as_experiment` SQL table.
- `DELETE /experiments/{id}` issues ClickHouse `ALTER TABLE ... DELETE WHERE exp_id = ?` for each telemetry table.
- `POST /export` streams ClickHouse query results into CSV/JSON zip.

### Phase 6: Remove DuckDB fallback

**Before:** `DatabaseActor.__init__` at `database_actor.py:43` constructs `ClickHouseDatabase`, checks `is_available()`, and falls back to `DuckDBDatabase` if not available.

**After:**
- `DatabaseActor.__init__` constructs `ClickHouseDatabase` and calls `is_available()`. If False, raises `RuntimeError` immediately.
- Delete `agentsociety/database/duckdb.py`.
- Remove `DuckDBDatabase` from `agentsociety/database/__init__.py`.
- Remove `duckdb` optional import from `database_actor.py`.

---

## Trade-Offs

| Gained | Sacrificed or risked |
|--------|---------------------|
| Single source of truth for all simulation data | Loss of SQLite as zero-dependency dev option — ClickHouse must be running |
| Web UI and analytics read from same store | More complex web API queries (raw SQL strings instead of ORM) |
| No dual-write performance cost | ClickHouse `FINAL` queries for `experiment_info` are slightly slower |
| DuckDB fallback removed = less code surface | Users who relied on DuckDB (e.g., no Docker) will break |
| Pending dialogs/surveys in ClickHouse can be more observable | ClickHouse mutations for pending message marking are expensive (if not using hybrid approach) |

---

## Rejected Approaches

**Keep `DatabaseWriter` alongside `DatabaseActor` but make it opt-in.** This was the status quo and is what created the dual-write complexity in the first place. The whole motivation for this plan is to eliminate that.

**Move management tables (surveys, agent profiles) to ClickHouse too.** ClickHouse is not designed for low-latency transactional reads/writes on small tables with frequent point updates. The SQLAlchemy session for management tables is the right tool. Mixing it would add complexity without benefit.

**Use ClickHouse for pending messages with full mutation semantics.** The `ALTER TABLE ... DELETE` path is asynchronous and non-transactional in ClickHouse. It is not appropriate for a "fetch and mark as processed" pattern that runs every simulation tick. The hybrid approach (keep pending tables in SQL) is simpler and safer.

**Use DuckDB as the primary store instead of ClickHouse.** DuckDB is single-process and does not support concurrent writes from multiple Ray actors. The simulation uses one `DatabaseActor` Ray actor, so DuckDB would technically work, but it is not suited for the web UI's concurrent read workload. ClickHouse handles both.

**Export ClickHouse data back to SQLite for the web UI.** This would re-introduce a sync problem and dual-write.

---

## Assumptions & Open Questions

1. **Pending dialogs/surveys approach.** The critical question: should the web UI write pending dialogs/surveys to the existing SQLite/PostgreSQL management DB (hybrid approach), or to ClickHouse? The hybrid approach is simpler to implement and avoids the ClickHouse mutation problem. The full-ClickHouse approach is cleaner but requires a more careful pending message design. **This must be decided before Phase 4/5 begin.**

2. **`IndividualEngine` scope.** `IndividualEngine` uses `DatabaseWriter` for task results (`write_task_result()`) and experiment info (`update_exp_info()`). Does the user want `IndividualEngine` fully migrated in this refactor, or is it out of scope? Currently assumed in scope.

3. **`agent_profile` vs `static_agent_attributes` unification.** The `static_agent_attributes` table (migration `0007`) already stores most of what `agent_profile` stored (name, demographics, etc.). The web UI's `GET /agents/-/profile` returns a JSON blob of the full profile. Should the `agent_profile` ClickHouse table store a serialized full-profile JSON (as `DatabaseWriter` did), or should the web API reconstruct profile data from `static_agent_attributes`? The former is simpler.

4. **Historical data migration scope.** The migration script needs to handle the schema mismatch between the SQLite/PostgreSQL `as_{exp_id}_agent_status` table (stores `day`, `t`, `action`, `status` per tick) and ClickHouse `step_agent_status` (stores `simulation_step`). The script must either reconstruct `simulation_step` from `(day, t)` ordering, or store it as 0 for historical data. This is acceptable for historical records.

5. **ClickHouse connection in the web API.** The `get_clickhouse_client()` at `webapi/clickhouse.py:6` hardcodes `host="localhost"`, `password="clickhouse"`. After the refactor, all web API telemetry reads go through this client. It must be configurable via `EnvConfig.clickhouse`. The `lru_cache` approach breaks if config changes at runtime, but for the web server (single process, static config) it is fine.

---

## Code That Could Be Refactored *(informational)*

- `agentsociety/simulation/datarecorder.py:207–255` — `record_block_performance_metrics()` and `record_routing_metrics()` both check `self._database_writer is not None` before doing anything useful. After the migration these guards disappear but the methods could be simplified further.
- `agentsociety/storage/database.py:680–895` — The `write_*` and `read_*` methods follow a repetitive pattern that could be a single `_write_records(table_name, data)` helper. Moot if the file is deleted.
- `agentsociety/webapi/api/experiment.py:133–148` — The `_find_started_experiment_by_id()` helper currently fetches the full `Experiment` ORM object to derive table names. After the migration, table names are no longer experiment-specific, so this helper simplifies to just verifying the experiment exists and is not `NOT_STARTED`.
- `agentsociety/database/clickhouse.py:89–109` — `table_schemas` and `table_columns` dictionaries are coupled. They could be derived from a single canonical list of `(table_name, TypedDict_class)` pairs, eliminating the `table_columns` derivation loop.

---

## Export/Import Migration Script

Location: `tools/migrate_sqlite_to_clickhouse.py`

The script performs the following steps for a given SQLite file (or PostgreSQL DSN) and ClickHouse connection:

```
1. Connect to source database (SQLite or PostgreSQL)
2. Read the as_experiment table → insert rows into experiment_info (ClickHouse)
3. For each experiment row:
   a. Read as_{exp_id}_agent_status → insert into step_agent_status
      - simulation_step is reconstructed by ordering rows by (day, t) and assigning sequential integers
   b. Read as_{exp_id}_agent_dialog → insert into agent_dialog
   c. Read as_{exp_id}_agent_survey → insert into agent_survey
   d. Read as_{exp_id}_agent_profile → insert into agent_profile
   e. Read as_{exp_id}_global_prompt → insert into global_prompt
   f. Read as_{exp_id}_metric → insert into metric
4. Report rows migrated per table
```

The script is a standalone Python file with no dependency on the agentsociety package internals (only `sqlalchemy`, `clickhouse_connect`). It takes CLI arguments:

```bash
python tools/migrate_sqlite_to_clickhouse.py \
  --source-sqlite ./agentsociety_data/sqlite.db \
  --ch-host localhost \
  --ch-port 8123 \
  --ch-user default \
  --ch-password clickhouse \
  --ch-database fastsociety \
  [--dry-run]
```

For PostgreSQL source:
```bash
python tools/migrate_sqlite_to_clickhouse.py \
  --source-pg "postgresql://user:pass@host:5432/dbname" \
  ...
```

---

## Proposed Next Steps

These steps are ordered. Each should be completed and tested before the next begins.

1. **Decide the pending dialog/survey approach** (hybrid SQL vs full ClickHouse). This is an open question that affects Phase 4 and 5 significantly. Recommend the hybrid approach.

2. **Phase 1: Add new ClickHouse tables and `DatabaseActor` methods.** Write migration files `0014`–`0019`. Add new `TypedDict` schemas. Add insert methods to `ClickHouseDatabase` and `DatabaseActor`. The new methods must be individually testable.

3. **Phase 2: Migrate `DataRecorder`.** Remove `database_writer` parameter. Route all events to `db_actor`. Verify with an end-to-end example run that all data still lands in ClickHouse.

4. **Phase 3: Remove `DatabaseWriter` from agents and agent manager.** Update `AgentToolbox`, `AgentManager`, `agent.py`, `agent_base.py`.

5. **Phase 4: Remove `DatabaseWriter` from engines and config.** Update `InfrastructureManager`, `SimulationEngine`, `IndividualEngine`, `EnvConfig`.

6. **Phase 6 (can be done in parallel with Phase 4): Remove DuckDB fallback.** Delete `duckdb.py`, simplify `DatabaseActor.__init__`.

7. **Phase 5: Rewrite web API to read from ClickHouse.** This is the highest risk change for the web UI. Do it last, after the write path is confirmed stable.

8. **Write `tools/migrate_sqlite_to_clickhouse.py`.**

9. **Delete `agentsociety/storage/database.py`** and clean up `storage/__init__.py`, `storage/model.py`, `storage/type.py`, `storage/_base.py` — remove everything only used by `DatabaseWriter`. Keep `Experiment`, `Base`, `TABLE_PREFIX` for the web UI's management tables.

10. **Update the `agentsociety check` CLI** to remove the SQL DB connection check (or make it conditional on `env.db` being configured). Update the `agentsociety ui` CLI to pass a ClickHouse-based query helper to the web app rather than a `db_dsn`.
