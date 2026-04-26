from typing import Any, Optional
from datetime import datetime

import ray

from ..logger import get_logger
from .clickhouse import ClickHouseConfig, ClickHouseDatabase
from .duckdb import DuckDBConfig, DuckDBDatabase
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
        clickhouse_config: Optional[ClickHouseConfig] = None,
        batch_size: int = 128,
        batch_timeout: float = 30.0,
        metrics_actor: Optional[Any] = None,
        duckdb_config: Optional[DuckDBConfig] = None,
    ):
        resolved_clickhouse_config = clickhouse_config or ClickHouseConfig()

        clickhouse_db = ClickHouseDatabase(
            exp_id=exp_id,
            home_dir=home_dir,
            batch_size=batch_size,
            batch_timeout=batch_timeout,
            metrics_actor=metrics_actor,
            config=resolved_clickhouse_config,
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
                config=duckdb_config,
            )
            if not self._db.is_available():
                raise RuntimeError(
                    "Failed to initialize both ClickHouse and DuckDB backends."
                )

            get_logger().info("DatabaseActor initialized with DuckDB backend")

    def set_simulation_step(self, step: int):
        self._db.set_simulation_step(step)

    def _current_simulation_step(self) -> int:
        return getattr(self._db, "simulation_step", -1)

    @staticmethod
    def _to_model_list(records: list[Any], model_cls: Any) -> list[Any]:
        normalized: list[Any] = []
        for record in records:
            if isinstance(record, model_cls):
                normalized.append(record)
            else:
                normalized.append(model_cls.model_validate(record))
        return normalized

    def insert_adjust_needs_record(self, record: AdjustNeedsRecord | dict[str, Any]) -> None:
        normalized = (
            record
            if isinstance(record, AdjustNeedsRecord)
            else AdjustNeedsRecord.model_validate(record)
        )
        self._db.insert_record("NeedsBlock_adjust_needs", normalized)

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

        record = PromptResponseRecord(
            simulation_step=self._current_simulation_step(),
            timestamp=timestamp,
            agent_id=agent_id,
            prompt=prompt_text,
            response=response_text,
            block_name=block_name,
            func_name=func_name,
        )
        self._db.insert_record("prompt_responses", record)

    def insert_user_location_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        location_type: str,
    ):
        record = AgentLocationTypeRecord(
            simulation_step=self._current_simulation_step(),
            timestamp=timestamp,
            agent_id=agent_id,
            location_type=location_type,
        )
        self._db.insert_record("agent_location_type", record)

    def insert_user_transport_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        transport_type: str,
    ):
        record = AgentTransportTypeRecord(
            simulation_step=self._current_simulation_step(),
            timestamp=timestamp,
            agent_id=agent_id,
            transport_type=transport_type,
        )
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
        record = StepAgentStatusRecord(
            agent_id=agent_id,
            simulation_step=self._current_simulation_step(),
            timestamp=timestamp,
            lat=lat,
            lng=lng,
            parent_id=parent_id,
            action=action,
            status=status,
        )
        self._db.insert_record("step_agent_status", record)

    def insert_block_dispatcher_record(
        self,
        agent_id: int,
        timestamp: datetime,
        target_block: str,
        reason: str,
        possible_blocks: list[str],
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
        record = BlockDispatcherRecord(
            agent_id=agent_id,
            simulation_step=self._current_simulation_step(),
            timestamp=timestamp,
            target_block=target_block,
            reason=reason,
            possible_blocks=possible_blocks,
            ctx_time=ctx_time,
            ctx_need=ctx_need,
            ctx_intention=ctx_intention,
            ctx_emotion=ctx_emotion,
            ctx_thought=ctx_thought,
            ctx_location=ctx_location,
            ctx_area_info=ctx_area_info,
            ctx_weather=ctx_weather,
            ctx_temperature=ctx_temperature,
            ctx_other_info=ctx_other_info,
            ctx_plan_target=ctx_plan_target,
        )
        self._db.insert_record("block_dispatcher", record)

    def insert_experiment_info_record(
        self, record: ExperimentInfoRecord | dict[str, Any]
    ):
        normalized = (
            record
            if isinstance(record, ExperimentInfoRecord)
            else ExperimentInfoRecord.model_validate(record)
        )
        self._db.insert_record("experiment_info", normalized)

    def insert_kv_snapshot_batch(
        self, records: list[AgentKVSnapshotRecord | dict[str, Any]]
    ) -> None:
        normalized = self._to_model_list(records, AgentKVSnapshotRecord)
        self._db.insert_records("agent_kv_snapshot", normalized)

    def insert_stream_snapshot_batch(
        self, records: list[AgentStreamSnapshotRecord | dict[str, Any]]
    ) -> None:
        normalized = self._to_model_list(records, AgentStreamSnapshotRecord)
        self._db.insert_records("agent_stream_snapshot", normalized)

    def insert_spatial_snapshot_batch(
        self, records: list[AgentSpatialSnapshotRecord | dict[str, Any]]
    ) -> None:
        normalized = self._to_model_list(records, AgentSpatialSnapshotRecord)
        self._db.insert_records("agent_spatial_snapshot", normalized)

    def insert_pending_messages_snapshot(
        self, records: list[PendingMessageSnapshotRecord | dict[str, Any]]
    ) -> None:
        normalized = self._to_model_list(records, PendingMessageSnapshotRecord)
        self._db.insert_records("pending_messages_snapshot", normalized)

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

    def fetch_resume_data(
        self,
        source_exp_id: str,
        rollback_depth: int = 10,
        expected_agent_ids: Optional[set[int]] = None,
    ) -> Optional[dict[str, Any]]:
        resolved_expected_agent_ids = expected_agent_ids or set()
        try:
            data = self._db.fetch_resume_data(
                source_exp_id,
                rollback_depth=rollback_depth,
                expected_agent_ids=resolved_expected_agent_ids,
            )
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
