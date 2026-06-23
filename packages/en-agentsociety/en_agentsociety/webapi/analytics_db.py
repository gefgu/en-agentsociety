"""
Unified analytics read layer for the web API.

Tries DuckDB first (local files), then ClickHouse.
All read operations are async (DuckDB calls are wrapped in asyncio.to_thread).

DuckDB files are at {data_dir}/duckdb/{exp_id}.duckdb (read-only).
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = ["AnalyticsDB"]

logger = logging.getLogger(__name__)


class AnalyticsDB:
    """Async read-only analytics query layer backed by DuckDB (with optional ClickHouse)."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = Path(data_dir)
        self._duckdb_dir = self.data_dir / "duckdb"

    def _duckdb_path(self, exp_id: str) -> Path:
        return self._duckdb_dir / f"{exp_id}.duckdb"

    def _duckdb_exists(self, exp_id: str) -> bool:
        return self._duckdb_path(exp_id).exists()

    # ------------------------------------------------------------------
    # DuckDB helpers — run synchronously in a thread
    # ------------------------------------------------------------------

    def _duckdb_query_sync(
        self, exp_id: str, sql: str, params: Optional[list] = None
    ) -> List[Dict[str, Any]]:
        """Open DuckDB file in read-only mode and run a query."""
        try:
            import duckdb  # type: ignore
        except ImportError:
            logger.warning("duckdb package not installed; analytics queries unavailable")
            return []

        db_path = self._duckdb_path(exp_id)
        if not db_path.exists():
            return []
        try:
            conn = duckdb.connect(str(db_path), read_only=True)
            try:
                if params:
                    result = conn.execute(sql, params)
                else:
                    result = conn.execute(sql)
                cols = [desc[0] for desc in result.description]
                return [dict(zip(cols, row)) for row in result.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"AnalyticsDB DuckDB query error ({db_path}): {e}")
            return []

    def _duckdb_query_one_sync(
        self, exp_id: str, sql: str, params: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        rows = self._duckdb_query_sync(exp_id, sql, params)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def query_agent_profiles(
        self, exp_id: str, agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Return agent profile rows. Optionally filter by agent_id."""
        if not self._duckdb_exists(exp_id):
            return []
        if agent_id is not None:
            sql = "SELECT * FROM agent_profile WHERE exp_id = ? AND agent_id = ?"
            params = [exp_id, agent_id]
        else:
            sql = "SELECT * FROM agent_profile WHERE exp_id = ?"
            params = [exp_id]
        return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, params)

    async def query_agent_statuses(
        self,
        exp_id: str,
        day: Optional[int] = None,
        t: Optional[float] = None,
        agent_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return agent status rows. Filter by day/t or agent_id."""
        if not self._duckdb_exists(exp_id):
            return []
        conditions = ["exp_id = ?"]
        params: list = [exp_id]
        if agent_id is not None:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if day is not None:
            conditions.append("day = ?")
            params.append(day)
        if t is not None:
            conditions.append("t = ?")
            params.append(t)
        sql = (
            f"SELECT * FROM step_agent_status WHERE {' AND '.join(conditions)} "
            "ORDER BY day, t"
        )
        return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, params)

    async def query_timeline(self, exp_id: str) -> List[Dict[str, Any]]:
        """Return unique (day, t) pairs from step_agent_status, ordered by day/t."""
        if not self._duckdb_exists(exp_id):
            return []
        sql = (
            "SELECT day, t FROM step_agent_status WHERE exp_id = ? "
            "GROUP BY day, t ORDER BY day, t"
        )
        return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, [exp_id])

    async def query_metrics(
        self, exp_id: str, key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return metric rows for the experiment, optionally filtered by key."""
        if not self._duckdb_exists(exp_id):
            return []
        if key is not None:
            sql = "SELECT * FROM metric WHERE exp_id = ? AND key = ? ORDER BY step"
            params = [exp_id, key]
        else:
            sql = "SELECT * FROM metric WHERE exp_id = ? ORDER BY key, step"
            params = [exp_id]
        return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, params)

    async def query_experiment_info(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Return experiment_info row from DuckDB for the given experiment."""
        if not self._duckdb_exists(exp_id):
            return None
        sql = "SELECT * FROM experiment_info WHERE id = ? LIMIT 1"
        return await asyncio.to_thread(self._duckdb_query_one_sync, exp_id, sql, [exp_id])

    async def query_block_timeline(
        self, exp_id: str, agent_id: int
    ) -> List[Dict[str, Any]]:
        """Return prompt_response rows for one agent, ordered by simulation_step then timestamp."""
        if not self._duckdb_exists(exp_id):
            return []
        sql = (
            "SELECT simulation_step, block_name, func_name, prompt, response, detail_available "
            "FROM prompt_responses "
            "WHERE exp_id = ? AND agent_id = ? "
            "ORDER BY simulation_step, timestamp"
        )
        return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, [exp_id, agent_id])

    async def query_daily_schedule(
        self,
        exp_id: str,
        agent_id: int,
        day: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return daily_schedule dict from the latest step_agent_status for a given day."""
        if not self._duckdb_exists(exp_id):
            return None
        conditions = ["exp_id = ?", "agent_id = ?"]
        params: list = [exp_id, agent_id]
        if day is not None:
            conditions.append("day = ?")
            params.append(day)
        sql = (
            f"SELECT status, day FROM step_agent_status WHERE {' AND '.join(conditions)} "
            "ORDER BY day DESC, t DESC LIMIT 1"
        )
        row = await asyncio.to_thread(self._duckdb_query_one_sync, exp_id, sql, params)
        if not row:
            return None
        status_val = row.get("status", "{}")
        if isinstance(status_val, str):
            try:
                status_val = json.loads(status_val)
            except Exception:
                return None
        schedule = status_val.get("daily_schedule")
        return schedule if isinstance(schedule, dict) and schedule.get("blocks") else None

    def duckdb_exists(self, exp_id: str) -> bool:
        return self._duckdb_exists(exp_id)
