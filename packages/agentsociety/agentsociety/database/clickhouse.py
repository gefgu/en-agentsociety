from __future__ import annotations

from collections import deque
from datetime import datetime
import uuid
import time
from pathlib import Path
from typing import Any, List, Optional, TypedDict, Union, cast

import clickhouse_connect
from clickhouse_connect.driver.client import Client
import ray

from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from .schema import (
    AdjustNeedsRecord,
    AgentLocationTypeRecord,
    AgentTransportTypeRecord,
    BlockDispatcherRecord,
    ExperimentInfoRecord,
    PromptResponseRecord,
    StaticAgentAttributesRecord,
    StepAgentStatusRecord,
)

TableRecord = Union[
    AdjustNeedsRecord,
    PromptResponseRecord,
    AgentLocationTypeRecord,
    AgentTransportTypeRecord,
    StepAgentStatusRecord,
    BlockDispatcherRecord,
    StaticAgentAttributesRecord,
    ExperimentInfoRecord,
]


class TableBatchState(TypedDict):
    batch: deque[TableRecord]
    last_flush_time: float


class ClickHouseDatabase:
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
        self.exp_id = exp_id
        self.home_dir = Path(home_dir)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.auto_create_database = auto_create_database
        self.db_path = self.home_dir / "clickhouse"
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.migrations_dir = Path(__file__).resolve().parent / "migrations"
        self._metrics_actor = metrics_actor

        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        self.table_schemas: dict[str, type] = {
            "NeedsBlock_adjust_needs": AdjustNeedsRecord,
            "prompt_responses": PromptResponseRecord,
            "agent_location_type": AgentLocationTypeRecord,
            "agent_transport_type": AgentTransportTypeRecord,
            "step_agent_status": StepAgentStatusRecord,
            "block_dispatcher": BlockDispatcherRecord,
            "static_agent_attributes": StaticAgentAttributesRecord,
            "experiment_info": ExperimentInfoRecord,
        }

        self.table_columns: dict[str, List[str]] = {
            table_name: list(schema.__annotations__.keys())
            for table_name, schema in self.table_schemas.items()
        }
        # This column is persisted in ClickHouse but inferred from DB state.
        self.table_columns["NeedsBlock_adjust_needs"].insert(1, "simulation_step")

        self.table_batches: dict[str, TableBatchState] = {
            table_name: {
                "batch": deque(),
                "last_flush_time": time.time(),
            }
            for table_name in self.table_columns
        }

        self.simulation_step = -1

        self.client: Optional[Client] = None
        self._connect()
        self._create_tables()

        get_logger().info(f"ClickHouseDatabase initialized with {batch_size=}")

    def _record_metric(self, table_name: str, size: int) -> None:
        if self._metrics_actor is None:
            return
        self._metrics_actor.record_table_records.remote(table_name, size)

    def _connect(self):
        """Establish connection to ClickHouse server."""
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
            query = migration_file.read_text(encoding="utf-8").strip()
            if not query:
                get_logger().warning(
                    f"Skipping empty migration file '{migration_file.name}'."
                )
                continue

            try:
                self.client.command(query)
                get_logger().debug(f"Applied migration '{migration_file.name}'.")
            except Exception as migration_error:
                failed_migrations.append(migration_file.name)
                get_logger().error(
                    f"Failed migration '{migration_file.name}': {migration_error}"
                )

        if failed_migrations:
            get_logger().warning(
                "Completed table initialization with failed migrations: "
                + ", ".join(failed_migrations)
            )
        else:
            get_logger().info("Tables created successfully in ClickHouse database.")

    def set_simulation_step(self, step: int):
        self.simulation_step = step

    def _clean_incoming_record(self, timestamp: Any, agent_id: Any):
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()

        if not isinstance(agent_id, int):
            try:
                agent_id = int(agent_id)
            except (ValueError, TypeError):
                agent_id = -1

        return timestamp, agent_id

    def _record_value(self, record: TableRecord, column_name: str) -> Any:
        raw_record = cast(dict[str, Any], record)
        if column_name == "simulation_step" and "simulation_step" not in raw_record:
            return self.simulation_step
        return raw_record[column_name]

    @staticmethod
    def _is_unknown_table_error(error: Exception) -> bool:
        message = str(error)
        return "UNKNOWN_TABLE" in message or "does not exist" in message

    def _flush_table_batch(self, table_name: str) -> None:
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot flush batch."
            )
            return

        table_state = self.table_batches.get(table_name)
        if table_state is None:
            get_logger().error(f"Unknown table '{table_name}'. Cannot flush batch.")
            return

        if not table_state["batch"]:
            return

        column_names = self.table_columns.get(table_name)
        if column_names is None:
            get_logger().error(f"No columns configured for table '{table_name}'.")
            return

        try:
            records = list(table_state["batch"])
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

            table_state["batch"].clear()
            table_state["last_flush_time"] = time.time()
            self._record_metric(table_name, len(records))
        except Exception as e:
            if self._is_unknown_table_error(e):
                get_logger().warning(
                    f"Table '{table_name}' is missing. Re-applying migrations and retrying batch flush once."
                )
                try:
                    self._create_tables()
                    self.client.insert(
                        table_name,
                        column_data,
                        column_names=column_names,
                        column_oriented=True,
                    )
                    table_state["batch"].clear()
                    table_state["last_flush_time"] = time.time()
                    self._record_metric(table_name, len(records))
                    get_logger().info(
                        f"Recovered missing table '{table_name}' and flushed pending batch."
                    )
                    return
                except Exception as retry_error:
                    get_logger().error(
                        f"Retry after recreating table '{table_name}' failed: {retry_error}"
                    )

            get_logger().error(f"Failed to flush '{table_name}' batch to ClickHouse: {e}")

    def _queue_record(self, table_name: str, record: TableRecord) -> None:
        table_state = self.table_batches.get(table_name)
        if table_state is None:
            get_logger().error(f"Unknown table '{table_name}'. Cannot queue record.")
            return

        table_state["batch"].append(record)
        if (len(table_state["batch"]) >= self.batch_size) or (
            time.time() - table_state["last_flush_time"] >= self.batch_timeout
        ):
            self._flush_table_batch(table_name)

    def insert_adjust_needs_record(self, record: AdjustNeedsRecord) -> None:
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert record."
            )
            return

        timestamp, agent_id = self._clean_incoming_record(
            record["timestamp"], record["agent_id"]
        )
        normalized_record: AdjustNeedsRecord = {
            **record,
            "exp_id": self.exp_id,
            "timestamp": timestamp,
            "agent_id": agent_id,
        }
        self._queue_record("NeedsBlock_adjust_needs", normalized_record)

    def insert_prompt_response_record(
        self,
        timestamp: datetime,
        agent_id: int,
        prompt: str,
        response: str,
        block_name: str,
        func_name: str,
    ):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert prompt-response record."
            )
            return

        try:
            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            if not isinstance(response, str):
                if hasattr(response, "choices") and len(response.choices) > 0:
                    response = response.choices[0].message.content or ""
                else:
                    response = str(response)

            if not isinstance(prompt, str):
                prompt = str(prompt)

            record: PromptResponseRecord = {
                "exp_id": self.exp_id,
                "simulation_step": self.simulation_step,
                "timestamp": timestamp,
                "agent_id": agent_id,
                "prompt": prompt,
                "response": response,
                "block_name": block_name,
                "func_name": func_name,
            }
            self._queue_record("prompt_responses", record)

        except Exception as e:
            get_logger().error(f"Failed to insert prompt-response record: {e}")

    def insert_user_location_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        location_type: str,
    ):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert agent location type record."
            )
            return

        try:
            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            record: AgentLocationTypeRecord = {
                "exp_id": self.exp_id,
                "simulation_step": self.simulation_step,
                "timestamp": timestamp,
                "agent_id": agent_id,
                "location_type": location_type,
            }
            self._queue_record("agent_location_type", record)

        except Exception as e:
            get_logger().error(f"Failed to insert agent location type record: {e}")

    def insert_user_transport_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        transport_type: str,
    ):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert agent transport type record."
            )
            return

        try:
            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            record: AgentTransportTypeRecord = {
                "exp_id": self.exp_id,
                "simulation_step": self.simulation_step,
                "timestamp": timestamp,
                "agent_id": agent_id,
                "transport_type": transport_type,
            }
            self._queue_record("agent_transport_type", record)

        except Exception as e:
            get_logger().error(f"Failed to insert agent transport type record: {e}")

    def insert_step_agent_status_record(
        self,
        agent_id: int,
        timestamp: datetime,
        lat: float,
        lng: float,
        parent_id: int,
        action: str,
        status: str,
    ):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert step agent status record."
            )
            return

        try:
            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            record: StepAgentStatusRecord = {
                "exp_id": self.exp_id,
                "agent_id": agent_id,
                "simulation_step": self.simulation_step,
                "timestamp": timestamp,
                "lat": lat,
                "lng": lng,
                "parent_id": parent_id,
                "action": action,
                "status": status,
            }
            self._queue_record("step_agent_status", record)

        except Exception as e:
            get_logger().error(f"Failed to insert step agent status record: {e}")

    def insert_block_dispatcher_record(
        self,
        agent_id: int,
        timestamp: datetime,
        target_block: str,
        reason: str,
        possible_blocks: List[str],
        ctx_time: str,
        ctx_need: str,
        ctx_intention: str,
        ctx_emotion: str,
        ctx_thought: str,
        ctx_location: str,
        ctx_area_info: str,
        ctx_weather: str,
        ctx_temperature: int,
        ctx_other_info: str,
        ctx_plan_target: str,
    ):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert block dispatcher record."
            )
            return

        record: Optional[BlockDispatcherRecord] = None
        try:
            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            record = {
                "exp_id": self.exp_id,
                "agent_id": agent_id,
                "simulation_step": self.simulation_step,
                "timestamp": timestamp,
                "target_block": target_block,
                "reason": reason,
                "possible_blocks": possible_blocks,
                "ctx_time": ctx_time,
                "ctx_need": ctx_need,
                "ctx_intention": ctx_intention,
                "ctx_emotion": ctx_emotion,
                "ctx_thought": ctx_thought,
                "ctx_location": ctx_location,
                "ctx_area_info": ctx_area_info,
                "ctx_weather": ctx_weather,
                "ctx_temperature": ctx_temperature,
                "ctx_other_info": ctx_other_info,
                "ctx_plan_target": ctx_plan_target,
            }

            self._queue_record("block_dispatcher", record)

        except Exception as e:
            get_logger().error(
                f"Failed to insert block dispatcher record: {e}. Record: {record}"
            )

    def insert_static_agent_attributes_record(
        self, record: StaticAgentAttributesRecord
    ) -> None:
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert static agent attributes record."
            )
            return

        try:
            timestamp, agent_id = self._clean_incoming_record(
                record["timestamp"], record["agent_id"]
            )

            normalized_record: StaticAgentAttributesRecord = {
                **record,
                "exp_id": self.exp_id,
                "simulation_step": self.simulation_step,
                "timestamp": timestamp,
                "agent_id": agent_id,
            }
            self._queue_record("static_agent_attributes", normalized_record)

        except Exception as e:
            get_logger().error(
                f"Failed to insert static agent attributes record: {e}"
            )

    def insert_experiment_info_record(self, record: ExperimentInfoRecord) -> None:
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert experiment info record."
            )
            return

        try:
            created_at = record["created_at"]
            updated_at = record["updated_at"]
            if isinstance(created_at, (int, float)):
                created_at = datetime.fromtimestamp(created_at)
            if isinstance(updated_at, (int, float)):
                updated_at = datetime.fromtimestamp(updated_at)
            if not isinstance(created_at, datetime):
                created_at = datetime.now()
            if not isinstance(updated_at, datetime):
                updated_at = datetime.now()

            normalized_record: ExperimentInfoRecord = {
                **record,
                "id": str(uuid.UUID(record["id"])),
                "created_at": created_at,
                "updated_at": updated_at,
            }
            self._queue_record("experiment_info", normalized_record)

        except Exception as e:
            get_logger().error(f"Failed to insert experiment info record: {e}")

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
            return [dict(zip(column_names, row)) for row in rows]
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
                "input_tokens, output_tokens, created_at, updated_at "
                "FROM experiment_info "
                f"WHERE id = toUUID('{escaped_source_uuid}') "
                "ORDER BY updated_at DESC "
                "LIMIT 1"
            )
        )
        if not exp_info_rows:
            return None

        step_rows = self._query_rows(
            (
                "SELECT max(simulation_step) AS max_step "
                "FROM step_agent_status "
                f"WHERE exp_id = '{escaped_exp_id}'"
            )
        )
        latest_step_raw = step_rows[0].get("max_step") if step_rows else None
        latest_step = int(latest_step_raw) if latest_step_raw is not None else 0

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

        latest_exp_info = exp_info_rows[0]

        return {
            "source_exp_id": source_exp_id,
            "config": str(latest_exp_info.get("config") or ""),
            "latest_experiment_info": latest_exp_info,
            "latest_step": latest_step,
            "static_step": static_step,
            "static_records": static_rows,
        }

    def flush_all_batches(self):
        for table_name in self.table_batches:
            self._flush_table_batch(table_name)

    def close(self):
        if self.client:
            self.flush_all_batches()
            self.client.close()
            get_logger().info("ClickHouse client connection closed.")
