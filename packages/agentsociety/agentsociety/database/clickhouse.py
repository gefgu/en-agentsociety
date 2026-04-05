from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

import ray

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None  # type: ignore[assignment]

from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from .base_database import BaseSimulationDatabase, TableRecord
from .schema import ExperimentInfoRecord

ClickHouseClient = Any

class ClickHouseDatabase(BaseSimulationDatabase):
    """ClickHouse database manager for simulation telemetry and batch writes."""

    def __init__(
        self,
        exp_id: str,
        home_dir: str,
        host: str = "localhost",
        port: int = 8123,
        username: str = "default",
        password: str = "clickhouse",
        database: str = "fastsociety",
        batch_size: int = 128,
        batch_timeout: float = 30.0,
        auto_create_database: bool = True,
        metrics_actor: Optional[ray.actor.ActorHandle[PrometheusActor]] = None,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.auto_create_database = auto_create_database
        self.client: Optional[ClickHouseClient] = None
        super().__init__(
            exp_id=exp_id,
            home_dir=home_dir,
            db_subdir="clickhouse",
            batch_size=batch_size,
            batch_timeout=batch_timeout,
            metrics_actor=metrics_actor,
        )
        self._connect()
        self._create_tables()

        get_logger().info(f"ClickHouseDatabase initialized with {batch_size=}")

    @property
    def backend_name(self) -> str:
        return "clickhouse"

    def is_available(self) -> bool:
        if not self._is_connected():
            return False
        try:
            self.client.command("SELECT 1")
            return True
        except Exception as e:
            get_logger().error(f"ClickHouse health check failed: {e}")
            return False

    def _is_connected(self) -> bool:
        return self.client is not None

    def _connect(self):
        """Establish connection to ClickHouse server."""
        if clickhouse_connect is None:
            get_logger().error(
                "clickhouse_connect package is not installed. ClickHouse backend is unavailable."
            )
            self.client = None
            return

        try:
            if self.auto_create_database:
                temp_client = None
                try:
                    temp_client = clickhouse_connect.get_client(
                        host=self.host,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                    )
                    temp_client.command(
                        f"CREATE DATABASE IF NOT EXISTS {self.database}"
                    )
                    get_logger().info(
                        f"Database '{self.database}' ensured in ClickHouse server."
                    )
                except Exception as e:
                    get_logger().error(
                        f"Failed to ensure database '{self.database}': {e}"
                    )
                finally:
                    if temp_client:
                        temp_client.close()
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
            )

            get_logger().info("Connected to ClickHouse server.")
        except Exception as e:
            get_logger().error(f"Failed to connect to ClickHouse server: {e}")
            self.client = None

    def _create_tables(self):
        """Create necessary tables in ClickHouse database."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot create tables."
            )
            return

        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        if not migration_files:
            get_logger().warning(
                f"No migration files found in '{self.migrations_dir}'."
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

            # Split on semicolons so files with multiple statements work correctly.
            statements = [s.strip() for s in raw.split(";") if s.strip()]
            migration_failed = False
            for statement in statements:
                try:
                    self.client.command(statement)
                except Exception as migration_error:
                    migration_failed = True
                    get_logger().error(
                        f"Failed migration '{migration_file.name}' statement: {migration_error}"
                    )
            if migration_failed:
                failed_migrations.append(migration_file.name)
            else:
                get_logger().debug(f"Applied migration '{migration_file.name}'.")

        if failed_migrations:
            get_logger().warning(
                "Completed table initialization with failed migrations: "
                + ", ".join(failed_migrations)
            )
        else:
            get_logger().info("Tables created successfully in ClickHouse database.")

    @staticmethod
    def _is_unknown_table_error(error: Exception) -> bool:
        message = str(error)
        return "UNKNOWN_TABLE" in message or "does not exist" in message

    def _recover_missing_table_and_retry_flush(
        self,
        table_name: str,
        records: list[TableRecord],
        column_names: list[str],
    ) -> bool:
        try:
            self._create_tables()
            self._flush_records(table_name, records, column_names)
            return True
        except Exception as retry_error:
            get_logger().error(
                f"Retry after recreating table '{table_name}' failed: {retry_error}"
            )
            return False

    def _flush_records(
        self, table_name: str, records: list[TableRecord], column_names: list[str]
    ) -> None:
        if self.client is None:
            raise RuntimeError("ClickHouse client is not connected")

        column_data = [
            [self._record_value(record, column_name) for record in records]
            for column_name in column_names
        ]
        self.client.insert(
            table_name,
            column_data,
            column_names=column_names,
            column_oriented=True,
        )

    def _close_connection(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    @staticmethod
    def _escape_sql_string(value: str) -> str:
        return value.replace("'", "''")

    def _query_rows(self, query: str) -> list[dict[str, Any]]:
        if self.client is None:
            get_logger().error("ClickHouse client is not connected. Cannot query.")
            return []

        try:
            result = self.client.query(query)
            rows = getattr(result, "result_rows", [])
            column_names = getattr(result, "column_names", [])
            return [dict(zip(column_names, row, strict=False)) for row in rows]
        except Exception as e:
            get_logger().error(f"Failed to query ClickHouse: {e}")
            return []

    def fetch_resume_data(self, source_exp_id: str) -> Optional[dict[str, Any]]:
        """Fetch config, latest step, and latest static attributes for a source experiment."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot fetch resume data."
            )
            return None

        try:
            source_uuid = str(uuid.UUID(source_exp_id))
        except (ValueError, TypeError):
            get_logger().error(f"Invalid source experiment id: {source_exp_id}")
            return None

        escaped_exp_id = self._escape_sql_string(source_exp_id)
        escaped_source_uuid = self._escape_sql_string(source_uuid)

        exp_info_rows = self._query_rows(
            (
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at, "
                "last_mobility_safe_step, prev_mobility_safe_step, economy_checkpoint_path "
                "FROM experiment_info FINAL "
                f"WHERE id = toUUID('{escaped_source_uuid}') "
                "ORDER BY updated_at DESC "
                "LIMIT 1"
            )
        )
        if not exp_info_rows:
            return None

        latest_exp_info = exp_info_rows[0]

        step_rows = self._query_rows(
            (
                "SELECT max(simulation_step) AS max_step "
                "FROM step_agent_status "
                f"WHERE exp_id = '{escaped_exp_id}'"
            )
        )
        latest_step_raw = step_rows[0].get("max_step") if step_rows else None
        latest_step = int(latest_step_raw) if latest_step_raw is not None else 0

        # Use last_mobility_safe_step as the canonical resume step
        last_safe_raw = latest_exp_info.get("last_mobility_safe_step")
        last_safe_step = int(last_safe_raw) if last_safe_raw is not None else -1
        economy_checkpoint_path = str(
            latest_exp_info.get("economy_checkpoint_path") or ""
        )

        static_step_rows = self._query_rows(
            (
                "SELECT max(simulation_step) AS max_static_step "
                "FROM static_agent_attributes "
                f"WHERE exp_id = '{escaped_exp_id}'"
            )
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
                f"WHERE exp_id = '{escaped_exp_id}' AND simulation_step = {static_step} "
                "ORDER BY agent_id"
            )
        )

        # Determine the resume step for checkpoint data (N-1 fallback if incomplete)
        resume_step = last_safe_step
        kv_snapshots: dict[int, list[dict]] = {}
        stream_snapshots: dict[int, list[dict]] = {}
        spatial_snapshots: dict[int, list[dict]] = {}
        pending_messages: list[dict] = []

        if resume_step >= 0:
            (
                resume_step,
                kv_snapshots,
                stream_snapshots,
                spatial_snapshots,
                pending_messages,
            ) = self._fetch_checkpoint_snapshots(
                escaped_exp_id=escaped_exp_id,
                resume_step=resume_step,
                prev_step=(
                    int(latest_exp_info.get("prev_mobility_safe_step"))
                    if latest_exp_info.get("prev_mobility_safe_step") is not None
                    else -1
                ),
                expected_agent_ids={int(r["agent_id"]) for r in static_rows},
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
        escaped_exp_id: str,
        resume_step: int,
        prev_step: int,
        expected_agent_ids: set[int],
    ) -> tuple[int, dict[int, list], dict[int, list], dict[int, list], list[dict]]:
        """Fetch KV/stream/spatial/message snapshots at resume_step with N-1 fallback."""
        for attempt_step in [resume_step, prev_step]:
            if attempt_step < 0:
                continue

            kv_rows = self._query_rows(
                f"SELECT agent_id, key, value_json FROM agent_kv_snapshot "
                f"WHERE exp_id = '{escaped_exp_id}' AND simulation_step = {attempt_step}"
            )

            # Integrity check: all expected agents must have KV data
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

            # Group KV by agent_id
            kv_snapshots: dict[int, list[dict]] = {}
            for row in kv_rows:
                aid = int(row["agent_id"])
                kv_snapshots.setdefault(aid, []).append(
                    {"key": row["key"], "value_json": row["value_json"]}
                )

            stream_rows = self._query_rows(
                f"SELECT agent_id, memory_id, cognition_id, topic, location, description, day, t "
                f"FROM agent_stream_snapshot "
                f"WHERE exp_id = '{escaped_exp_id}' AND simulation_step = {attempt_step}"
            )
            stream_snapshots: dict[int, list[dict]] = {}
            for row in stream_rows:
                aid = int(row["agent_id"])
                stream_snapshots.setdefault(aid, []).append(row)

            spatial_rows = self._query_rows(
                f"SELECT agent_id, location_id, description, price, atmosphere, satisfaction, convenience, uncertainty "
                f"FROM agent_spatial_snapshot "
                f"WHERE exp_id = '{escaped_exp_id}' AND simulation_step = {attempt_step}"
            )
            spatial_snapshots: dict[int, list[dict]] = {}
            for row in spatial_rows:
                aid = int(row["agent_id"])
                spatial_snapshots.setdefault(aid, []).append(row)

            pending_messages = self._query_rows(
                f"SELECT from_id, to_id, day, t, kind, payload_json, created_at, extra_json "
                f"FROM pending_messages_snapshot "
                f"WHERE exp_id = '{escaped_exp_id}' AND simulation_step = {attempt_step}"
            )

            get_logger().info(f"Loaded checkpoint snapshots at step {attempt_step}")
            return (
                attempt_step,
                kv_snapshots,
                stream_snapshots,
                spatial_snapshots,
                pending_messages,
            )

        get_logger().warning(
            "No valid checkpoint snapshots found; memory will start from defaults"
        )
        return -1, {}, {}, {}, []

    def update_experiment_info_checkpoint(
        self,
        exp_id: str,
        last_mobility_safe_step: int,
        prev_mobility_safe_step: int,
        economy_checkpoint_path: str,
    ) -> None:
        """Write checkpoint columns for an experiment by inserting a new row.

        Reads the current ``experiment_info`` row for ``exp_id`` via a FINAL
        SELECT (to collapse ReplacingMergeTree duplicates), then inserts a new
        row with the same non-checkpoint fields plus the updated checkpoint
        values.  This eliminates the ALTER TABLE UPDATE mutation race: the
        ReplacingMergeTree engine deduplicates on the next FINAL read, always
        preferring the row with the highest ``updated_at``.

        Args:
            exp_id: UUID string of the experiment to update.
            last_mobility_safe_step: Step index of the latest mobility-safe checkpoint.
            prev_mobility_safe_step: Step index of the previous mobility-safe checkpoint.
            economy_checkpoint_path: Filesystem path to the economy snapshot file.

        @usedBy: simulationengine.py via ``_db_actor.update_experiment_info_checkpoint.remote(...)``
        Side effects: queues one INSERT into the ``experiment_info`` ClickHouse table.
        """
        if self.client is None:
            return
        try:
            source_uuid = str(uuid.UUID(exp_id))
            escaped_uuid = self._escape_sql_string(source_uuid)

            rows = self._query_rows(
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at "
                "FROM experiment_info FINAL "
                f"WHERE id = toUUID('{escaped_uuid}') "
                "ORDER BY updated_at DESC "
                "LIMIT 1"
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
            get_logger().error(
                f"Failed to update experiment_info checkpoint columns: {e}"
            )
