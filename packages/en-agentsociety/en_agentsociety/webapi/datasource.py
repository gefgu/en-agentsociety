"""Unified analytics source for mobility data.

The web API serves chart/metric data from the per-experiment ``step_agent_status``
and ``agent_location_type`` tables, which are written to either ClickHouse (prod)
or DuckDB (dev / portable export). Both backends share the same schema (see the
``database/migrations/*.sql`` files), so a single ``SELECT * WHERE exp_id = ?``
yields the same columns from either.

The strategy is: probe ClickHouse first; if there is no valid connection, fall
back to a DuckDB file (either the experiment's local file under ``data_dir`` or a
``.duckdb`` file the user uploads through the UI).
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

__all__ = [
    "clickhouse_available",
    "load_experiment_frames",
    "resolve_local_duckdb_path",
]

logger = logging.getLogger(__name__)

STATUS_TABLE = "step_agent_status"
LOCATION_TYPE_TABLE = "agent_location_type"

# Short cache so we do not re-probe ClickHouse on every request.
_CLICKHOUSE_PROBE_TTL = 30.0
_clickhouse_probe: tuple[float, bool] | None = None


def clickhouse_available() -> bool:
    """Return True iff a ClickHouse connection can be established and queried.

    Never raises — a missing/unreachable ClickHouse simply returns False so the
    caller can fall back to DuckDB.
    """
    global _clickhouse_probe
    now = time.monotonic()
    if _clickhouse_probe is not None and now - _clickhouse_probe[0] < _CLICKHOUSE_PROBE_TTL:
        return _clickhouse_probe[1]

    available = False
    try:
        from .clickhouse import get_clickhouse_client

        client = get_clickhouse_client()
        client.command("SELECT 1")
        available = True
    except Exception as exc:  # noqa: BLE001 - any failure means "not available"
        logger.info("ClickHouse not available, will fall back to DuckDB: %s", exc)

    _clickhouse_probe = (now, available)
    return available


def _clickhouse_table_df(client, table: str, exp_id: str) -> pd.DataFrame:
    result = client.query(
        f"SELECT * FROM {table} WHERE exp_id = {{exp_id:String}}",
        parameters={"exp_id": exp_id},
    )
    return pd.DataFrame(
        [dict(zip(result.column_names, row)) for row in result.result_rows]
    )


def _duckdb_table_df(conn, table: str, exp_id: str) -> pd.DataFrame:
    cursor = conn.execute(f"SELECT * FROM {table} WHERE exp_id = ?", [exp_id])
    columns = [desc[0] for desc in (cursor.description or [])]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def load_experiment_frames(
    exp_id: str,
    *,
    client=None,
    duckdb_path: Optional[str | Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load ``(step_agent_status, agent_location_type)`` frames for an experiment.

    Provide exactly one source: a ClickHouse ``client`` or a ``duckdb_path``.
    """
    if client is not None:
        return (
            _clickhouse_table_df(client, STATUS_TABLE, exp_id),
            _clickhouse_table_df(client, LOCATION_TYPE_TABLE, exp_id),
        )
    if duckdb_path is not None:
        import duckdb

        path = str(duckdb_path)
        conn = duckdb.connect(path, read_only=True)
        try:
            return (
                _duckdb_table_df(conn, STATUS_TABLE, exp_id),
                _duckdb_table_df(conn, LOCATION_TYPE_TABLE, exp_id),
            )
        finally:
            conn.close()
    raise ValueError("load_experiment_frames requires either client or duckdb_path")


def resolve_local_duckdb_path(request, exp_id: str) -> Optional[Path]:
    """Best-effort lookup of an experiment's local DuckDB file via AnalyticsDB."""
    analytics_db = getattr(request.app.state, "analytics_db", None)
    if analytics_db is None:
        return None
    try:
        path = analytics_db._duckdb_path(exp_id)  # noqa: SLF001 - internal helper
    except Exception:  # noqa: BLE001
        return None
    return path if path.exists() else None
