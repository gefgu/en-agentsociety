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
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = ["AnalyticsDB"]

logger = logging.getLogger(__name__)


class AnalyticsDB:
    """Async read-only analytics query layer backed by DuckDB (with optional ClickHouse)."""

    def __init__(self, data_dir: str, clickhouse_config: Optional[Any] = None) -> None:
        self.data_dir = Path(data_dir)
        self._duckdb_dir = self.data_dir / "duckdb"
        self._ch_config = clickhouse_config
        if clickhouse_config is not None:
            # Probe connectivity once at startup; each query gets its own client
            if self._make_ch_client() is not None:
                logger.info("AnalyticsDB ClickHouse connectivity verified")
            else:
                logger.info("ClickHouse unavailable for analytics reads")

    # ------------------------------------------------------------------
    # ClickHouse helpers
    # ------------------------------------------------------------------

    def _make_ch_client(self) -> Optional[Any]:
        """Create a fresh ClickHouse client. Called per-thread to avoid shared-session errors."""
        if self._ch_config is None:
            return None
        try:
            import clickhouse_connect  # type: ignore
            return clickhouse_connect.get_client(
                host=self._ch_config.host,
                port=self._ch_config.port,
                username=self._ch_config.username,
                password=self._ch_config.password,
                database=self._ch_config.database,
            )
        except Exception as e:
            logger.warning(f"ClickHouse client creation failed: {e}")
            return None

    def _ch_query_all_experiments_sync(self, allowed_tenant_ids: tuple) -> list[dict[str, Any]]:
        ch = self._make_ch_client()
        if ch is None:
            return []
        try:
            placeholders = ", ".join(f"'{t}'" for t in allowed_tenant_ids)
            result = ch.query(
                f"SELECT * FROM experiment_info FINAL WHERE tenant_id IN ({placeholders})"
            )
            cols = result.column_names
            return [dict(zip(cols, row)) for row in result.result_rows]
        except Exception as e:
            logger.warning(f"ClickHouse experiment list query failed: {e}")
            return []

    def _ch_query_one_experiment_sync(self, exp_id: str) -> Optional[dict[str, Any]]:
        ch = self._make_ch_client()
        if ch is None:
            return None
        try:
            result = ch.query(
                "SELECT * FROM experiment_info WHERE id = {exp_id:String} "
                "ORDER BY updated_at DESC LIMIT 1",
                parameters={"exp_id": exp_id},
            )
            cols = result.column_names
            rows = [dict(zip(cols, row)) for row in result.result_rows]
            return rows[0] if rows else None
        except Exception as e:
            logger.warning(f"ClickHouse experiment query failed ({exp_id}): {e}")
            return None

    # ------------------------------------------------------------------
    # DuckDB helpers — run synchronously in a thread
    # ------------------------------------------------------------------

    def _duckdb_path(self, exp_id: str) -> Path:
        return self._duckdb_dir / f"{exp_id}.duckdb"

    def _duckdb_exists(self, exp_id: str) -> bool:
        return self._duckdb_path(exp_id).exists()

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

    def _list_all_duckdb_exp_ids(self) -> list[str]:
        """Return all experiment IDs found as DuckDB files (UUID-named only)."""
        if not self._duckdb_dir.exists():
            return []
        result = []
        for p in self._duckdb_dir.glob("*.duckdb"):
            try:
                uuid.UUID(p.stem)
                result.append(p.stem)
            except ValueError:
                pass
        return result

    def _duckdb_query_one_exp_sync(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Return the latest experiment_info row from a single DuckDB file."""
        sql = "SELECT * FROM experiment_info ORDER BY updated_at DESC LIMIT 1"
        return self._duckdb_query_one_sync(exp_id, sql)

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def query_all_experiment_infos(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Scan all DuckDB files + ClickHouse concurrently; return merged list."""
        allowed = {tenant_id, "", "default"}

        exp_ids = await asyncio.to_thread(self._list_all_duckdb_exp_ids)

        duckdb_tasks = [
            asyncio.to_thread(self._duckdb_query_one_exp_sync, eid)
            for eid in exp_ids
        ]
        ch_task = asyncio.to_thread(
            self._ch_query_all_experiments_sync, tuple(allowed)
        )

        all_done = await asyncio.gather(*duckdb_tasks, ch_task, return_exceptions=True)
        duckdb_results = all_done[:-1]
        ch_result = all_done[-1]

        merged: Dict[str, Dict[str, Any]] = {}

        for row in duckdb_results:
            if isinstance(row, Exception) or row is None:
                continue
            if row.get("tenant_id", "") not in allowed:
                continue
            merged[str(row["id"])] = row

        if not isinstance(ch_result, Exception):
            for row in ch_result:
                if row.get("tenant_id", "") not in allowed:
                    continue
                rid = str(row["id"])
                if rid not in merged:
                    merged[rid] = row
                else:
                    existing_ts = merged[rid].get("updated_at")
                    new_ts = row.get("updated_at")
                    if new_ts and existing_ts and new_ts > existing_ts:
                        merged[rid] = row

        return sorted(
            merged.values(),
            key=lambda r: r.get("created_at") or "",
            reverse=True,
        )

    async def query_experiment_info(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Return the latest experiment_info for the given exp_id (DuckDB first, then ClickHouse)."""
        row = await asyncio.to_thread(self._duckdb_query_one_exp_sync, exp_id)
        if row is not None:
            return row
        return await asyncio.to_thread(self._ch_query_one_experiment_sync, exp_id)

    def _ch_query_agent_profiles_sync(
        self, exp_id: str, agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        ch = self._make_ch_client()
        if ch is None:
            return []
        try:
            if agent_id is not None:
                result = ch.query(
                    "SELECT agent_id, name, profile FROM agent_profile "
                    "WHERE exp_id = {exp_id:String} AND agent_id = {agent_id:Int32}",
                    parameters={"exp_id": exp_id, "agent_id": agent_id},
                )
            else:
                result = ch.query(
                    "SELECT agent_id, name, profile FROM agent_profile "
                    "WHERE exp_id = {exp_id:String}",
                    parameters={"exp_id": exp_id},
                )
            cols = result.column_names
            return [dict(zip(cols, row)) for row in result.result_rows]
        except Exception as e:
            logger.warning(f"ClickHouse agent_profile query failed ({exp_id}): {e}")
            return []

    def _ch_query_block_timeline_sync(
        self, exp_id: str, agent_id: int
    ) -> List[Dict[str, Any]]:
        ch = self._make_ch_client()
        if ch is None:
            return []
        try:
            result = ch.query(
                "SELECT simulation_step, block_name, func_name, prompt, response, "
                "0 AS detail_available "
                "FROM prompt_responses "
                "WHERE exp_id = {exp_id:String} AND agent_id = {agent_id:Int32} "
                "ORDER BY simulation_step, timestamp",
                parameters={"exp_id": exp_id, "agent_id": agent_id},
            )
            cols = result.column_names
            return [dict(zip(cols, row)) for row in result.result_rows]
        except Exception as e:
            logger.warning(f"ClickHouse block_timeline query failed ({exp_id}/{agent_id}): {e}")
            return []

    async def query_agent_profiles(
        self, exp_id: str, agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Return agent profile rows. Optionally filter by agent_id."""
        if self._duckdb_exists(exp_id):
            if agent_id is not None:
                sql = "SELECT * FROM agent_profile WHERE exp_id = ? AND agent_id = ?"
                params = [exp_id, agent_id]
            else:
                sql = "SELECT * FROM agent_profile WHERE exp_id = ?"
                params = [exp_id]
            return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, params)
        return await asyncio.to_thread(self._ch_query_agent_profiles_sync, exp_id, agent_id)

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

    async def query_block_timeline(
        self, exp_id: str, agent_id: int
    ) -> List[Dict[str, Any]]:
        """Return prompt_response rows for one agent, ordered by simulation_step then timestamp."""
        if self._duckdb_exists(exp_id):
            sql = (
                "SELECT simulation_step, block_name, func_name, prompt, response, detail_available "
                "FROM prompt_responses "
                "WHERE exp_id = ? AND agent_id = ? "
                "ORDER BY simulation_step, timestamp"
            )
            return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, [exp_id, agent_id])
        return await asyncio.to_thread(self._ch_query_block_timeline_sync, exp_id, agent_id)

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

    def _ch_query_location_timeline_sync(
        self, exp_id: str, agent_id: int
    ) -> List[Dict[str, Any]]:
        ch = self._make_ch_client()
        if ch is None:
            return []
        try:
            result = ch.query(
                "SELECT simulation_step, location_type FROM agent_location_type "
                "WHERE exp_id = {exp_id:String} AND agent_id = {agent_id:Int32} "
                "ORDER BY simulation_step",
                parameters={"exp_id": exp_id, "agent_id": agent_id},
            )
            cols = result.column_names
            return [dict(zip(cols, row)) for row in result.result_rows]
        except Exception as e:
            logger.warning(f"ClickHouse location_timeline query failed ({exp_id}/{agent_id}): {e}")
            return []

    async def query_agent_location_timeline(
        self, exp_id: str, agent_id: int
    ) -> List[Dict[str, Any]]:
        """Return location type change events for one agent, ordered by simulation_step."""
        if self._duckdb_exists(exp_id):
            sql = (
                "SELECT simulation_step, location_type FROM agent_location_type "
                "WHERE exp_id = ? AND agent_id = ? ORDER BY simulation_step"
            )
            return await asyncio.to_thread(self._duckdb_query_sync, exp_id, sql, [exp_id, agent_id])
        return await asyncio.to_thread(self._ch_query_location_timeline_sync, exp_id, agent_id)

    def duckdb_exists(self, exp_id: str) -> bool:
        return self._duckdb_exists(exp_id)
