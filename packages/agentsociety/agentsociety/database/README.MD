# Database Module

This folder contains the simulation telemetry persistence layer with
ClickHouse-first startup and DuckDB fallback.

## Purpose

The database package provides:

- A ClickHouse backend with batched writes.
- A DuckDB fallback backend for environments without ClickHouse.
- Strongly typed telemetry record schemas.
- A Ray actor wrapper used by simulation code.
- SQL migration loading on startup.

## Files

- `clickhouse.py`: Main `ClickHouseDatabase` implementation.
- `duckdb.py`: `DuckDBDatabase` fallback implementation.
- `schema.py`: TypedDict definitions for all record payloads.
- `database_actor.py`: Ray actor wrapper that selects backend at init.
- `migrations/`: ClickHouse SQL files applied at startup in lexicographic order.
- `__init__.py`: Public exports.

## Data Model

Record contracts are defined in `schema.py`:

- `AdjustNeedsRecord`
- `PromptResponseRecord`
- `AgentLocationTypeRecord`
- `AgentTransportTypeRecord`
- `StepAgentStatusRecord`
- `BlockDispatcherRecord`
- `ExperimentInfoRecord`

Both backends map each table name to one schema and derive column names from the
TypedDict annotations to reduce duplication.

## Batching Behavior

Both backends use a unified per-table batch state:

- In-memory queue per table.
- Last flush timestamp per table.
- Auto-flush when either condition is met:
  - queue size reaches `batch_size`
  - elapsed time reaches `batch_timeout`

Manual flush methods:

- `flush_all_batches()`: flushes all table queues.
- `close()`: flushes and closes the active backend connection.

## Startup Flow

On actor initialization, `DatabaseActor`:

1. Attempts to initialize ClickHouse first.
2. If ClickHouse is unavailable, initializes DuckDB fallback.
3. Uses the same actor method surface for simulation regardless of backend.

DuckDB file layout:

- `<data_dir>/duckdb/<exp_id>.duckdb`

## Migration Conversion For DuckDB

DuckDB does not use separate migration files. It reads the ClickHouse `.sql`
migrations and converts them at runtime.

Current conversion rules include:

- Type conversions such as `LowCardinality(String)` -> `VARCHAR`,
	`DateTime64(3)` -> `TIMESTAMP`, `Int32` -> `INTEGER`, `Float64` -> `DOUBLE`.
- `Array(...)` and `Nullable(...)` ClickHouse types converted to DuckDB-compatible
	scalar/text representations.
- ClickHouse `CODEC(...)` removed.
- `ENGINE = ...`, `ORDER BY ...`, and `PARTITION BY ...` clauses removed.
- Multi-column `ALTER TABLE ... ADD COLUMN ...` normalized into per-column DuckDB
	`ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` statements.

When adding migrations, keep SQL compatible with this conversion approach.

## Simulation Step

The active step is stored in `simulation_step` and set via:

- `set_simulation_step(step: int)`

Most insert methods include this value directly in the record payload. For adjust-needs records, the value is inferred at flush time.

Experiment metadata snapshots are stored in `experiment_info` and updated when simulation metadata is persisted by `DatabaseWriter.update_exp_info`.

## Direct Usage Example

```python
from datetime import datetime

from agentsociety.database import ClickHouseDatabase

db = ClickHouseDatabase(
	exp_id="exp-001",
	home_dir="/tmp/agentsociety",
	host="localhost",
	port=8123,
	username="default",
	password="clickhouse",
	database="fastsociety",
	batch_size=128,
	batch_timeout=30.0,
)

db.set_simulation_step(42)

db.insert_prompt_response_record(
	timestamp=datetime.now(),
	agent_id=7,
	prompt="What should I do next?",
	response="Go to work",
	block_name="PlannerBlock",
	func_name="step",
)

db.flush_all_batches()
db.close()
```

Optional DuckDB dependency install:

```bash
pip install .[duckdb]
```

## Ray Actor Usage Example

```python
import ray
from datetime import datetime

from agentsociety.database.database_actor import DatabaseActor

ray.init()

db_actor = DatabaseActor.remote(
	exp_id="exp-001",
	home_dir="/tmp/agentsociety",
)

db_actor.set_simulation_step.remote(42)
db_actor.insert_prompt_response_record.remote(
	timestamp=datetime.now(),
	agent_id=7,
	prompt="What should I do next?",
	response="Go to work",
	block_name="PlannerBlock",
	func_name="step",
)

db_actor.flush_all_batches.remote()
db_actor.close.remote()
```

## Resume Behavior

- Resume fetch probes available backends and returns the first matching source
	experiment data.
- Checkpoint and snapshot resume data are supported by both backends.

## Notes

- Backend fallback is init-time only.
- If ClickHouse is unavailable at startup, simulation uses DuckDB automatically.
- Metrics can be emitted through an optional Prometheus actor handle.
- Keep migrations backward-compatible for existing deployments.
