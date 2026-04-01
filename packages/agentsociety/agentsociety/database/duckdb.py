from __future__ import annotations

from collections import deque
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any, List, Optional, TypedDict, Union, cast
import uuid

try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore[assignment]

import ray

from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from .schema import (
    AdjustNeedsRecord,
    AgentKVSnapshotRecord,
    AgentLocationTypeRecord,
    AgentSpatialSnapshotRecord,
    AgentStreamSnapshotRecord,
    AgentTransportTypeRecord,
    BlockDispatcherRecord,
    ExperimentInfoRecord,
    PendingMessageSnapshotRecord,
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
    AgentKVSnapshotRecord,
    AgentStreamSnapshotRecord,
    AgentSpatialSnapshotRecord,
    PendingMessageSnapshotRecord,
]


class TableBatchState(TypedDict):
    batch: deque[TableRecord]
    last_flush_time: float


class DuckDBDatabase:
    """DuckDB database manager for simulation telemetry and batch writes."""

    def __init__(
        self,
        exp_id: str,
        home_dir: str,
        batch_size: int = 128,
        batch_timeout: float = 30.0,
        metrics_actor: Optional[ray.actor.ActorHandle[PrometheusActor]] = None,
    ):
        self.exp_id = exp_id
        self.home_dir = Path(home_dir)
        self.db_path = self.home_dir / "duckdb"
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.db_file = self.db_path / f"{self.exp_id}.duckdb"
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
            "agent_kv_snapshot": AgentKVSnapshotRecord,
            "agent_stream_snapshot": AgentStreamSnapshotRecord,
            "agent_spatial_snapshot": AgentSpatialSnapshotRecord,
            "pending_messages_snapshot": PendingMessageSnapshotRecord,
        }

        self.table_columns: dict[str, List[str]] = {
            table_name: list(schema.__annotations__.keys())
            for table_name, schema in self.table_schemas.items()
        }
        self.table_columns["NeedsBlock_adjust_needs"].insert(1, "simulation_step")

        self.table_batches: dict[str, TableBatchState] = {
            table_name: {
                "batch": deque(),
                "last_flush_time": time.time(),
            }
            for table_name in self.table_columns
        }

        self.simulation_step = -1

        self.conn: Optional[Any] = None
        self._connect()
        self._create_tables()

        get_logger().info(
            f"DuckDBDatabase initialized with {batch_size=}, db_file='{self.db_file}'"
        )

    @property
    def backend_name(self) -> str:
        return "duckdb"

    def is_available(self) -> bool:
        if self.conn is None:
            return False
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception as e:
            get_logger().error(f"DuckDB health check failed: {e}")
            return False

    def _record_metric(self, table_name: str, size: int) -> None:
        if self._metrics_actor is None:
            return
        self._metrics_actor.record_table_records.remote(table_name, size)

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

        migration_files = sorted(self.migrations_dir.glob("*.duckdb.sql"))
        if not migration_files:
            get_logger().warning(
                f"No DuckDB migration files found in '{self.migrations_dir}'."
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

            statements = [s.strip() for s in raw.split(";") if s.strip()]
            migration_failed = False
            for statement in statements:
                try:
                    self.conn.execute(statement)
                except Exception as migration_error:
                    migration_failed = True
                    get_logger().error(
                        f"Failed DuckDB migration '{migration_file.name}' statement: {migration_error}"
                    )
            if migration_failed:
                failed_migrations.append(migration_file.name)
            else:
                get_logger().debug(
                    f"Applied DuckDB migration '{migration_file.name}'."
                )

        if failed_migrations:
            get_logger().warning(
                "Completed DuckDB table initialization with failed migrations: "
                + ", ".join(failed_migrations)
            )
        else:
            get_logger().info("Tables created successfully in DuckDB database.")

    def set_simulation_step(self, step: int) -> None:
        self.simulation_step = step

    def _clean_incoming_record(self, timestamp: Any, agent_id: Any) -> tuple[datetime, int]:
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

        value = raw_record[column_name]
        if column_name in {"possible_blocks", "hobbies"}:
            return json.dumps(value if value is not None else [])
        return value

    def _flush_table_batch(self, table_name: str) -> None:
        if self.conn is None:
            get_logger().error("DuckDB connection is not available. Cannot flush batch.")
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

            table_state["batch"].clear()
            table_state["last_flush_time"] = time.time()
            self._record_metric(table_name, len(records))
        except Exception as e:
            get_logger().error(f"Failed to flush '{table_name}' batch to DuckDB: {e}")

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
        if self.conn is None:
            get_logger().error("DuckDB connection is not available. Cannot insert record.")
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
    ) -> None:
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot insert prompt-response record."
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
    ) -> None:
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot insert agent location type record."
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
    ) -> None:
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot insert agent transport type record."
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
    ) -> None:
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot insert step agent status record."
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
    ) -> None:
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot insert block dispatcher record."
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
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot insert static agent attributes record."
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
            get_logger().error(f"Failed to insert static agent attributes record: {e}")

    def insert_experiment_info_record(self, record: ExperimentInfoRecord) -> None:
        if self.conn is None:
            get_logger().error(
                "DuckDB connection is not available. Cannot insert experiment info record."
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
                "last_mobility_safe_step": record.get("last_mobility_safe_step", -1),
                "prev_mobility_safe_step": record.get("prev_mobility_safe_step", -1),
                "economy_checkpoint_path": record.get("economy_checkpoint_path", ""),
            }
            self._queue_record("experiment_info", normalized_record)

        except Exception as e:
            get_logger().error(f"Failed to insert experiment info record: {e}")

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

    def insert_kv_snapshot_batch(self, records: List[AgentKVSnapshotRecord]) -> None:
        if self.conn is None:
            return
        try:
            for record in records:
                self._queue_record("agent_kv_snapshot", record)
        except Exception as e:
            get_logger().error(f"Failed to insert KV snapshot batch: {e}")

    def insert_stream_snapshot_batch(self, records: List[AgentStreamSnapshotRecord]) -> None:
        if self.conn is None:
            return
        try:
            for record in records:
                self._queue_record("agent_stream_snapshot", record)
        except Exception as e:
            get_logger().error(f"Failed to insert stream snapshot batch: {e}")

    def insert_spatial_snapshot_batch(self, records: List[AgentSpatialSnapshotRecord]) -> None:
        if self.conn is None:
            return
        try:
            for record in records:
                self._queue_record("agent_spatial_snapshot", record)
        except Exception as e:
            get_logger().error(f"Failed to insert spatial snapshot batch: {e}")

    def insert_pending_messages_snapshot(self, records: List[PendingMessageSnapshotRecord]) -> None:
        if self.conn is None:
            return
        try:
            for record in records:
                self._queue_record("pending_messages_snapshot", record)
        except Exception as e:
            get_logger().error(f"Failed to insert pending messages snapshot: {e}")

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
            self.insert_experiment_info_record(new_record)
        except Exception as e:
            get_logger().error(f"Failed to update experiment_info checkpoint columns: {e}")

    def flush_all_batches(self) -> None:
        for table_name in self.table_batches:
            self._flush_table_batch(table_name)

    def close(self) -> None:
        if self.conn is not None:
            self.flush_all_batches()
            self.conn.close()
            get_logger().info("DuckDB connection closed.")
