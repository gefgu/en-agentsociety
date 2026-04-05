from __future__ import annotations

from typing import List, Optional
from datetime import datetime

import ray

from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from .clickhouse import ClickHouseDatabase
from .duckdb import DuckDBDatabase
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
    StepAgentStatusRecord,
)


@ray.remote
class DatabaseActor:
    """Ray actor wrapper around simulation telemetry databases.

    It tries ClickHouse first and falls back to DuckDB at initialization time.
    """

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
        clickhouse_db = ClickHouseDatabase(
            exp_id=exp_id,
            home_dir=home_dir,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            batch_size=batch_size,
            batch_timeout=batch_timeout,
            auto_create_database=auto_create_database,
            metrics_actor=metrics_actor,
        )


        if clickhouse_db.is_available():
            self._db = clickhouse_db
            get_logger().info("DatabaseActor initialized with ClickHouse backend")
        else:
            get_logger().warning(
                "ClickHouse unavailable at startup. Falling back to DuckDB backend."
            )
            self._db = DuckDBDatabase(
                exp_id=exp_id,
                home_dir=home_dir,
                batch_size=batch_size,
                batch_timeout=batch_timeout,
                metrics_actor=metrics_actor,
            )
            if not self._db.is_available():
                raise RuntimeError(
                    "Failed to initialize both ClickHouse and DuckDB backends."
                )

            get_logger().info("DatabaseActor initialized with DuckDB backend")

    def set_simulation_step(self, step: int):
        self._db.set_simulation_step(step)

    def insert_adjust_needs_record(self, record: AdjustNeedsRecord) -> None:
        self._db.insert_record("NeedsBlock_adjust_needs", record)

    def insert_prompt_response_record(
        self,
        timestamp: datetime,
        agent_id: int,
        prompt: str,
        response: str,
        block_name: str,
        func_name: str,
    ):
        response_text = response
        if not isinstance(response_text, str):
            if hasattr(response_text, "choices") and len(response_text.choices) > 0:
                response_text = response_text.choices[0].message.content or ""
            else:
                response_text = str(response_text)

        prompt_text = prompt if isinstance(prompt, str) else str(prompt)

        record: PromptResponseRecord = {
            "exp_id": "",
            "simulation_step": -1,
            "timestamp": timestamp,
            "agent_id": agent_id,
            "prompt": prompt_text,
            "response": response_text,
            "block_name": block_name,
            "func_name": func_name,
        }
        self._db.insert_record("prompt_responses", record)

    def insert_user_location_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        location_type: str,
    ):
        record: AgentLocationTypeRecord = {
            "exp_id": "",
            "simulation_step": -1,
            "timestamp": timestamp,
            "agent_id": agent_id,
            "location_type": location_type,
        }
        self._db.insert_record("agent_location_type", record)

    def insert_user_transport_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        transport_type: str,
    ):
        record: AgentTransportTypeRecord = {
            "exp_id": "",
            "simulation_step": -1,
            "timestamp": timestamp,
            "agent_id": agent_id,
            "transport_type": transport_type,
        }
        self._db.insert_record("agent_transport_type", record)

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
        record: StepAgentStatusRecord = {
            "exp_id": "",
            "agent_id": agent_id,
            "simulation_step": -1,
            "timestamp": timestamp,
            "lat": lat,
            "lng": lng,
            "parent_id": parent_id,
            "action": action,
            "status": status,
        }
        self._db.insert_record("step_agent_status", record)

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
        record: BlockDispatcherRecord = {
            "exp_id": "",
            "agent_id": agent_id,
            "simulation_step": -1,
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
        self._db.insert_record("block_dispatcher", record)

    def insert_experiment_info_record(self, record: ExperimentInfoRecord):
        self._db.insert_record("experiment_info", record)

    def insert_kv_snapshot_batch(self, records: List[AgentKVSnapshotRecord]) -> None:
        self._db.insert_records("agent_kv_snapshot", records)

    def insert_stream_snapshot_batch(self, records: List[AgentStreamSnapshotRecord]) -> None:
        self._db.insert_records("agent_stream_snapshot", records)

    def insert_spatial_snapshot_batch(self, records: List[AgentSpatialSnapshotRecord]) -> None:
        self._db.insert_records("agent_spatial_snapshot", records)

    def insert_pending_messages_snapshot(self, records: List[PendingMessageSnapshotRecord]) -> None:
        self._db.insert_records("pending_messages_snapshot", records)

    def update_experiment_info_checkpoint(
        self,
        exp_id: str,
        last_mobility_safe_step: int,
        prev_mobility_safe_step: int,
        economy_checkpoint_path: str,
    ) -> None:
        self._db.update_experiment_info_checkpoint(
            exp_id=exp_id,
            last_mobility_safe_step=last_mobility_safe_step,
            prev_mobility_safe_step=prev_mobility_safe_step,
            economy_checkpoint_path=economy_checkpoint_path,
        )

    def fetch_resume_data(self, source_exp_id: str, rollback_depth: int = 10):
        try:
            data = self._db.fetch_resume_data(source_exp_id, rollback_depth=rollback_depth)
            if data is not None:
                get_logger().info(
                    f"Loaded resume data for source_exp_id={source_exp_id} from primary backend={self._db.backend_name}"
                )
                return data
        except Exception as e:
            get_logger().warning(
                f"Resume probe failed on primary backend={self._db.backend_name}: {e}"
            )

        return None


    def flush_all_batches(self):
        self._db.flush_all_batches()

    def close(self):
        self._db.close()
