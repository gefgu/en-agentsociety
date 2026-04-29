"""
Per-experiment SQLite connection utility for the web API.

Opens individual SQLite files (one per experiment) to read/write
interactive data: dialogs, surveys, pending messages, global prompts.
Files are at {home_dir}/sqlite/{exp_id}.db.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = ["PerExperimentSQLite"]

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PerExperimentSQLite:
    """Opens per-experiment SQLite files for dialog/survey/pending data."""

    def __init__(self, home_dir: str) -> None:
        self.home_dir = Path(home_dir)
        self._sqlite_dir = self.home_dir / "sqlite"

    def _db_path(self, exp_id: str) -> Path:
        return self._sqlite_dir / f"{exp_id}.db"

    def _db_exists(self, exp_id: str) -> bool:
        return self._db_path(exp_id).exists()

    # ------------------------------------------------------------------
    # Internal helpers — all run in a thread via asyncio.to_thread
    # ------------------------------------------------------------------

    def _run_query_sync(self, db_path: Path, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT and return list of dicts (column → value)."""
        import sqlite3

        try:
            with sqlite3.connect(str(db_path), timeout=10) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"PerExperimentSQLite query error ({db_path}): {e}")
            return []

    def _run_write_sync(self, db_path: Path, sql: str, params: tuple = ()) -> bool:
        """Execute an INSERT/UPDATE and return success flag."""
        import sqlite3

        try:
            with sqlite3.connect(str(db_path), timeout=10) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute(sql, params)
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"PerExperimentSQLite write error ({db_path}): {e}")
            return False

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def query_dialogs(
        self, exp_id: str, agent_id: int
    ) -> List[Dict[str, Any]]:
        """Return all dialog rows for a given agent (ordered by day, t)."""
        if not self._db_exists(exp_id):
            return []
        db_path = self._db_path(exp_id)
        sql = (
            "SELECT * FROM dialog WHERE id = ? ORDER BY day, t"
        )
        return await asyncio.to_thread(self._run_query_sync, db_path, sql, (agent_id,))

    async def query_pending_dialogs(
        self, exp_id: str, agent_id: int, unprocessed_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Return pending dialog rows for a given agent."""
        if not self._db_exists(exp_id):
            return []
        db_path = self._db_path(exp_id)
        if unprocessed_only:
            sql = (
                "SELECT * FROM pending_dialog WHERE agent_id = ? AND processed = 0 "
                "ORDER BY created_at"
            )
        else:
            sql = "SELECT * FROM pending_dialog WHERE agent_id = ? ORDER BY created_at"
        return await asyncio.to_thread(self._run_query_sync, db_path, sql, (agent_id,))

    async def write_pending_dialog(
        self,
        exp_id: str,
        agent_id: int,
        day: int,
        t: float,
        content: str,
    ) -> bool:
        """Insert a pending dialog into the per-experiment SQLite."""
        if not self._db_exists(exp_id):
            logger.warning(
                f"Per-experiment SQLite not found for exp_id={exp_id}; "
                f"pending dialog will not be persisted."
            )
            return False
        db_path = self._db_path(exp_id)
        sql = (
            "INSERT INTO pending_dialog (experiment_id, agent_id, day, t, content, "
            "created_at, processed) VALUES (?, ?, ?, ?, ?, ?, 0)"
        )
        params = (exp_id, agent_id, day, t, content, _utc_now().isoformat())
        return await asyncio.to_thread(self._run_write_sync, db_path, sql, params)

    async def query_surveys(
        self, exp_id: str, agent_id: int
    ) -> List[Dict[str, Any]]:
        """Return all survey rows for a given agent (ordered by day, t)."""
        if not self._db_exists(exp_id):
            return []
        db_path = self._db_path(exp_id)
        sql = "SELECT * FROM survey WHERE id = ? ORDER BY day, t"
        return await asyncio.to_thread(self._run_query_sync, db_path, sql, (agent_id,))

    async def query_pending_surveys(
        self, exp_id: str, agent_id: int, unprocessed_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Return pending survey rows for a given agent."""
        if not self._db_exists(exp_id):
            return []
        db_path = self._db_path(exp_id)
        if unprocessed_only:
            sql = (
                "SELECT * FROM pending_survey WHERE agent_id = ? AND processed = 0 "
                "ORDER BY created_at"
            )
        else:
            sql = "SELECT * FROM pending_survey WHERE agent_id = ? ORDER BY created_at"
        return await asyncio.to_thread(self._run_query_sync, db_path, sql, (agent_id,))

    async def write_pending_survey(
        self,
        exp_id: str,
        agent_id: int,
        day: int,
        t: float,
        survey_id: uuid.UUID,
        data: Any,
    ) -> bool:
        """Insert a pending survey into the per-experiment SQLite."""
        if not self._db_exists(exp_id):
            logger.warning(
                f"Per-experiment SQLite not found for exp_id={exp_id}; "
                f"pending survey will not be persisted."
            )
            return False
        db_path = self._db_path(exp_id)
        data_json = json.dumps(data) if not isinstance(data, str) else data
        sql = (
            "INSERT INTO pending_survey (experiment_id, agent_id, day, t, survey_id, "
            "data, created_at, processed) VALUES (?, ?, ?, ?, ?, ?, ?, 0)"
        )
        params = (exp_id, agent_id, day, t, str(survey_id), data_json, _utc_now().isoformat())
        return await asyncio.to_thread(self._run_write_sync, db_path, sql, params)

    async def query_global_prompt(
        self, exp_id: str, day: int, t: float
    ) -> Optional[Dict[str, Any]]:
        """Return the global prompt for a given day/t."""
        if not self._db_exists(exp_id):
            return None
        db_path = self._db_path(exp_id)
        sql = "SELECT * FROM global_prompt WHERE day = ? AND t = ? LIMIT 1"
        rows = await asyncio.to_thread(self._run_query_sync, db_path, sql, (day, t))
        return rows[0] if rows else None

    async def query_experiment_info(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Return the experiment_info row from the per-experiment SQLite."""
        if not self._db_exists(exp_id):
            return None
        db_path = self._db_path(exp_id)
        sql = "SELECT * FROM experiment_info WHERE experiment_id = ? LIMIT 1"
        rows = await asyncio.to_thread(self._run_query_sync, db_path, sql, (exp_id,))
        return rows[0] if rows else None

    async def _run_async_all_dialogs(self, exp_id: str) -> List[Dict[str, Any]]:
        """Return all dialog rows for an experiment (all agents)."""
        if not self._db_exists(exp_id):
            return []
        db_path = self._db_path(exp_id)
        sql = "SELECT * FROM dialog ORDER BY day, t"
        return await asyncio.to_thread(self._run_query_sync, db_path, sql)

    async def _run_async_all_surveys(self, exp_id: str) -> List[Dict[str, Any]]:
        """Return all survey rows for an experiment (all agents)."""
        if not self._db_exists(exp_id):
            return []
        db_path = self._db_path(exp_id)
        sql = "SELECT * FROM survey ORDER BY day, t"
        return await asyncio.to_thread(self._run_query_sync, db_path, sql)
