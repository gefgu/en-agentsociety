from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any, Optional
import uuid

try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore[assignment]

import ray

from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from .base_database import BaseSimulationDatabase, TableRecord
from .schema import ExperimentInfoRecord


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

    def _flush_records(
        self, table_name: str, records: list[TableRecord], column_names: list[str]
    ) -> None:
        if self.conn is None:
            raise RuntimeError("DuckDB connection is not available")

        row_data = [
            tuple(self._record_value(record, column_name) for column_name in column_names)
            for record in records
        ]
        placeholders = ", ".join(["?"] * len(column_names))
        sql = (
            f"INSERT INTO {table_name} ({', '.join(column_names)}) "
            f"VALUES ({placeholders})"
        )
        self.conn.executemany(sql, row_data)

    def _close_connection(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _query_rows(self, query: str, params: Optional[list[Any]] = None) -> list[dict[str, Any]]:
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

    def fetch_resume_data(self, source_exp_id: str) -> Optional[dict[str, Any]]:
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot fetch resume data."
            )
            return None

        try:
            source_uuid = str(uuid.UUID(source_exp_id))
        except (ValueError, TypeError):
            get_logger().error(f"Invalid source experiment id: {source_exp_id}")
            return None

        exp_info_rows = self._query_rows(
            (
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at, "
                "last_mobility_safe_step, prev_mobility_safe_step, economy_checkpoint_path "
                "FROM experiment_info "
                "WHERE id = ? "
                "ORDER BY updated_at DESC "
                "LIMIT 1"
            ),
            [source_uuid],
        )
        if not exp_info_rows:
            return None

        latest_exp_info = exp_info_rows[0]

        step_rows = self._query_rows(
            (
                "SELECT max(simulation_step) AS max_step "
                "FROM step_agent_status "
                "WHERE exp_id = ?"
            ),
            [source_exp_id],
        )
        latest_step_raw = step_rows[0].get("max_step") if step_rows else None
        latest_step = int(latest_step_raw) if latest_step_raw is not None else 0

        last_safe_step = int(latest_exp_info.get("last_mobility_safe_step") or -1)
        economy_checkpoint_path = str(latest_exp_info.get("economy_checkpoint_path") or "")

        static_step_rows = self._query_rows(
            (
                "SELECT max(simulation_step) AS max_static_step "
                "FROM static_agent_attributes "
                "WHERE exp_id = ?"
            ),
            [source_exp_id],
        )
        static_step_raw = (
            static_step_rows[0].get("max_static_step") if static_step_rows else None
        )
        static_step = int(static_step_raw) if static_step_raw is not None else 0

        static_rows = self._query_rows(
            (
                "SELECT "
                "agent_id, type, home_aoi_id, work_aoi_id, name, gender, age, "
                "education, household, life_stage, skill, occupation, work_skill, "
                "firm_id, government_id, bank_id, nbs_id, "
                "preferences_chronotype, preferences_risk_tolerance, "
                "preferences_spending_tendency, preferences_social_frequency, "
                "preferences_work_ethic, preferences_leisure_preference, hobbies, "
                "personality, big5_openness, big5_conscientiousness, "
                "big5_extraversion, big5_agreeableness, big5_neuroticism, "
                "income, currency, residence, city, race, religion, "
                "marriage_status, background_story "
                "FROM static_agent_attributes "
                "WHERE exp_id = ? AND simulation_step = ? "
                "ORDER BY agent_id"
            ),
            [source_exp_id, static_step],
        )
        for row in static_rows:
            row["hobbies"] = self._decode_json_array(row.get("hobbies"))

        resume_step = last_safe_step
        kv_snapshots: dict[int, list[dict]] = {}
        stream_snapshots: dict[int, list[dict]] = {}
        spatial_snapshots: dict[int, list[dict]] = {}
        pending_messages: list[dict] = []

        if resume_step >= 0:
            resume_step, kv_snapshots, stream_snapshots, spatial_snapshots, pending_messages = (
                self._fetch_checkpoint_snapshots(
                    source_exp_id=source_exp_id,
                    resume_step=resume_step,
                    prev_step=int(latest_exp_info.get("prev_mobility_safe_step") or -1),
                    expected_agent_ids={int(r["agent_id"]) for r in static_rows},
                )
            )

        return {
            "source_exp_id": source_exp_id,
            "config": str(latest_exp_info.get("config") or ""),
            "latest_experiment_info": latest_exp_info,
            "latest_step": latest_step,
            "last_mobility_safe_step": resume_step,
            "economy_checkpoint_path": economy_checkpoint_path,
            "static_step": static_step,
            "static_records": static_rows,
            "kv_snapshots": kv_snapshots,
            "stream_snapshots": stream_snapshots,
            "spatial_snapshots": spatial_snapshots,
            "pending_messages": pending_messages,
        }

    def _fetch_checkpoint_snapshots(
        self,
        source_exp_id: str,
        resume_step: int,
        prev_step: int,
        expected_agent_ids: set[int],
    ) -> tuple[int, dict[int, list], dict[int, list], dict[int, list], list[dict]]:
        for attempt_step in [resume_step, prev_step]:
            if attempt_step < 0:
                continue

            kv_rows = self._query_rows(
                (
                    "SELECT agent_id, key, value_json FROM agent_kv_snapshot "
                    "WHERE exp_id = ? AND simulation_step = ?"
                ),
                [source_exp_id, attempt_step],
            )

            kv_agent_ids = {int(r["agent_id"]) for r in kv_rows}
            if expected_agent_ids and not expected_agent_ids.issubset(kv_agent_ids):
                missing = expected_agent_ids - kv_agent_ids
                get_logger().warning(
                    f"KV snapshot at step {attempt_step} is incomplete (missing {len(missing)} agents). "
                    + (
                        f"Falling back to step {prev_step}."
                        if attempt_step == resume_step
                        else "No valid checkpoint found."
                    )
                )
                continue

            kv_snapshots: dict[int, list[dict]] = {}
            for row in kv_rows:
                aid = int(row["agent_id"])
                kv_snapshots.setdefault(aid, []).append(
                    {"key": row["key"], "value_json": row["value_json"]}
                )

            stream_rows = self._query_rows(
                (
                    "SELECT agent_id, memory_id, cognition_id, topic, location, description, day, t "
                    "FROM agent_stream_snapshot "
                    "WHERE exp_id = ? AND simulation_step = ?"
                ),
                [source_exp_id, attempt_step],
            )
            stream_snapshots: dict[int, list[dict]] = {}
            for row in stream_rows:
                aid = int(row["agent_id"])
                stream_snapshots.setdefault(aid, []).append(row)

            spatial_rows = self._query_rows(
                (
                    "SELECT agent_id, location_id, description, price, atmosphere, satisfaction, convenience, uncertainty "
                    "FROM agent_spatial_snapshot "
                    "WHERE exp_id = ? AND simulation_step = ?"
                ),
                [source_exp_id, attempt_step],
            )
            spatial_snapshots: dict[int, list[dict]] = {}
            for row in spatial_rows:
                aid = int(row["agent_id"])
                spatial_snapshots.setdefault(aid, []).append(row)

            pending_messages = self._query_rows(
                (
                    "SELECT from_id, to_id, day, t, kind, payload_json, created_at, extra_json "
                    "FROM pending_messages_snapshot "
                    "WHERE exp_id = ? AND simulation_step = ?"
                ),
                [source_exp_id, attempt_step],
            )

            get_logger().info(f"Loaded checkpoint snapshots at step {attempt_step}")
            return (
                attempt_step,
                kv_snapshots,
                stream_snapshots,
                spatial_snapshots,
                pending_messages,
            )

        get_logger().warning("No valid checkpoint snapshots found; memory will start from defaults")
        return -1, {}, {}, {}, []

    def update_experiment_info_checkpoint(
        self,
        exp_id: str,
        last_mobility_safe_step: int,
        prev_mobility_safe_step: int,
        economy_checkpoint_path: str,
    ) -> None:
        if self.conn is None:
            return
        try:
            source_uuid = str(uuid.UUID(exp_id))

            rows = self._query_rows(
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at "
                "FROM experiment_info "
                "WHERE id = ? "
                "ORDER BY updated_at DESC "
                "LIMIT 1",
                [source_uuid],
            )
            if not rows:
                get_logger().error(
                    f"update_experiment_info_checkpoint: no row found for exp_id={exp_id}"
                )
                return

            base = rows[0]
            new_record: ExperimentInfoRecord = {
                "tenant_id": base["tenant_id"],
                "id": str(base["id"]),
                "name": base["name"],
                "num_day": base["num_day"],
                "status": base["status"],
                "cur_day": base["cur_day"],
                "cur_t": base["cur_t"],
                "config": base["config"],
                "error": base["error"],
                "input_tokens": base["input_tokens"],
                "output_tokens": base["output_tokens"],
                "created_at": base["created_at"],
                "updated_at": datetime.now(),
                "last_mobility_safe_step": last_mobility_safe_step,
                "prev_mobility_safe_step": prev_mobility_safe_step,
                "economy_checkpoint_path": economy_checkpoint_path,
            }
            self.insert_record("experiment_info", new_record)
        except Exception as e:
            get_logger().error(f"Failed to update experiment_info checkpoint columns: {e}")

