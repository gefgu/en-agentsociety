import asyncio
import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any, Literal, Optional

from ..agent import (
    BankAgentBase,
    CitizenAgentBase,
    FirmAgentBase,
    GovernmentAgentBase,
    NBSAgentBase,
)
from ..database.database_actor import DatabaseActor
from ..logger import get_logger
from ..performance.prometheusActor import PrometheusActor
from ..storage import DatabaseWriter
from ..storage.type import StorageExpInfo, StorageGlobalPrompt

RecorderEventType = Literal[
    "dialog",
    "survey",
    "global_prompt",
    "exp_info",
    "clickhouse_status",
    "kv_snapshot",
    "stream_snapshot",
    "spatial_snapshot",
    "message_snapshot",
    "profile",
    "metric",
    "task_result",
    "flush",
    "stop",
]


@dataclass
class RecorderEvent:
    event_type: RecorderEventType
    payload: Any = None
    future: Optional[asyncio.Future[None]] = None
    step: Optional[int] = None


class DataRecorder:
    """Async write-through recorder for simulation persistence sinks."""

    def __init__(
        self,
        database_writer: Optional[DatabaseWriter],
        db_actor: Optional[DatabaseActor],
        metrics_actor: Optional[PrometheusActor],
        *,
        queue_maxsize: int = 0,
        enqueue_timeout_seconds: float = 5.0,
        close_timeout_seconds: float = 30.0,
    ) -> None:
        self._database_writer = database_writer
        self._db_actor = db_actor
        self._metrics_actor = metrics_actor
        self._queue: asyncio.Queue[RecorderEvent] = asyncio.Queue(maxsize=queue_maxsize)
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._enqueue_timeout_seconds = enqueue_timeout_seconds
        self._close_timeout_seconds = close_timeout_seconds
        self._is_stopping = False

        self.processed_events = 0
        self.retried_events = 0
        self.dropped_events = 0
        self.failed_events = 0

    def start_background_worker(self) -> None:
        if self._worker_task is not None and not self._worker_task.done():
            return
        self._is_stopping = False
        self._worker_task = asyncio.create_task(self._process_queue())
        get_logger().info("DataRecorder background worker started")

    async def enqueue_dialog(self, rows: list[Any]) -> None:
        await self._enqueue(RecorderEvent(event_type="dialog", payload=rows))

    async def enqueue_survey(self, rows: list[Any]) -> None:
        await self._enqueue(RecorderEvent(event_type="survey", payload=rows))

    async def enqueue_exp_info(self, exp_info: StorageExpInfo) -> None:
        await self._enqueue(RecorderEvent(event_type="exp_info", payload=exp_info))

    async def enqueue_global_prompt(self, prompt_info: StorageGlobalPrompt) -> None:
        await self._enqueue(RecorderEvent(event_type="global_prompt", payload=prompt_info))

    async def enqueue_clickhouse_status(self, record: dict[str, Any]) -> None:
        await self._enqueue(RecorderEvent(event_type="clickhouse_status", payload=record))

    async def enqueue_kv_snapshot(self, records: list[dict[str, Any]]) -> None:
        await self._enqueue(RecorderEvent(event_type="kv_snapshot", payload=records))

    async def enqueue_stream_snapshot(self, records: list[dict[str, Any]]) -> None:
        await self._enqueue(RecorderEvent(event_type="stream_snapshot", payload=records))

    async def enqueue_spatial_snapshot(self, records: list[dict[str, Any]]) -> None:
        await self._enqueue(RecorderEvent(event_type="spatial_snapshot", payload=records))

    async def enqueue_message_snapshot(self, records: list[dict[str, Any]]) -> None:
        await self._enqueue(RecorderEvent(event_type="message_snapshot", payload=records))

    async def enqueue_profiles(self, records: list[dict[str, Any]]) -> None:
        await self._enqueue(RecorderEvent(event_type="profile", payload=records))

    async def enqueue_metrics(self, metrics: list[tuple[str, float, int]]) -> None:
        """Route metrics to ClickHouse/DuckDB."""
        records = [
            {"key": key, "value": value, "step": step, "created_at": datetime.now(timezone.utc)}
            for key, value, step in metrics
        ]
        await self._enqueue(RecorderEvent(event_type="metric", payload=records))

    async def enqueue_task_results(self, records: list[dict[str, Any]]) -> None:
        await self._enqueue(RecorderEvent(event_type="task_result", payload=records))

    async def save_exp_info(self, exp_info: StorageExpInfo) -> None:
        """Persist experiment info through recorder queue."""
        exp_info.updated_at = datetime.now(timezone.utc)
        if self._worker_task is None or self._worker_task.done():
            await self._process_event_once(
                RecorderEvent(event_type="exp_info", payload=exp_info)
            )
            return
        await self.enqueue_exp_info(exp_info)

    async def save_global_prompt(self, prompt: str, day: int, t: float) -> None:
        """Build and persist global prompt record through recorder queue."""
        prompt_info = StorageGlobalPrompt(
            day=day,
            t=t,
            prompt=prompt,
            created_at=datetime.now(timezone.utc),
        )
        await self.enqueue_global_prompt(prompt_info)

    async def save_statuses(self, day: int, t: int, agents: dict[int, Any], environment: Any) -> None:
        """Build and persist ClickHouse status rows (SQLite no longer stores statuses)."""
        if self._db_actor is None:
            return

        for agent in agents.values():
            if isinstance(agent, CitizenAgentBase):
                position = await agent.status.get("position")
                x = position["xy_position"]["x"]
                y = position["xy_position"]["y"]
                lng, lat = environment.projector(x, y, inverse=True)
                if "aoi_position" in position:
                    parent_id = position["aoi_position"]["aoi_id"]
                elif "lane_position" in position:
                    parent_id = position["lane_position"]["lane_id"]
                else:
                    parent_id = None

                current_plan = await agent.status.get("current_plan", {})
                if current_plan is not None and current_plan:
                    step_index = current_plan.get("index", 0)
                    steps = current_plan.get("steps", [])
                    if 0 <= step_index < len(steps):
                        action = steps[step_index].get("intention", "Planning")
                    else:
                        action = "Planning"
                else:
                    action = "Planning"

                status_summary = await agent.status.get("status_summary", "Nothing")

                await self.enqueue_clickhouse_status(
                    {
                        "agent_id": agent.id,
                        "lng": lng,
                        "lat": lat,
                        "parent_id": parent_id,
                        "action": action,
                        "status": status_summary,
                        "timestamp": time.time(),
                    }
                )

            elif isinstance(
                agent, (FirmAgentBase, BankAgentBase, NBSAgentBase, GovernmentAgentBase)
            ):
                status_summary = await agent.status.get("status_summary", "Nothing")
                await self.enqueue_clickhouse_status(
                    {
                        "agent_id": agent.id,
                        "lng": None,
                        "lat": None,
                        "parent_id": None,
                        "action": "",
                        "status": status_summary,
                        "timestamp": time.time(),
                    }
                )
            else:
                raise ValueError(f"Unknown agent type: {type(agent)}")

    async def record_block_performance_metrics(self, step: int) -> None:
        """Capture block performance from Prometheus actor and persist metrics."""
        if self._metrics_actor is None:
            get_logger().warning("No performance actor available to retrieve stats.")
            return

        try:
            perf_stats = await self._metrics_actor.get_block_performance_stats.remote()
            if not perf_stats:
                return

            metric_tuples: list[tuple[str, float, int]] = []
            for block_func, metrics in perf_stats.items():
                metric_tuples.extend(
                    [
                        (f"bp.{block_func}.calls", metrics["calls"], step),
                        (f"bp.{block_func}.avg_duration", metrics["average_duration"], step),
                        (f"bp.{block_func}.total_token_input", metrics["total_token_input"], step),
                        (f"bp.{block_func}.total_token_output", metrics["total_token_output"], step),
                    ]
                )

            await self.enqueue_metrics(metric_tuples)
        except Exception as e:
            get_logger().warning(f"Error retrieving block performance stats: {str(e)}")

    async def record_routing_metrics(self, step: int) -> None:
        """Capture routing stats from Prometheus actor and persist metrics."""
        if self._metrics_actor is None:
            get_logger().warning("No performance actor available to retrieve stats.")
            return

        try:
            perf_stats = await self._metrics_actor.get_routing_stats.remote()
            if not perf_stats:
                return

            metric_tuples: list[tuple[str, float, int]] = []
            for block_func, metrics in perf_stats.items():
                metric_tuples.extend(
                    [
                        (f"bp.{block_func}.calls", metrics["calls"], step),
                        (f"bp.{block_func}.routing_ratio", metrics["routing_ratio"], step),
                    ]
                )

            await self.enqueue_metrics(metric_tuples)
        except Exception as e:
            get_logger().warning(f"Error retrieving routing performance stats: {str(e)}")

    async def record_simulation_step_duration(self, duration: float, step: int) -> None:
        """Persist step duration metrics to ClickHouse/DuckDB and Prometheus actor."""
        await self.enqueue_metrics(
            [("simulation.step_duration_seconds", duration, step)]
        )
        if self._metrics_actor is not None:
            self._metrics_actor.record_simulation_step_duration.remote(duration)

    async def record_environment_metrics(self, metrics: list[tuple[str, float, int]]) -> None:
        """Persist environment metrics through recorder queue."""
        await self.enqueue_metrics(metrics)

    async def flush(self, step: Optional[int] = None) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[None] = loop.create_future()
        await self._enqueue(RecorderEvent(event_type="flush", future=future, step=step))
        await future

    async def stop_background_worker(self) -> None:
        if self._worker_task is None:
            return

        self._is_stopping = True
        flush_ok = True
        try:
            await asyncio.wait_for(self.flush(), timeout=self._close_timeout_seconds)
        except Exception as e:
            flush_ok = False
            get_logger().warning(
                f"DataRecorder flush timed out or failed during shutdown: {e}"
            )

        loop = asyncio.get_running_loop()
        stop_future: asyncio.Future[None] = loop.create_future()
        await self._enqueue(RecorderEvent(event_type="stop", future=stop_future))

        try:
            await asyncio.wait_for(stop_future, timeout=self._close_timeout_seconds)
            await asyncio.wait_for(self._worker_task, timeout=self._close_timeout_seconds)
        except Exception as e:
            get_logger().warning(f"DataRecorder worker did not stop cleanly: {e}")
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
        finally:
            self._worker_task = None

        if flush_ok:
            get_logger().info("DataRecorder stopped after full flush")
        else:
            get_logger().warning(
                "DataRecorder stopped with partial flush; some queued events may not be persisted"
            )

    async def _enqueue(self, event: RecorderEvent) -> None:
        if self._is_stopping and event.event_type not in {"flush", "stop"}:
            self.dropped_events += 1
            get_logger().warning(
                f"Dropping DataRecorder event {event.event_type} while stopping"
            )
            return

        try:
            await asyncio.wait_for(
                self._queue.put(event), timeout=self._enqueue_timeout_seconds
            )
        except Exception as e:
            self.dropped_events += 1
            get_logger().error(
                f"Failed to enqueue DataRecorder event {event.event_type}: {e}"
            )
            if event.future is not None and not event.future.done():
                event.future.set_exception(e)

    async def _write_recorder_counters(self, step: Optional[int]) -> None:
        if step is None:
            return

        counter_metrics: list[tuple[str, float, int]] = [
            ("datarecorder.events.processed", float(self.processed_events), step),
            ("datarecorder.events.retried", float(self.retried_events), step),
            ("datarecorder.events.dropped", float(self.dropped_events), step),
            ("datarecorder.events.failed", float(self.failed_events), step),
            ("datarecorder.queue.size", float(self._queue.qsize()), step),
        ]

        await self.enqueue_metrics(counter_metrics)

        if self._metrics_actor is not None:
            try:
                self._metrics_actor.record_table_records.remote(
                    "datarecorder.events.processed", self.processed_events
                )
                self._metrics_actor.record_table_records.remote(
                    "datarecorder.events.retried", self.retried_events
                )
                self._metrics_actor.record_table_records.remote(
                    "datarecorder.events.dropped", self.dropped_events
                )
                self._metrics_actor.record_table_records.remote(
                    "datarecorder.events.failed", self.failed_events
                )
            except Exception as e:
                get_logger().warning(f"Failed to emit DataRecorder counters to Prometheus actor: {e}")

    async def _process_event_once(self, event: RecorderEvent) -> None:
        if event.event_type == "dialog":
            rows = event.payload
            if self._database_writer is not None and rows:
                await self._database_writer.write_dialogs(rows)
            return

        if event.event_type == "survey":
            rows = event.payload
            if self._database_writer is not None and rows:
                await self._database_writer.write_surveys(rows)
            return

        if event.event_type == "global_prompt":
            prompt_info = event.payload
            if self._database_writer is not None:
                await self._database_writer.write_global_prompt(prompt_info)
            return

        if event.event_type == "exp_info":
            exp_info = event.payload
            if self._database_writer is not None:
                await self._database_writer.update_exp_info(exp_info)
            if self._db_actor is not None:
                self._db_actor.insert_experiment_info_record.remote(
                    {
                        "tenant_id": exp_info.tenant_id,
                        "id": exp_info.id,
                        "name": exp_info.name,
                        "num_day": exp_info.num_day,
                        "status": exp_info.status,
                        "cur_day": exp_info.cur_day,
                        "cur_t": exp_info.cur_t,
                        "config": exp_info.config,
                        "error": exp_info.error,
                        "input_tokens": exp_info.input_tokens,
                        "output_tokens": exp_info.output_tokens,
                        "created_at": exp_info.created_at,
                        "updated_at": exp_info.updated_at,
                    }
                )
            return

        if event.event_type == "clickhouse_status":
            if self._db_actor is None:
                return
            record = event.payload
            self._db_actor.insert_step_agent_status_record.remote(
                agent_id=record["agent_id"],
                lng=record["lng"] or 0.0,
                lat=record["lat"] or 0.0,
                parent_id=record["parent_id"] or -1,
                action=record["action"] or "",
                status=record["status"],
                timestamp=record["timestamp"],
            )
            return

        if event.event_type == "profile":
            if self._db_actor is not None:
                self._db_actor.insert_agent_profile_batch.remote(event.payload)
            return

        if event.event_type == "metric":
            if self._db_actor is not None and event.payload:
                self._db_actor.insert_metric_batch.remote(event.payload)
            return

        if event.event_type == "task_result":
            if self._db_actor is not None and event.payload:
                self._db_actor.insert_task_result_batch.remote(event.payload)
            return

        if event.event_type == "kv_snapshot":
            if self._db_actor is not None:
                self._db_actor.insert_kv_snapshot_batch.remote(event.payload)
            return

        if event.event_type == "stream_snapshot":
            if self._db_actor is not None:
                self._db_actor.insert_stream_snapshot_batch.remote(event.payload)
            return

        if event.event_type == "spatial_snapshot":
            if self._db_actor is not None:
                self._db_actor.insert_spatial_snapshot_batch.remote(event.payload)
            return

        if event.event_type == "message_snapshot":
            if self._db_actor is not None:
                self._db_actor.insert_pending_messages_snapshot.remote(event.payload)
            return

        if event.event_type == "flush":
            if self._db_actor is not None:
                try:
                    await self._db_actor.flush_all_batches.remote()
                except Exception as e:
                    get_logger().warning(f"ClickHouse flush_all_batches failed: {e}")

            await self._write_recorder_counters(event.step)
            if event.future is not None and not event.future.done():
                event.future.set_result(None)
            return

        if event.event_type == "stop":
            if event.future is not None and not event.future.done():
                event.future.set_result(None)
            raise StopAsyncIteration

        raise ValueError(f"Unknown DataRecorder event type: {event.event_type}")

    async def _process_queue(self) -> None:
        while True:
            event = await self._queue.get()
            try:
                max_attempts = 2
                for attempt in range(1, max_attempts + 1):
                    try:
                        await self._process_event_once(event)
                        self.processed_events += 1
                        break
                    except StopAsyncIteration:
                        self.processed_events += 1
                        return
                    except Exception as e:
                        if attempt < max_attempts:
                            self.retried_events += 1
                            get_logger().warning(
                                f"DataRecorder event {event.event_type} failed on attempt {attempt}, retrying: {e}"
                            )
                            continue

                        self.failed_events += 1
                        get_logger().error(
                            f"DataRecorder event {event.event_type} failed after retries: {e}"
                        )
                        if event.future is not None and not event.future.done():
                            event.future.set_exception(e)
            finally:
                self._queue.task_done()
