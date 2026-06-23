# `webapi/` — REST API and Web Backend

This package provides a FastAPI-based web backend to manage, monitor, and interact with simulations via HTTP.

---

## Files

| File | Purpose |
|---|---|
| `app.py` | FastAPI application factory and startup configuration |
| `clickhouse.py` | ClickHouse query helpers for the analytics endpoints |
| `api/` | Route handlers grouped by domain |
| `constants/` | Shared constants (status codes, error messages) |
| `models/` | Pydantic request/response schemas for the API |

---

## Starting the Server

```bash
uvicorn en_agentsociety.webapi.app:app --host 0.0.0.0 --port 8080 --reload
```

Or programmatically:

```python
from en_agentsociety.webapi.app import create_app
import uvicorn

app = create_app(config=...)
uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## API Endpoints

### Experiments

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/experiments` | Create and start a new simulation |
| `GET` | `/api/experiments` | List all experiments |
| `GET` | `/api/experiments/{id}` | Get experiment status and config |
| `POST` | `/api/experiments/{id}/stop` | Stop a running experiment |
| `DELETE` | `/api/experiments/{id}` | Delete experiment and its data |

### Agents

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/experiments/{id}/agents` | List all agents and their status |
| `GET` | `/api/experiments/{id}/agents/{agent_id}` | Get agent details and memory |
| `POST` | `/api/experiments/{id}/agents/{agent_id}/interview` | Send interview message |

### Surveys & Data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/experiments/{id}/surveys` | Get survey responses |
| `GET` | `/api/experiments/{id}/dialogs` | Get agent dialog logs |
| `GET` | `/api/experiments/{id}/status` | Time-series status data |

### Analytics (ClickHouse)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/experiments/{id}/metrics` | Aggregated metrics from ClickHouse |
| `GET` | `/api/experiments/{id}/performance` | Block execution time stats |

---

## Authentication

When the `commercial/auth/` package is installed, all endpoints require a valid API key via:

```
Authorization: Bearer <api-key>
```

Without the commercial package, the API runs without authentication.

---

## CLI Integration

The `cli/` package wraps common API calls for command-line use:

```bash
en-agentsociety run --config my_experiment.yaml
en-agentsociety status <experiment-id>
en-agentsociety stop <experiment-id>
```
