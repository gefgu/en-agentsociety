# Database Module

This folder contains the ClickHouse persistence layer used to store simulation telemetry.

## Purpose

The database package provides:

- A ClickHouse client wrapper with batched writes.
- Strongly typed telemetry record schemas.
- Optional Ray actor wrappers for distributed execution.
- SQL migration loading on startup.

## Files

- `clickhouse.py`: Main `ClickHouseDatabase` implementation.
- `schema.py`: TypedDict definitions for all record payloads.
- `database_actor.py`: Ray actor wrapper delegating calls to `ClickHouseDatabase`.
- `clickhouse_actor.py`: Same wrapper plus `ClickHouseActor` compatibility alias.
- `migrations/`: SQL files applied at startup in lexicographic order.
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

`ClickHouseDatabase` maps each table name to one schema and derives column names from the TypedDict annotations to reduce duplication.

## Batching Behavior

`ClickHouseDatabase` uses a unified per-table batch state:

- In-memory queue per table.
- Last flush timestamp per table.
- Auto-flush when either condition is met:
  - queue size reaches `batch_size`
  - elapsed time reaches `batch_timeout`

Manual flush methods:

- `flush_all_batches()`: flushes all table queues.
- `close()`: flushes and closes the ClickHouse client.

## Startup Flow

On initialization, `ClickHouseDatabase`:

1. Optionally creates the target database if it does not exist.
2. Connects to ClickHouse.
3. Applies SQL migrations from `migrations/`.

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

## Notes

- If ClickHouse is unavailable, insert/flush calls are logged and skipped.
- Metrics can be emitted through an optional Prometheus actor handle.
- Keep migrations backward-compatible for existing deployments.
