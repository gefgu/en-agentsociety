# `storage/` — Persistence Layer

This package handles all durable storage for experiment results, agent dialogs, profiles, and status snapshots.

---

## Files

| File | Purpose |
|---|---|
| `_base.py` | Abstract base class for storage backends |
| `database.py` | `DatabaseWriter` — async batch writer with SQLite / PostgreSQL backends |
| `model.py` | SQLAlchemy ORM models |
| `type.py` | Pydantic data schemas for each storage object type |

---

## Supported Backends

| Backend | Config | Notes |
|---|---|---|
| **SQLite** | `sqlite:///path/to/sim.db` | Default, zero-setup, file-based |
| **PostgreSQL** | `postgresql+asyncpg://...` | Recommended for production / multi-process runs |

---

## Storage Object Types (`type.py`)

| Type | Description |
|---|---|
| `StorageExpInfo` | Experiment metadata: name, status, timeline, config YAML |
| `StorageProfile` | Agent demographic profile snapshot |
| `StorageStatus` | Agent status field snapshot (per tick) |
| `StorageDialog` | Agent dialog record (LLM input/output) |
| `StorageDialogType` | Classifies dialogs: action, interview, survey, system |
| `StorageGlobalPrompt` | Global environment prompt history |
| `StoragePendingSurvey` | Survey instances waiting for agent response |

---

## `DatabaseWriter`

Async batch writer that queues writes and flushes to the database periodically:

```python
writer = DatabaseWriter(dsn="sqlite:///experiment.db")
await writer.init()

# Write a status snapshot
await writer.write_status(StorageStatus(
    exp_id="...",
    agent_id=42,
    day=1,
    t=3600,
    data={"hunger_satisfaction": 0.7, "energy_satisfaction": 0.9},
))

# Flush pending writes
await writer.flush()
await writer.close()
```

Writes are batched internally using an `asyncio.Queue` and flushed on a configurable interval to avoid overwhelming the database during high-throughput simulation.

---

## Schema

Tables are created automatically on first run using SQLAlchemy's `create_all()`. Each experiment's data is identified by `exp_id`.

---

## `EnvConfig.db`

Database connection is configured in `EnvConfig`:

```python
class EnvConfig(BaseModel):
    db: DBConfig

class DBConfig(BaseModel):
    pg_dsn: Optional[str] = None      # PostgreSQL DSN (preferred)
    # If not set, defaults to SQLite in the working directory
```
