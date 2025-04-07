import asyncio
from typing import Any, Literal, Union

import psycopg
import psycopg.sql
import ray
from psycopg.rows import dict_row
from pydantic import BaseModel, Field, model_validator

from ..logger import get_logger
from ..utils.decorators import lock_decorator
from .type import (
    StorageDialog,
    StorageExpInfo,
    StorageGlobalPrompt,
    StorageProfile,
    StorageStatus,
    StorageSurvey,
)

__all__ = ["PgWriter", "PostgreSQLConfig"]

TABLE_PREFIX = "as_"

PGSQL_DICT: dict[str, list[Any]] = {
    # Experiment
    "experiment": [
        """
    CREATE TABLE IF NOT EXISTS {table_name} (
        tenant_id TEXT,
        id UUID,
        name TEXT,
        num_day INT4,
        status INT4,
        cur_day INT4,
        cur_t FLOAT,
        config TEXT,
        error TEXT,
        input_tokens INT4,
        output_tokens INT4,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (tenant_id, id)
    )
""",
    ],
    # Agent Profile
    "agent_profile": [
        """
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT PRIMARY KEY,
        name TEXT,
        profile JSONB
    )
""",
    ],
    # Global Prompt
    "global_prompt": [
        """
    CREATE TABLE IF NOT EXISTS {table_name} (
        day INT4,
        t FLOAT,
        prompt TEXT,
        created_at TIMESTAMPTZ
    )
""",
        "CREATE INDEX {table_name}_day_t_idx ON {table_name} (day,t)",
    ],
    # Agent Dialog
    "agent_dialog": [
        """
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT,
        day INT4,
        t FLOAT,
        type INT4,
        speaker TEXT,
        content TEXT,
        created_at TIMESTAMPTZ
    )
""",
        "CREATE INDEX {table_name}_id_idx ON {table_name} (id)",
        "CREATE INDEX {table_name}_day_t_idx ON {table_name} (day,t)",
    ],
    # Agent Status
    "agent_status": [
        """
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT,
        day INT4,
        t FLOAT,
        lng DOUBLE PRECISION,
        lat DOUBLE PRECISION,
        parent_id INT4,
        friend_ids INT[],
        action TEXT,
        status JSONB,
        created_at TIMESTAMPTZ
    )
""",
        "CREATE INDEX {table_name}_id_idx ON {table_name} (id)",
        "CREATE INDEX {table_name}_day_t_idx ON {table_name} (day,t)",
    ],
    # Agent Survey
    "agent_survey": [
        """
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT,
        day INT4,
        t FLOAT,
        survey_id UUID,
        result JSONB,
        created_at TIMESTAMPTZ
    )
""",
        "CREATE INDEX {table_name}_id_idx ON {table_name} (id)",
        "CREATE INDEX {table_name}_day_t_idx ON {table_name} (day,t)",
    ],
}


def _migrate_experiment_table(dsn: str):
    """为experiment表添加新的token列"""
    table_name = f"{TABLE_PREFIX}experiment"
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # check if columns exist
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND column_name IN ('input_tokens', 'output_tokens')
            """,
                (table_name,),
            )
            existing_columns = [row[0] for row in cur.fetchall()]

            # add missing columns
            if "input_tokens" not in existing_columns:
                cur.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN input_tokens INT4 DEFAULT 0"
                )
                get_logger().info(f"Added input_tokens column to {table_name}")

            if "output_tokens" not in existing_columns:
                cur.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN output_tokens INT4 DEFAULT 0"
                )
                get_logger().info(f"Added output_tokens column to {table_name}")

            conn.commit()


def _create_pg_tables(exp_id: str, dsn: str):
    for table_type, exec_strs in PGSQL_DICT.items():
        if not table_type == "experiment":
            table_name = f"{TABLE_PREFIX}{exp_id.replace('-', '_')}_{table_type}"
        else:
            table_name = f"{TABLE_PREFIX}{table_type}"
        # # debug str
        # for _str in [f"DROP TABLE IF EXISTS {table_name}"] + [
        #     _exec_str.format(table_name=table_name) for _exec_str in exec_strs
        # ]:
        #     print(_str)
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                if not table_type == "experiment":
                    # delete table
                    cur.execute(
                        psycopg.sql.SQL("DROP TABLE IF EXISTS {}").format(
                            psycopg.sql.Identifier(table_name)
                        )
                    )
                    get_logger().debug(
                        f"table:{table_name} sql: DROP TABLE IF EXISTS {table_name}"
                    )
                    conn.commit()
                # create table
                for _exec_str in exec_strs:
                    exec_str = _exec_str.format(table_name=table_name)
                    cur.execute(exec_str)
                    get_logger().debug(f"table:{table_name} sql: {exec_str}")
                conn.commit()
    # execute migration
    _migrate_experiment_table(dsn)


class PostgreSQLConfig(BaseModel):
    """PostgreSQL configuration class."""

    enabled: bool = Field(True)
    """Whether PostgreSQL storage is enabled"""

    dsn: str = Field(...)
    """Data source name for PostgreSQL"""

    num_workers: Union[int, Literal["auto"]] = Field("auto")
    """Number of workers for PostgreSQL"""

    @model_validator(mode="after")
    def validate_dsn(self):
        if not self.enabled:
            return self
        if not self.dsn.startswith("postgresql://"):
            raise ValueError("dsn must start with postgresql://")
        return self


@ray.remote
class PgWriter:
    def __init__(self, tenant_id: str, exp_id: str, dsn: str, init: bool):
        """
        Initialize the PgWriter.

        - **Args**:
            - `tenant_id` (str): The ID of the tenant.
            - `exp_id` (str): The ID of the experiment.
            - `dsn` (str): The DSN of the PostgreSQL database.
            - `init` (bool): Whether to initialize the PostgreSQL tables.
        """
        self.tenant_id = tenant_id
        self.exp_id = exp_id
        self._dsn = dsn
        self._lock = asyncio.Lock()
        if init:
            _create_pg_tables(exp_id, dsn)

    @lock_decorator
    async def write_dialogs(self, rows: list[StorageDialog]):
        table_name = f"{TABLE_PREFIX}{self.exp_id.replace('-', '_')}_agent_dialog"
        async with await psycopg.AsyncConnection.connect(self._dsn) as aconn:
            copy_sql = psycopg.sql.SQL(
                "COPY {} (id, day, t, type, speaker, content, created_at) FROM STDIN"
            ).format(psycopg.sql.Identifier(table_name))
            _rows: list[Any] = []
            async with aconn.cursor() as cur:
                async with cur.copy(copy_sql) as copy:
                    for row in rows:
                        _row = [
                            row.id,
                            row.day,
                            row.t,
                            row.type,
                            row.speaker,
                            row.content,
                            row.created_at,
                        ]
                        await copy.write_row(_row)
                        _rows.append(_row)
            get_logger().debug(f"table:{table_name} sql: {copy_sql} values: {_rows}")

    @lock_decorator
    async def write_statuses(self, rows: list[StorageStatus]):
        table_name = f"{TABLE_PREFIX}{self.exp_id.replace('-', '_')}_agent_status"
        async with await psycopg.AsyncConnection.connect(self._dsn) as aconn:
            copy_sql = psycopg.sql.SQL(
                "COPY {} (id, day, t, lng, lat, parent_id, friend_ids, action, status, created_at) FROM STDIN"
            ).format(psycopg.sql.Identifier(table_name))
            _rows: list[Any] = []
            async with aconn.cursor() as cur:
                async with cur.copy(copy_sql) as copy:
                    for row in rows:
                        _row = [
                            row.id,
                            row.day,
                            row.t,
                            row.lng,
                            row.lat,
                            row.parent_id,
                            row.friend_ids,
                            row.action,
                            row.status,
                            row.created_at,
                        ]
                        await copy.write_row(_row)
                        _rows.append(_row)
            get_logger().debug(f"table:{table_name} sql: {copy_sql} values: {_rows}")

    @lock_decorator
    async def write_profiles(self, rows: list[StorageProfile]):
        table_name = f"{TABLE_PREFIX}{self.exp_id.replace('-', '_')}_agent_profile"
        async with await psycopg.AsyncConnection.connect(self._dsn) as aconn:
            copy_sql = psycopg.sql.SQL("COPY {} (id, name, profile) FROM STDIN").format(
                psycopg.sql.Identifier(table_name)
            )
            _rows: list[Any] = []
            async with aconn.cursor() as cur:
                async with cur.copy(copy_sql) as copy:
                    for row in rows:
                        _row = [
                            row.id,
                            row.name,
                            row.profile,
                        ]
                        await copy.write_row(_row)
                        _rows.append(_row)
            get_logger().debug(f"table:{table_name} sql: {copy_sql} values: {_rows}")

    @lock_decorator
    async def write_surveys(self, rows: list[StorageSurvey]):
        table_name = f"{TABLE_PREFIX}{self.exp_id.replace('-', '_')}_agent_survey"
        async with await psycopg.AsyncConnection.connect(self._dsn) as aconn:
            copy_sql = psycopg.sql.SQL(
                "COPY {} (id, day, t, survey_id, result, created_at) FROM STDIN"
            ).format(psycopg.sql.Identifier(table_name))
            _rows: list[Any] = []
            async with aconn.cursor() as cur:
                async with cur.copy(copy_sql) as copy:
                    for row in rows:
                        _row = [
                            row.id,
                            row.day,
                            row.t,
                            row.survey_id,
                            row.result,
                            row.created_at,
                        ]
                        await copy.write_row(_row)
                        _rows.append(_row)
            get_logger().debug(f"table:{table_name} sql: {copy_sql} values: {_rows}")

    @lock_decorator
    async def write_global_prompt(self, prompt_info: StorageGlobalPrompt):
        table_name = f"{TABLE_PREFIX}{self.exp_id.replace('-', '_')}_global_prompt"
        async with await psycopg.AsyncConnection.connect(self._dsn) as aconn:
            async with aconn.cursor() as cur:
                copy_sql = psycopg.sql.SQL(
                    "COPY {} (day, t, prompt, created_at) FROM STDIN"
                ).format(psycopg.sql.Identifier(table_name))
                row = (
                    prompt_info.day,
                    prompt_info.t,
                    prompt_info.prompt,
                    prompt_info.created_at,
                )
                async with cur.copy(copy_sql) as copy:
                    await copy.write_row(row)
                get_logger().debug(f"table:{table_name} sql: {copy_sql} values: {row}")

    @lock_decorator
    async def update_exp_info(self, exp_info: StorageExpInfo):
        # timestamp不做类型转换
        table_name = f"{TABLE_PREFIX}experiment"
        async with await psycopg.AsyncConnection.connect(self._dsn) as aconn:
            async with aconn.cursor(row_factory=dict_row) as cur:
                # 使用固定的SQL语句，避免动态构建列名
                upsert_sql = psycopg.sql.SQL(
                    "INSERT INTO {} (tenant_id, id, name, num_day, status, cur_day, cur_t, config, error, input_tokens, output_tokens, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (tenant_id, id) DO UPDATE SET "
                    "name = EXCLUDED.name, "
                    "num_day = EXCLUDED.num_day, "
                    "status = EXCLUDED.status, "
                    "cur_day = EXCLUDED.cur_day, "
                    "cur_t = EXCLUDED.cur_t, "
                    "config = EXCLUDED.config, "
                    "error = EXCLUDED.error, "
                    "input_tokens = EXCLUDED.input_tokens, "
                    "output_tokens = EXCLUDED.output_tokens, "
                    "updated_at = EXCLUDED.updated_at"
                ).format(psycopg.sql.Identifier(table_name))

                # 准备参数值
                params = [
                    exp_info.tenant_id,
                    self.exp_id,
                    exp_info.name,
                    exp_info.num_day,
                    exp_info.status,
                    exp_info.cur_day,
                    exp_info.cur_t,
                    exp_info.config,
                    exp_info.error,
                    exp_info.input_tokens,
                    exp_info.output_tokens,
                    exp_info.created_at,
                    exp_info.updated_at,
                ]

                get_logger().debug(
                    f"table:{table_name} sql: {upsert_sql} values: {params}"
                )

                await cur.execute(upsert_sql, params)
                await aconn.commit()
