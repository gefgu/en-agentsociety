from dataclasses import dataclass
from typing import Any, Optional
import ray

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None  # type: ignore[assignment]

from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from .base_database import BaseSimulationDatabase, TableRecord

ClickHouseClient = Any


@dataclass
class ClickHouseConfig:
    """Connection and configuration parameters for ClickHouse."""
    host: str = "localhost"
    port: int = 8123
    username: str = "default"
    password: str = "clickhouse"
    database: str = "fastsociety"
    auto_create_database: bool = True

    def get_client_kwargs(self, include_db: bool = True) -> dict[str, Any]:
        """Returns kwargs ready to be unpacked into clickhouse_connect.get_client()"""
        kwargs = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
        }
        if include_db:
            kwargs["database"] = self.database
        return kwargs


class ClickHouseDatabase(BaseSimulationDatabase):
    """ClickHouse database manager for simulation telemetry and batch writes."""

    def __init__(
        self,
        exp_id: str,
        home_dir: str,
        config: Optional[ClickHouseConfig] = None,
        batch_size: int = 128,
        batch_timeout: float = 30.0,
        metrics_actor: Optional[Any] = None,
    ):
        self.config = config or ClickHouseConfig()
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
            if self.config.auto_create_database:
                temp_client = None
                try:
                    temp_client = clickhouse_connect.get_client(
                        **self.config.get_client_kwargs(include_db=False)
                    )
                    temp_client.command(
                        f"CREATE DATABASE IF NOT EXISTS {self.config.database}"
                    )
                    get_logger().info(
                        f"Database '{self.config.database}' ensured in ClickHouse server."
                    )
                except Exception as e:
                    get_logger().error(
                        f"Failed to ensure database '{self.config.database}': {e}"
                    )
                finally:
                    if temp_client:
                        temp_client.close()
            self.client = clickhouse_connect.get_client(
                **self.config.get_client_kwargs(include_db=True)
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

    def _query_rows(
        self, query: str, parameters: Optional[Any] = None
    ) -> list[dict[str, Any]]:
        if self.client is None:
            get_logger().error("ClickHouse client is not connected. Cannot query.")
            return []

        try:
            result = self.client.query(query, parameters=parameters)
            rows = getattr(result, "result_rows", [])
            column_names = getattr(result, "column_names", [])
            return [dict(zip(column_names, row, strict=False)) for row in rows]
        except Exception as e:
            get_logger().error(f"Failed to query ClickHouse: {e}")
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
        base_params = {
            "source_exp_id": source_exp_id,
            "source_uuid": source_uuid,
        }

        if query_name == "latest_experiment_info":
            return (
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at, "
                "last_mobility_safe_step, prev_mobility_safe_step, economy_checkpoint_path "
                "FROM experiment_info FINAL "
                "WHERE id = toUUID({source_uuid:String}) "
                "ORDER BY updated_at DESC "
                "LIMIT 1",
                base_params,
            )
        if query_name == "latest_step":
            return (
                "SELECT max(simulation_step) AS max_step "
                "FROM step_agent_status "
                "WHERE exp_id = {source_exp_id:String}",
                base_params,
            )
        if query_name == "candidate_steps":
            if resume_step is None or rollback_depth is None:
                raise ValueError("resume_step and rollback_depth are required for candidate_steps query")
            return (
                "SELECT DISTINCT simulation_step FROM agent_kv_snapshot "
                "WHERE exp_id = {source_exp_id:String} AND simulation_step >= 1 AND simulation_step <= {resume_step:Int32} "
                "ORDER BY simulation_step DESC "
                "LIMIT {rollback_depth:Int32}",
                {
                    **base_params,
                    "resume_step": resume_step,
                    "rollback_depth": rollback_depth,
                },
            )
        if query_name == "kv_rows":
            if attempt_step is None:
                raise ValueError("attempt_step is required for kv_rows query")
            return (
                "SELECT agent_id, key, value_json FROM agent_kv_snapshot "
                "WHERE exp_id = {source_exp_id:String} AND simulation_step = {attempt_step:Int32}",
                {
                    **base_params,
                    "attempt_step": attempt_step,
                },
            )
        if query_name == "stream_rows":
            if attempt_step is None:
                raise ValueError("attempt_step is required for stream_rows query")
            return (
                "SELECT agent_id, memory_id, cognition_id, topic, location, description, day, t "
                "FROM agent_stream_snapshot "
                "WHERE exp_id = {source_exp_id:String} AND simulation_step = {attempt_step:Int32}",
                {
                    **base_params,
                    "attempt_step": attempt_step,
                },
            )
        if query_name == "spatial_rows":
            if attempt_step is None:
                raise ValueError("attempt_step is required for spatial_rows query")
            return (
                "SELECT agent_id, location_id, description, price, atmosphere, satisfaction, convenience, uncertainty "
                "FROM agent_spatial_snapshot "
                "WHERE exp_id = {source_exp_id:String} AND simulation_step = {attempt_step:Int32}",
                {
                    **base_params,
                    "attempt_step": attempt_step,
                },
            )
        if query_name == "pending_messages":
            if attempt_step is None:
                raise ValueError("attempt_step is required for pending_messages query")
            return (
                "SELECT from_id, to_id, day, t, kind, payload_json, created_at, extra_json "
                "FROM pending_messages_snapshot "
                "WHERE exp_id = {source_exp_id:String} AND simulation_step = {attempt_step:Int32}",
                {
                    **base_params,
                    "attempt_step": attempt_step,
                },
            )
        if query_name == "experiment_info_for_update":
            return (
                "SELECT "
                "id, tenant_id, name, num_day, status, cur_day, cur_t, config, error, "
                "input_tokens, output_tokens, created_at, updated_at "
                "FROM experiment_info FINAL "
                "WHERE id = toUUID({source_uuid:String}) "
                "ORDER BY updated_at DESC "
                "LIMIT 1",
                {"source_uuid": source_uuid},
            )

        raise ValueError(f"Unknown resume query '{query_name}'")
