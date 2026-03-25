# `performance/` — Observability and Monitoring Stack

This package provides production-grade observability for simulation runs, integrating Prometheus metrics, Grafana dashboards, ClickHouse analytics, and Loki log aggregation.

---

## Files

| File | Purpose |
|---|---|
| `monitoring.py` | `start_monitoring()` / `stop_monitoring()` — starts the Docker Compose stack |
| `prometheusActor.py` | Ray actor that exposes custom metrics to Prometheus |
| `DatabaseActor.py` | Ray actor that writes simulation events to ClickHouse |
| `MetricsTracker.py` | High-level API for recording agent metrics |
| `BlockPerformance.py` | Records per-block execution time and LLM token counts |
| `RoutingTracker.py` | Tracks `BlockDispatcher` routing decisions |
| `docker-compose.yml` | Full observability stack: Prometheus, Grafana, ClickHouse, Loki, Alloy |
| `prometheus.yml` | Prometheus scrape configuration |
| `grafana/` | Pre-built Grafana dashboard JSON exports |
| `clickhouse/` | ClickHouse schema SQL files |
| `loki/` | Loki configuration |
| `alloy/` | Grafana Alloy (log collector) config |

---

## Stack Architecture

```
Agents (Ray) ──► PrometheusActor ──► Prometheus ──► Grafana
             └─► DatabaseActor ──► ClickHouse ──► Grafana
Logger ──────────────────────────────────────────► Loki ──► Grafana
```

---

## Starting Monitoring

Called automatically by `SimulationEngine` when monitoring is enabled in config:

```python
from agentsociety.performance.monitoring import start_monitoring, stop_monitoring

start_monitoring(user_data_path="./sim_data")
# Access Grafana at http://localhost:3000  (default credentials: admin / admin)
# Access Prometheus at http://localhost:9091
```

`stop_monitoring()` tears down the Docker Compose stack.

The `CLICKHOUSE_DATA_PATH` environment variable is injected automatically to point ClickHouse storage at the user-specified path.

---

## `MetricsTracker`

High-level abstraction for recording per-agent metrics:

```python
tracker = MetricsTracker.remote()
await tracker.record.remote(
    agent_id=42,
    metric_name="hunger_satisfaction",
    value=0.75,
    timestamp=sim_time,
)
```

---

## `BlockPerformance`

Automatically wraps block `forward()` calls to record:

- Wall-clock execution time
- LLM prompt / completion token counts
- Block name and agent ID

Data is pushed to both Prometheus (real-time gauges/histograms) and ClickHouse (persistent event log).

---

## `RoutingTracker`

Records `BlockDispatcher` routing decisions:

- Which block was selected for each agent intention
- LLM latency for the routing call

---

## Prerequisites

- Docker and `docker compose` (v2) must be installed and the current user must belong to the `docker` group.
- Ports `3000` (Grafana), `9091` (Prometheus), `8123` (ClickHouse HTTP), `3100` (Loki) must be free.

---

## Disabling Monitoring

Omit the monitoring config or set `start_monitoring=False`. All actor operations are safely skipped.