

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
import time
import uuid
from pathlib import Path
from typing import Any, List, Optional, TypedDict, Union, cast

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


class BaseSimulationDatabase(ABC):
	"""Shared logic for simulation telemetry backends.

	Subclasses provide transport/storage-specific behavior via abstract methods.
	"""

	def __init__(
		self,
		exp_id: str,
		home_dir: str,
		db_subdir: str,
		batch_size: int = 128,
		batch_timeout: float = 30.0,
		metrics_actor: Optional[ray.actor.ActorHandle[PrometheusActor]] = None,
	):
		self.exp_id = exp_id
		self.home_dir = Path(home_dir)
		self.db_path = self.home_dir / db_subdir
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
			"agent_kv_snapshot": AgentKVSnapshotRecord,
			"agent_stream_snapshot": AgentStreamSnapshotRecord,
			"agent_spatial_snapshot": AgentSpatialSnapshotRecord,
			"pending_messages_snapshot": PendingMessageSnapshotRecord,
		}

		self.table_columns: dict[str, List[str]] = {
			table_name: list(schema.__annotations__.keys())
			for table_name, schema in self.table_schemas.items()
		}
		# This column is persisted in both backends but inferred from database state.
		self.table_columns["NeedsBlock_adjust_needs"].insert(1, "simulation_step")

		self.table_batches: dict[str, TableBatchState] = {
			table_name: {
				"batch": deque(),
				"last_flush_time": time.time(),
			}
			for table_name in self.table_columns
		}

		self.simulation_step = -1

	@property
	@abstractmethod
	def backend_name(self) -> str:
		raise NotImplementedError

	@abstractmethod
	def is_available(self) -> bool:
		raise NotImplementedError

	@abstractmethod
	def _is_connected(self) -> bool:
		raise NotImplementedError

	@abstractmethod
	def _create_tables(self) -> None:
		raise NotImplementedError

	@abstractmethod
	def _flush_records(
		self, table_name: str, records: list[TableRecord], column_names: list[str]
	) -> None:
		raise NotImplementedError

	@abstractmethod
	def _close_connection(self) -> None:
		raise NotImplementedError

	def _is_unknown_table_error(self, error: Exception) -> bool:
		return False

	def _recover_missing_table_and_retry_flush(
		self,
		table_name: str,
		records: list[TableRecord],
		column_names: list[str],
	) -> bool:
		return False

	def _record_metric(self, table_name: str, size: int) -> None:
		if self._metrics_actor is None:
			return
		self._metrics_actor.record_table_records.remote(table_name, size)

	def set_simulation_step(self, step: int) -> None:
		self.simulation_step = step

	def _record_value(self, record: TableRecord, column_name: str) -> Any:
		raw_record = cast(dict[str, Any], record)
		if column_name == "simulation_step" and "simulation_step" not in raw_record:
			return self.simulation_step
		return raw_record[column_name]

	def _flush_table_batch(self, table_name: str) -> None:
		if not self._is_connected():
			get_logger().error(
				f"{self.backend_name} backend is not connected. Cannot flush batch."
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

		records = list(table_state["batch"])
		try:
			self._flush_records(table_name, records, column_names)
			table_state["batch"].clear()
			table_state["last_flush_time"] = time.time()
			self._record_metric(table_name, len(records))
		except Exception as e:
			if self._is_unknown_table_error(e):
				get_logger().warning(
					f"Table '{table_name}' is missing. Re-applying migrations and retrying batch flush once."
				)
				if self._recover_missing_table_and_retry_flush(
					table_name=table_name,
					records=records,
					column_names=column_names,
				):
					table_state["batch"].clear()
					table_state["last_flush_time"] = time.time()
					self._record_metric(table_name, len(records))
					get_logger().info(
						f"Recovered missing table '{table_name}' and flushed pending batch."
					)
					return
			get_logger().error(
				f"Failed to flush '{table_name}' batch to {self.backend_name}: {e}"
			)

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

	@staticmethod
	def _normalize_timestamp(value: Any) -> datetime:
		if isinstance(value, (int, float)):
			return datetime.fromtimestamp(value)
		if isinstance(value, datetime):
			return value
		return datetime.now()

	@staticmethod
	def _normalize_agent_id(value: Any) -> int:
		if isinstance(value, int):
			return value
		try:
			return int(value)
		except (TypeError, ValueError):
			return -1

	def _normalize_record(
		self,
		table_name: str,
		record: dict[str, Any],
	) -> Optional[TableRecord]:
		schema = self.table_schemas.get(table_name)
		column_names = self.table_columns.get(table_name)
		if schema is None or column_names is None:
			get_logger().error(f"Unknown table '{table_name}'. Cannot normalize record.")
			return None

		normalized = dict(record)

		if "exp_id" in column_names:
			normalized["exp_id"] = self.exp_id
		if "simulation_step" in column_names and "simulation_step" not in normalized:
			normalized["simulation_step"] = self.simulation_step
		if "timestamp" in column_names:
			normalized["timestamp"] = self._normalize_timestamp(
				normalized.get("timestamp")
			)
		if "agent_id" in column_names:
			normalized["agent_id"] = self._normalize_agent_id(normalized.get("agent_id"))

		if table_name == "experiment_info":
			try:
				normalized["id"] = str(uuid.UUID(str(normalized["id"])))
			except Exception:
				get_logger().error("Invalid experiment_info record id; expected UUID string.")
				return None

			normalized["created_at"] = self._normalize_timestamp(
				normalized.get("created_at")
			)
			normalized["updated_at"] = self._normalize_timestamp(
				normalized.get("updated_at")
			)
			normalized["last_mobility_safe_step"] = normalized.get(
				"last_mobility_safe_step", -1
			)
			normalized["prev_mobility_safe_step"] = normalized.get(
				"prev_mobility_safe_step", -1
			)
			normalized["economy_checkpoint_path"] = normalized.get(
				"economy_checkpoint_path", ""
			)

		required_keys = set(getattr(schema, "__required_keys__", set()))
		missing_required = [key for key in required_keys if key not in normalized]
		if missing_required:
			get_logger().error(
				f"Cannot insert into '{table_name}': missing required keys {missing_required}."
			)
			return None

		unknown_keys = sorted(set(normalized.keys()) - set(column_names))
		if unknown_keys:
			get_logger().warning(
				f"Dropping unknown keys for '{table_name}': {unknown_keys}"
			)

		filtered_record = {
			column_name: normalized[column_name]
			for column_name in column_names
			if column_name in normalized
		}
		missing_columns = [
			column_name
			for column_name in column_names
			if column_name not in filtered_record
		]
		if missing_columns:
			get_logger().error(
				f"Cannot insert into '{table_name}': missing table columns {missing_columns}."
			)
			return None

		return cast(TableRecord, filtered_record)

	def insert_record(self, table_name: str, record: dict[str, Any]) -> None:
		if not self._is_connected():
			get_logger().error(
				f"{self.backend_name} backend is not connected. Cannot insert record."
			)
			return

		try:
			normalized_record = self._normalize_record(table_name, record)
			if normalized_record is None:
				return
			self._queue_record(table_name, normalized_record)
		except Exception as e:
			get_logger().error(f"Failed to insert record into '{table_name}': {e}")

	def insert_records(self, table_name: str, records: List[dict[str, Any]]) -> None:
		if not self._is_connected():
			return

		try:
			for record in records:
				self.insert_record(table_name, record)
		except Exception as e:
			get_logger().error(f"Failed to insert records into '{table_name}': {e}")

	def flush_all_batches(self) -> None:
		for table_name in self.table_batches:
			self._flush_table_batch(table_name)

	def close(self) -> None:
		if self._is_connected():
			self.flush_all_batches()
			self._close_connection()
			get_logger().info(f"{self.backend_name} connection closed.")