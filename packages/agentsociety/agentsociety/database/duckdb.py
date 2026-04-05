from __future__ import annotations

import json
import re
from typing import Any, Optional

try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore[assignment]

import ray

from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from .base_database import BaseSimulationDatabase, TableRecord


class DuckDBDatabase(BaseSimulationDatabase):
    """DuckDB database manager for simulation telemetry and batch writes."""

    def __init__(
        self,
        exp_id: str,
        home_dir: str,
        batch_size: int = 128,
        batch_timeout: float = 30.0,
        metrics_actor: Optional[ray.actor.ActorHandle[PrometheusActor]] = None,
    ):
        self.conn: Optional[Any] = None
        super().__init__(
            exp_id=exp_id,
            home_dir=home_dir,
            db_subdir="duckdb",
            batch_size=batch_size,
            batch_timeout=batch_timeout,
            metrics_actor=metrics_actor,
        )
        self._insert_sql_by_table = self._build_insert_sql_by_table()
        self.db_file = self.db_path / f"{self.exp_id}.duckdb"
        self._connect()
        self._create_tables()

        get_logger().info(
            f"DuckDBDatabase initialized with {batch_size=}, db_file='{self.db_file}'"
        )

    @property
    def backend_name(self) -> str:
        return "duckdb"

    def is_available(self) -> bool:
        if not self._is_connected():
            return False
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception as e:
            get_logger().error(f"DuckDB health check failed: {e}")
            return False

    def _is_connected(self) -> bool:
        return self.conn is not None

    def _connect(self) -> None:
        if duckdb is None:
            get_logger().error(
                "duckdb package is not installed. DuckDB fallback backend is unavailable."
            )
            self.conn = None
            return
        try:
            self.conn = duckdb.connect(str(self.db_file))
            get_logger().info(f"Connected to DuckDB file '{self.db_file}'.")
        except Exception as e:
            get_logger().error(f"Failed to connect to DuckDB: {e}")
            self.conn = None

    def _create_tables(self) -> None:
        if self.conn is None:
            get_logger().error("DuckDB connection is not available. Cannot create tables.")
            return

        migration_files = sorted(
            path
            for path in self.migrations_dir.glob("*.sql")
            if not path.name.endswith(".duckdb.sql")
        )
        if not migration_files:
            get_logger().warning(
                f"No ClickHouse migration files found in '{self.migrations_dir}'."
            )
            return

        failed_migrations: list[str] = []
        for migration_file in migration_files:
            raw = migration_file.read_text(encoding="utf-8").strip()
            if not raw:
                get_logger().warning(
                    f"Skipping empty migration file '{migration_file.name}'."
                )
                continue

            statements = self._to_duckdb_statements(raw)
            migration_failed = False
            for statement in statements:
                try:
                    self.conn.execute(statement)
                except Exception as migration_error:
                    migration_failed = True
                    get_logger().error(
                        "Failed converted DuckDB migration "
                        f"'{migration_file.name}' statement: {migration_error}"
                    )
            if migration_failed:
                failed_migrations.append(migration_file.name)
            else:
                get_logger().debug(
                    f"Applied converted migration '{migration_file.name}' to DuckDB."
                )

        if failed_migrations:
            get_logger().warning(
                "Completed DuckDB table initialization with failed migrations: "
                + ", ".join(failed_migrations)
            )
        else:
            get_logger().info("Tables created successfully in DuckDB database.")

    @classmethod
    def _to_duckdb_statements(cls, raw_sql: str) -> list[str]:
        statements = [s.strip() for s in raw_sql.split(";") if s.strip()]
        converted: list[str] = []
        for statement in statements:
            statement = cls._convert_clickhouse_types(statement)
            statement = cls._strip_clickhouse_engine_clause(statement)
            converted.extend(cls._normalize_alter_add_columns(statement))
        return converted

    @staticmethod
    def _convert_clickhouse_types(statement: str) -> str:
        out = DuckDBDatabase._strip_codec_clauses(statement)

        replacements = [
            (r"Array\(LowCardinality\(String\)\)", "VARCHAR"),
            (r"Array\(String\)", "VARCHAR"),
            (r"Nullable\(Int32\)", "INTEGER"),
            (r"Nullable\(String\)", "VARCHAR"),
            (r"LowCardinality\(String\)", "VARCHAR"),
            (r"DateTime64\(3\)", "TIMESTAMP"),
            (r"Float64", "DOUBLE"),
            (r"Float32", "REAL"),
            (r"Int64", "BIGINT"),
            (r"Int32", "INTEGER"),
            (r"UUID", "VARCHAR"),
            (r"String", "VARCHAR"),
        ]

        for pattern, replacement in replacements:
            out = re.sub(pattern, replacement, out)
        return out

    @staticmethod
    def _strip_codec_clauses(statement: str) -> str:
        # Remove ClickHouse column codecs, including nested parentheses like CODEC(ZSTD(3)).
        return re.sub(r"\s+CODEC\((?:[^)(]+|\([^)(]*\))*\)", "", statement)

    @staticmethod
    def _strip_clickhouse_engine_clause(statement: str) -> str:
        return re.sub(
            r"\s+ENGINE\s*=\s*.*$",
            "",
            statement,
            flags=re.DOTALL,
        ).strip()

    @staticmethod
    def _normalize_alter_add_columns(statement: str) -> list[str]:
        match = re.match(
            r"^ALTER\s+TABLE\s+(\S+)\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+(.+)$",
            statement,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return [statement]

        table_name = match.group(1)
        tail = match.group(2)
        columns = [col.strip() for col in tail.split(",") if col.strip()]

        normalized_columns: list[str] = []
        for column in columns:
            normalized_columns.append(
                re.sub(
                    r"^ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+",
                    "",
                    column,
                    flags=re.IGNORECASE,
                )
            )

        return [
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column}"
            for column in normalized_columns
        ]

    def _record_value(self, record: TableRecord, column_name: str) -> Any:
        value = super()._record_value(record, column_name)
        if column_name in {"possible_blocks", "hobbies"}:
            return json.dumps(value if value is not None else [])
        return value

    def _build_insert_sql_by_table(self) -> dict[str, str]:
        insert_sql: dict[str, str] = {}
        for table_name, column_names in self.table_columns.items():
            placeholders = ", ".join(["?"] * len(column_names))
            columns = ", ".join(column_names)
            insert_sql[table_name] = (
                "INSERT INTO " + table_name + " (" + columns + ") VALUES (" + placeholders + ")"
            )
        return insert_sql

    def _flush_records(
        self, table_name: str, records: list[TableRecord], column_names: list[str]
    ) -> None:
        if self.conn is None:
            raise RuntimeError("DuckDB connection is not available")

        row_data = [
            tuple(self._record_value(record, column_name) for column_name in column_names)
            for record in records
        ]
        sql = self._insert_sql_by_table.get(table_name)
        if sql is None:
            raise ValueError(f"Unknown table '{table_name}'")
        self.conn.executemany(sql, row_data)

    def _close_connection(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _query_rows(self, query: str, params: Optional[Any] = None) -> list[dict[str, Any]]:
        if self.conn is None:
            get_logger().error("DuckDB connection is not available. Cannot query.")
            return []

        try:
            cursor = self.conn.execute(query, params or [])
            rows = cursor.fetchall()
            column_names = [col[0] for col in (cursor.description or [])]
            return [dict(zip(column_names, row, strict=False)) for row in rows]
        except Exception as e:
            get_logger().error(f"Failed to query DuckDB: {e}")
            return []

    @staticmethod
    def _decode_json_array(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                loaded = json.loads(value)
                return loaded if isinstance(loaded, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def _resume_query(
        self,
        query_name: str,
        *,
        source_exp_id: str,
        source_uuid: str,
        resume_step: Optional[int] = None,
        rollback_depth: Optional[int] = None,
        attempt_step: Optional[int] = None,
    ) -> tuple[str, Optional[Any]]:
        if query_name == "latest_experiment_info":
            return (
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at, "
                "last_mobility_safe_step, prev_mobility_safe_step, economy_checkpoint_path "
                "FROM experiment_info "
                "WHERE id = ? "
                "ORDER BY updated_at DESC "
                "LIMIT 1",
                [source_uuid],
            )
        if query_name == "latest_step":
            return (
                "SELECT max(simulation_step) AS max_step "
                "FROM step_agent_status "
                "WHERE exp_id = ?",
                [source_exp_id],
            )
        if query_name == "candidate_steps":
            if resume_step is None or rollback_depth is None:
                raise ValueError("resume_step and rollback_depth are required for candidate_steps query")
            return (
                "SELECT DISTINCT simulation_step FROM agent_kv_snapshot "
                "WHERE exp_id = ? AND simulation_step <= ? "
                "ORDER BY simulation_step DESC "
                "LIMIT ?",
                [source_exp_id, resume_step, rollback_depth],
            )
        if query_name == "kv_rows":
            if attempt_step is None:
                raise ValueError("attempt_step is required for kv_rows query")
            return (
                "SELECT agent_id, key, value_json FROM agent_kv_snapshot "
                "WHERE exp_id = ? AND simulation_step = ?",
                [source_exp_id, attempt_step],
            )
        if query_name == "stream_rows":
            if attempt_step is None:
                raise ValueError("attempt_step is required for stream_rows query")
            return (
                "SELECT agent_id, memory_id, cognition_id, topic, location, description, day, t "
                "FROM agent_stream_snapshot "
                "WHERE exp_id = ? AND simulation_step = ?",
                [source_exp_id, attempt_step],
            )
        if query_name == "spatial_rows":
            if attempt_step is None:
                raise ValueError("attempt_step is required for spatial_rows query")
            return (
                "SELECT agent_id, location_id, description, price, atmosphere, satisfaction, convenience, uncertainty "
                "FROM agent_spatial_snapshot "
                "WHERE exp_id = ? AND simulation_step = ?",
                [source_exp_id, attempt_step],
            )
        if query_name == "pending_messages":
            if attempt_step is None:
                raise ValueError("attempt_step is required for pending_messages query")
            return (
                "SELECT from_id, to_id, day, t, kind, payload_json, created_at, extra_json "
                "FROM pending_messages_snapshot "
                "WHERE exp_id = ? AND simulation_step = ?",
                [source_exp_id, attempt_step],
            )
        if query_name == "experiment_info_for_update":
            return (
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at "
                "FROM experiment_info "
                "WHERE id = ? "
                "ORDER BY updated_at DESC "
                "LIMIT 1",
                [source_uuid],
            )

        raise ValueError(f"Unknown resume query '{query_name}'")

