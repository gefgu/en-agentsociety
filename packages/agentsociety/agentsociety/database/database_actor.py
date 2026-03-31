from __future__ import annotations

from typing import List, Optional
from datetime import datetime

import ray

from ..performance.prometheusActor import PrometheusActor
from .clickhouse import ClickHouseDatabase
from .schema import (
    AdjustNeedsRecord,
    AgentKVSnapshotRecord,
    AgentSpatialSnapshotRecord,
    AgentStreamSnapshotRecord,
    PendingMessageSnapshotRecord,
    StaticAgentAttributesRecord,
)


@ray.remote
class DatabaseActor:
    """Ray actor wrapper around ClickHouseDatabase."""

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
        self._db = ClickHouseDatabase(
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

    def set_simulation_step(self, step: int):
        self._db.set_simulation_step(step)

    def insert_adjust_needs_record(self, record: AdjustNeedsRecord) -> None:
        self._db.insert_adjust_needs_record(record)

    def insert_prompt_response_record(
        self,
        timestamp: datetime,
        agent_id: int,
        prompt: str,
        response: str,
        block_name: str,
        func_name: str,
    ):
        self._db.insert_prompt_response_record(
            timestamp=timestamp,
            agent_id=agent_id,
            prompt=prompt,
            response=response,
            block_name=block_name,
            func_name=func_name,
        )

    def insert_user_location_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        location_type: str,
    ):
        self._db.insert_user_location_type_record(
            timestamp=timestamp,
            agent_id=agent_id,
            location_type=location_type,
        )

    def insert_user_transport_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        transport_type: str,
    ):
        self._db.insert_user_transport_type_record(
            timestamp=timestamp,
            agent_id=agent_id,
            transport_type=transport_type,
        )

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
        self._db.insert_step_agent_status_record(
            agent_id=agent_id,
            timestamp=timestamp,
            lat=lat,
            lng=lng,
            parent_id=parent_id,
            action=action,
            status=status,
        )

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
        self._db.insert_block_dispatcher_record(
            agent_id=agent_id,
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

    def insert_static_agent_attributes_record(
        self,
        record: StaticAgentAttributesRecord,
    ) -> None:
        self._db.insert_static_agent_attributes_record(record)

    def insert_experiment_info_record(self, record):
        self._db.insert_experiment_info_record(record)

    def insert_kv_snapshot_batch(self, records: List[AgentKVSnapshotRecord]) -> None:
        self._db.insert_kv_snapshot_batch(records)

    def insert_stream_snapshot_batch(self, records: List[AgentStreamSnapshotRecord]) -> None:
        self._db.insert_stream_snapshot_batch(records)

    def insert_spatial_snapshot_batch(self, records: List[AgentSpatialSnapshotRecord]) -> None:
        self._db.insert_spatial_snapshot_batch(records)

    def insert_pending_messages_snapshot(self, records: List[PendingMessageSnapshotRecord]) -> None:
        self._db.insert_pending_messages_snapshot(records)

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

    def fetch_resume_data(self, source_exp_id: str):
        return self._db.fetch_resume_data(source_exp_id)

    def flush_all_batches(self):
        self._db.flush_all_batches()

    def close(self):
        self._db.close()