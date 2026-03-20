# `logger/` — Structured Logger

This package provides a project-wide structured logger with optional OpenTelemetry (OTLP) export support.

---

## Files

| File | Purpose |
|---|---|
| `__init__.py` | `get_logger()`, `set_logger_level()`, `set_exp_id()`, `attach_otlp_handler()` |

---

## API

```python
from agentsociety.logger import get_logger, set_logger_level, set_exp_id

logger = get_logger()

logger.debug("Detailed tracing info")
logger.info("Simulation started")
logger.warning("Missing configuration key, using default")
logger.error("LLM request failed", exc_info=True)

# Set log level globally
set_logger_level("DEBUG")

# Tag all log records with the current experiment ID
set_exp_id("exp-abc123")
```

---

## OTLP Export (OpenTelemetry)

When the performance monitoring stack is running, logs can be exported to Loki via OTLP:

```python
from agentsociety.logger import attach_otlp_handler

attach_otlp_handler(endpoint="http://localhost:4318/v1/logs")
```

This enables log correlation in Grafana alongside metrics from Prometheus and ClickHouse.

---

## Log Format

Log records include:

- ISO 8601 timestamp
- Log level
- Module and function name
- Experiment ID (when set via `set_exp_id`)
- Message

Example:
```
2026-03-12 14:23:01.234 | INFO | simulation.simulationengine:run:342 | [exp-abc123] Simulation started
```

---

## Notes

- The logger is a singleton — `get_logger()` always returns the same configured instance.
- `set_logger_level("WARNING")` is called automatically for production deployments controlled by `Config.logging_level`.
- All Ray workers inherit the logger configuration at startup.
