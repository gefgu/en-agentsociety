import asyncio
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Dict, List, Any
import uuid

import yaml
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, update, text, event
from sqlalchemy.exc import OperationalError, DatabaseError as SADatabaseError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..logger import get_logger
from ..utils.decorators import lock_decorator
from .model import (
    Experiment,
    agent_survey,
    agent_dialog,
    global_prompt,
    pending_dialog,
    pending_survey,
    experiment_info,
)
from ._base import Base, TABLE_PREFIX
from .type import (
    StorageDialog,
    StorageExpInfo,
    StorageGlobalPrompt,
    StoragePendingDialog,
    StoragePendingSurvey,
    StorageSurvey,
)

__all__ = ["DatabaseWriter", "DatabaseConfig"]

# Simple table names — no per-experiment prefix since each experiment has its own SQLite file
_TABLE_NAMES = {
    "dialog": "dialog",
    "survey": "survey",
    "global_prompt": "global_prompt",
    "pending_dialog": "pending_dialog",
    "pending_survey": "pending_survey",
    "experiment_info": "experiment_info",
}


class DatabaseConfig(BaseModel):
    """Database configuration class supporting multiple database types."""

    enabled: bool = Field(True)
    """Whether database storage is enabled"""

    db_type: Literal["postgresql", "sqlite"] = Field("sqlite")
    """Database type"""

    pg_dsn: Optional[str] = Field(None)
    """Database connection string (PostgreSQL)"""

    @model_validator(mode="after")
    def validate_config(self):
        if not self.enabled:
            return self
        if self.db_type == "postgresql" and not self.pg_dsn:
            raise ValueError("PostgreSQL DSN is required")
        return self

    def get_dsn(self, sqlite_path: Path):
        """Create async SQLAlchemy engine based on configuration"""
        if self.db_type == "postgresql":
            assert self.pg_dsn is not None
            if self.pg_dsn.startswith("postgresql://"):
                async_dsn = self.pg_dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
            else:
                async_dsn = self.pg_dsn
            return async_dsn
        elif self.db_type == "sqlite":
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{sqlite_path}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")


def _create_async_engine_from_config(config: DatabaseConfig, sqlite_path: Path):
    dsn = config.get_dsn(sqlite_path)
    if config.db_type == "sqlite":
        engine = create_async_engine(
            dsn,
            connect_args={"timeout": 30},
            pool_pre_ping=True,
        )

        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

        return engine

    return create_async_engine(dsn, pool_pre_ping=True)


def _is_sqlite_corruption_error(error: Exception, config: DatabaseConfig) -> bool:
    if config.db_type != "sqlite":
        return False
    if not isinstance(error, (OperationalError, SADatabaseError)):
        return False
    error_msg = str(error).lower()
    corruption_indicators = [
        "file is not a database",
        "not a database",
        "unable to open database",
    ]
    return any(indicator in error_msg for indicator in corruption_indicators)


def _rename_corrupt_sqlite(sqlite_path: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    new_path = sqlite_path.parent / f"{sqlite_path.name}.corrupt.{timestamp}"
    sqlite_path.rename(new_path)
    get_logger().warning(f"Renamed corrupted SQLite file from {sqlite_path} to {new_path}")


async def _create_tables(exp_id: str, config: DatabaseConfig, sqlite_path: Path):
    """Create simplified per-experiment tables."""
    engine = _create_async_engine_from_config(config, sqlite_path)

    async def _create_tables_impl(conn):
        table_functions = {
            "dialog": (agent_dialog, "dialog"),
            "survey": (agent_survey, "survey"),
            "global_prompt": (global_prompt, "global_prompt"),
            "pending_dialog": (pending_dialog, "pending_dialog"),
            "pending_survey": (pending_survey, "pending_survey"),
            "experiment_info": (experiment_info, "experiment_info"),
        }

        for table_type, (table_func, table_name) in table_functions.items():
            table_obj, _ = table_func(table_name)
            await conn.run_sync(table_obj.create, checkfirst=True)
            get_logger().debug(f"Created {config.db_type} table: {table_name}")

    try:
        try:
            async with engine.begin() as conn:
                await _create_tables_impl(conn)
        except Exception as e:
            if _is_sqlite_corruption_error(e, config):
                get_logger().warning(f"Detected SQLite corruption, attempting recovery: {e}")
                _rename_corrupt_sqlite(sqlite_path)
                retry_engine = _create_async_engine_from_config(config, sqlite_path)
                try:
                    async with retry_engine.begin() as conn:
                        await _create_tables_impl(conn)
                    get_logger().info("Successfully recovered from SQLite corruption")
                finally:
                    await retry_engine.dispose()
            else:
                raise
    finally:
        await engine.dispose()


class DatabaseWriter:
    def __init__(self, tenant_id: str, exp_id: str, config: DatabaseConfig, home_dir: str):
        """
        Initialize database writer.

        - **Args**:
            - `tenant_id` (str): Tenant ID.
            - `exp_id` (str): Experiment ID.
            - `config` (DatabaseConfig): Database configuration.
            - `home_dir` (str): Home directory. sqlite will be stored in home_dir/sqlite/<exp_id>.db
        """
        self.tenant_id = tenant_id
        self.exp_id = exp_id
        self._config = config
        self._lock = asyncio.Lock()
        self._sqlite_path = Path(home_dir) / "sqlite" / f"{exp_id}.db"
        self._engine = _create_async_engine_from_config(config, sqlite_path=self._sqlite_path)
        self._async_session = async_sessionmaker(self._engine, expire_on_commit=False)

        # Setup storage path
        self._storage_path = Path(home_dir) / "exps" / tenant_id / exp_id
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Cache table objects
        self._tables = {}
        self._init_tables()

    async def init(self):
        """Initialize database tables"""
        await self._create_tables()

    def _init_tables(self):
        """Initialize table object cache with simplified names."""
        table_functions = {
            "dialog": (agent_dialog, "dialog"),
            "survey": (agent_survey, "survey"),
            "global_prompt": (global_prompt, "global_prompt"),
            "pending_dialog": (pending_dialog, "pending_dialog"),
            "pending_survey": (pending_survey, "pending_survey"),
            "experiment_info": (experiment_info, "experiment_info"),
        }

        for table_type, (table_func, table_name) in table_functions.items():
            table_obj, columns = table_func(table_name)
            self._tables[table_type] = {"table": table_obj, "columns": columns}

    async def _create_tables(self):
        """Create tables"""
        await _create_tables(self.exp_id, self._config, self._sqlite_path)

    def _get_insert_func(self):
        """Get insert function based on database type"""
        if self._config.db_type == "postgresql":
            return pg_insert
        elif self._config.db_type == "sqlite":
            return sqlite_insert
        else:
            raise ValueError(f"Unsupported database type: {self._config.db_type}")

    def _is_sqlite_lock_error(self, error: Exception) -> bool:
        if self._config.db_type != "sqlite":
            return False
        if not isinstance(error, OperationalError):
            return False
        err_msg = str(error).lower()
        return "database is locked" in err_msg or "database table is locked" in err_msg

    def _is_sqlite_corruption_error(self, error: Exception, config: DatabaseConfig) -> bool:
        if config.db_type != "sqlite":
            return False
        if not isinstance(error, (OperationalError, SADatabaseError)):
            return False
        err_msg = str(error).lower()
        return any(s in err_msg for s in ["file is not a database", "not a database", "unable to open database"])

    async def _recover_sqlite_db(self) -> None:
        """Recover from a corrupt SQLite file mid-simulation."""
        get_logger().warning(
            f"SQLite database at {self._sqlite_path} is corrupt. "
            f"Renaming corrupt file and creating a fresh database. "
            f"Data written before this point may be lost."
        )
        await self._engine.dispose()
        _rename_corrupt_sqlite(self._sqlite_path)
        await _create_tables(self.exp_id, self._config, self._sqlite_path)
        self._engine = _create_async_engine_from_config(self._config, self._sqlite_path)
        self._async_session = async_sessionmaker(self._engine, expire_on_commit=False)
        get_logger().info(f"SQLite recovery complete. New database at {self._sqlite_path}.")

    @property
    def exp_info_file(self):
        """Experiment info file path"""
        return self._storage_path / "experiment_info.yaml"

    @property
    def storage_path(self):
        """Storage path"""
        return self._storage_path

    # ==================== WRITE METHODS ====================

    @lock_decorator
    async def write_dialogs(self, rows: list[StorageDialog]):
        table_obj = self._tables["dialog"]["table"]
        data = [
            {
                "experiment_id": self.exp_id,
                "id": row.id,
                "day": row.day,
                "t": row.t,
                "type": row.type,
                "speaker": row.speaker,
                "content": row.content,
                "created_at": row.created_at,
            }
            for row in rows
        ]
        recovered = False
        while True:
            insert_func = self._get_insert_func()
            async with self._async_session() as session:
                try:
                    stmt = insert_func(table_obj).values(data)
                    await session.execute(stmt)
                    await session.commit()
                    get_logger().debug(f"Inserted {len(rows)} dialog records")
                    return
                except Exception as e:
                    await session.rollback()
                    if not recovered and self._is_sqlite_corruption_error(e, self._config):
                        get_logger().warning("SQLite corruption detected; recovering and retrying write...")
                        await self._recover_sqlite_db()
                        recovered = True
                        continue
                    get_logger().error(f"Error writing dialogs: {e}")
                    if recovered:
                        get_logger().warning("Write still failed after recovery. Data lost for this batch.")
                        return
                    raise

    @lock_decorator
    async def write_surveys(self, rows: list[StorageSurvey]):
        table_obj = self._tables["survey"]["table"]
        data = [
            {
                "experiment_id": self.exp_id,
                "id": row.id,
                "day": row.day,
                "t": row.t,
                "survey_id": row.survey_id,
                "result": row.result,
                "created_at": row.created_at,
            }
            for row in rows
        ]
        recovered = False
        while True:
            insert_func = self._get_insert_func()
            async with self._async_session() as session:
                try:
                    stmt = insert_func(table_obj).values(data)
                    await session.execute(stmt)
                    await session.commit()
                    get_logger().debug(f"Inserted {len(rows)} survey records")
                    return
                except Exception as e:
                    await session.rollback()
                    if not recovered and self._is_sqlite_corruption_error(e, self._config):
                        get_logger().warning("SQLite corruption detected; recovering and retrying write...")
                        await self._recover_sqlite_db()
                        recovered = True
                        continue
                    get_logger().error(f"Error writing surveys: {e}")
                    if recovered:
                        get_logger().warning("Write still failed after recovery. Data lost for this batch.")
                        return
                    raise

    @lock_decorator
    async def write_global_prompt(self, prompt_info: StorageGlobalPrompt):
        table_obj = self._tables["global_prompt"]["table"]
        data = {
            "experiment_id": self.exp_id,
            "day": prompt_info.day,
            "t": prompt_info.t,
            "prompt": prompt_info.prompt,
            "created_at": prompt_info.created_at,
        }
        recovered = False
        while True:
            insert_func = self._get_insert_func()
            async with self._async_session() as session:
                try:
                    stmt = insert_func(table_obj).values([data])
                    await session.execute(stmt)
                    await session.commit()
                    get_logger().debug("Inserted global prompt record")
                    return
                except Exception as e:
                    await session.rollback()
                    if not recovered and self._is_sqlite_corruption_error(e, self._config):
                        get_logger().warning("SQLite corruption detected; recovering and retrying write...")
                        await self._recover_sqlite_db()
                        recovered = True
                        continue
                    get_logger().error(f"Error writing global prompt: {e}")
                    if recovered:
                        get_logger().warning("Write still failed after recovery. Data lost for this batch.")
                        return
                    raise

    @lock_decorator
    async def update_exp_info(self, exp_info: StorageExpInfo):
        # Save to local YAML (idempotent)
        with open(self.exp_info_file, "w") as f:
            yaml.dump(exp_info.model_dump(), f)

        table_obj = self._tables["experiment_info"]["table"]
        data = {
            "experiment_id": self.exp_id,
            "tenant_id": exp_info.tenant_id,
            "name": exp_info.name,
            "num_day": exp_info.num_day,
            "status": exp_info.status,
            "cur_day": exp_info.cur_day,
            "cur_t": exp_info.cur_t,
            "config": exp_info.config,
            "error": exp_info.error,
            "input_tokens": exp_info.input_tokens,
            "output_tokens": exp_info.output_tokens,
            "created_at": exp_info.created_at,
            "updated_at": exp_info.updated_at,
        }
        recovered = False
        while True:
            insert_func = self._get_insert_func()
            async with self._async_session() as session:
                try:
                    stmt = insert_func(table_obj).values([data])
                    if self._config.db_type in ("postgresql", "sqlite"):
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["experiment_id"],
                            set_={
                                "name": stmt.excluded.name,
                                "num_day": stmt.excluded.num_day,
                                "status": stmt.excluded.status,
                                "cur_day": stmt.excluded.cur_day,
                                "cur_t": stmt.excluded.cur_t,
                                "config": stmt.excluded.config,
                                "error": stmt.excluded.error,
                                "input_tokens": stmt.excluded.input_tokens,
                                "output_tokens": stmt.excluded.output_tokens,
                                "updated_at": stmt.excluded.updated_at,
                            },
                        )
                    await session.execute(stmt)
                    await session.commit()
                    get_logger().debug(f"Updated experiment info for {self.exp_id}")
                    return
                except Exception as e:
                    await session.rollback()
                    if not recovered and self._is_sqlite_corruption_error(e, self._config):
                        get_logger().warning("SQLite corruption detected; recovering and retrying write...")
                        await self._recover_sqlite_db()
                        recovered = True
                        continue
                    get_logger().error(f"Error updating experiment info: {e}")
                    if recovered:
                        get_logger().warning("Write still failed after recovery. Data lost for this batch.")
                        return
                    raise

    @lock_decorator
    async def fetch_pending_dialogs(self):
        """Fetch all unprocessed pending dialogs from the database."""
        table_obj = self._tables["pending_dialog"]["table"]

        max_attempts = 4 if self._config.db_type == "sqlite" else 1

        for attempt in range(1, max_attempts + 1):
            async with self._async_session() as session:
                try:
                    stmt = select(table_obj).where(table_obj.c.processed.is_(False))
                    result = await session.execute(stmt)
                    rows = result.fetchall()
                    return [StoragePendingDialog(**row._asdict()) for row in rows]

                except Exception as e:
                    if attempt < max_attempts and self._is_sqlite_lock_error(e):
                        delay_seconds = 0.2 * attempt
                        get_logger().warning(
                            f"SQLite lock while fetching pending dialogs "
                            f"(attempt {attempt}/{max_attempts}), retrying in {delay_seconds:.1f}s: {e}"
                        )
                        await asyncio.sleep(delay_seconds)
                        continue

                    get_logger().error(f"Error fetching pending dialogs: {e}")
                    raise

        return []

    @lock_decorator
    async def mark_dialogs_as_processed(self, pending_ids: list[int]):
        """Mark specified dialogs as processed."""
        if not pending_ids:
            return

        table_obj = self._tables["pending_dialog"]["table"]

        async with self._async_session() as session:
            try:
                stmt = (
                    update(table_obj)
                    .where(table_obj.c.id.in_(pending_ids))
                    .values(processed=True)
                )
                await session.execute(stmt)
                await session.commit()
                get_logger().debug(f"Marked {len(pending_ids)} dialogs as processed")
            except Exception as e:
                await session.rollback()
                get_logger().error(f"Error marking dialogs as processed: {e}")
                raise

    @lock_decorator
    async def fetch_pending_surveys(self):
        """Fetch all unprocessed pending surveys from the database."""
        table_obj = self._tables["pending_survey"]["table"]

        max_attempts = 4 if self._config.db_type == "sqlite" else 1

        for attempt in range(1, max_attempts + 1):
            async with self._async_session() as session:
                try:
                    stmt = select(table_obj).where(table_obj.c.processed.is_(False))
                    result = await session.execute(stmt)
                    rows = result.fetchall()

                    results = []
                    for row in rows:
                        row_dict = row._asdict()
                        row_dict["survey_id"] = str(row_dict["survey_id"])
                        results.append(StoragePendingSurvey(**row_dict))
                    return results

                except Exception as e:
                    if attempt < max_attempts and self._is_sqlite_lock_error(e):
                        delay_seconds = 0.2 * attempt
                        get_logger().warning(
                            f"SQLite lock while fetching pending surveys "
                            f"(attempt {attempt}/{max_attempts}), retrying in {delay_seconds:.1f}s: {e}"
                        )
                        await asyncio.sleep(delay_seconds)
                        continue

                    get_logger().error(f"Error fetching pending surveys: {e}")
                    raise

        return []

    @lock_decorator
    async def mark_surveys_as_processed(self, pending_ids: list[int]):
        """Mark specified surveys as processed."""
        if not pending_ids:
            return

        table_obj = self._tables["pending_survey"]["table"]

        async with self._async_session() as session:
            try:
                stmt = (
                    update(table_obj)
                    .where(table_obj.c.id.in_(pending_ids))
                    .values(processed=True)
                )
                await session.execute(stmt)
                await session.commit()
                get_logger().debug(f"Marked {len(pending_ids)} surveys as processed")
            except Exception as e:
                await session.rollback()
                get_logger().error(f"Error marking surveys as processed: {e}")
                raise

    async def close(self):
        """Close database connection"""
        if hasattr(self, "_engine"):
            await self._engine.dispose()
