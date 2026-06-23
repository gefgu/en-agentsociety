
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
import time
import uuid
from pathlib import Path
from typing import Any, List, Optional, TypedDict

from ..logger import get_logger
from .schema import (
	AdjustNeedsRecord,
	AgentKVSnapshotRecord,
	AgentLocationTypeRecord,
	AgentProfileRecord,
	AgentSpatialSnapshotRecord,
	AgentStreamSnapshotRecord,
	AgentTransportTypeRecord,
	BlockDispatcherRecord,
	DatabaseRecordModel,
	ExperimentInfoRecord,
	MetricRecord,
	PendingMessageSnapshotRecord,
	PromptResponseDetailRecord,
	PromptResponseRecord,
	StepAgentStatusRecord,
	TaskResultRecord,
)

TableRecord = dict[str, Any]


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
		metrics_actor: Optional[Any] = None,
		checkpoint_home_dir: Optional[str] = None,
	):
		self.exp_id = exp_id
		self.home_dir = Path(home_dir)
		self.checkpoint_home_dir = Path(checkpoint_home_dir) if checkpoint_home_dir else self.home_dir
		self.db_path = self.home_dir / db_subdir
		self.db_path.mkdir(parents=True, exist_ok=True)
		self.migrations_dir = Path(__file__).resolve().parent / "migrations"
		self._metrics_actor = metrics_actor

		self.batch_size = batch_size
		self.batch_timeout = batch_timeout

		self.table_schemas: dict[str, type[DatabaseRecordModel]] = {
			"NeedsBlock_adjust_needs": AdjustNeedsRecord,
			"prompt_responses": PromptResponseRecord,
			"prompt_response_details": PromptResponseDetailRecord,
			"agent_location_type": AgentLocationTypeRecord,
			"agent_transport_type": AgentTransportTypeRecord,
			"step_agent_status": StepAgentStatusRecord,
			"block_dispatcher": BlockDispatcherRecord,
			"experiment_info": ExperimentInfoRecord,
			"agent_kv_snapshot": AgentKVSnapshotRecord,
			"agent_stream_snapshot": AgentStreamSnapshotRecord,
			"agent_spatial_snapshot": AgentSpatialSnapshotRecord,
			"pending_messages_snapshot": PendingMessageSnapshotRecord,
			"agent_profile": AgentProfileRecord,
			"metric": MetricRecord,
			"task_result": TaskResultRecord,
		}

		self.table_columns: dict[str, List[str]] = {
			table_name: schema.column_names()
			for table_name, schema in self.table_schemas.items()
		}

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

	@abstractmethod
	def _query_rows(
		self, query: str, parameters: Optional[Any] = None
	) -> list[dict[str, Any]]:
		raise NotImplementedError

	@abstractmethod
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
		"""Return backend-specific SQL and parameters for shared resume logic."""
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
		if column_name == "simulation_step" and column_name not in record:
			return self.simulation_step

		# Check if column exists in the record
		if column_name not in record:
			get_logger().warning(
				f"Missing column '{column_name}' in record. "
				f"Available keys: {list(record.keys())}. "
				f"Record type: {type(record).__name__ if hasattr(record, '__class__') else 'unknown'}. "
				f"Returning None as default."
			)
			return None

		value = record[column_name]
		if value is None:
			get_logger().debug(
				f"Column '{column_name}' has None value in record"
			)
		return value

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

	def _normalize_record(
		self,
		table_name: str,
		record: dict[str, Any],
	) -> Optional[TableRecord]:
		schema = self.table_schemas.get(table_name)
		if schema is None:
			get_logger().error(f"Unknown table '{table_name}'. Cannot normalize record.")
			return None

		normalized: dict[str, Any] = dict(record)
		model_fields = set(schema.model_fields.keys())
		if "exp_id" in model_fields:
			normalized["exp_id"] = self.exp_id
		if "simulation_step" in model_fields and "simulation_step" not in normalized:
			normalized["simulation_step"] = self.simulation_step

		unknown_keys = sorted(set(normalized.keys()) - model_fields)
		if unknown_keys:
			get_logger().warning(
				f"Dropping unknown keys for '{table_name}': {unknown_keys}"
			)
		try:
			normalized_model = schema.model_validate(normalized)
		except Exception as e:
			get_logger().error(
				f"Cannot insert into '{table_name}': record validation failed: {e}"
			)
			return None

		return normalized_model.as_record()

	def insert_record(
		self, table_name: str, record: dict[str, Any] | DatabaseRecordModel
	) -> None:
		if not self._is_connected():
			get_logger().error(
				f"{self.backend_name} backend is not connected. Cannot insert record."
			)
			return

		try:
			record_data = record.as_record() if isinstance(record, DatabaseRecordModel) else record
			normalized_record = self._normalize_record(table_name, record_data)
			if normalized_record is None:
				return
			self._queue_record(table_name, normalized_record)
		except Exception as e:
			get_logger().error(f"Failed to insert record into '{table_name}': {e}")

	def insert_records(
		self,
		table_name: str,
		records: List[dict[str, Any] | DatabaseRecordModel],
	) -> None:
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

	def _run_resume_query(
		self,
		query_name: str,
		*,
		source_exp_id: str,
		source_uuid: str,
		resume_step: Optional[int] = None,
		rollback_depth: Optional[int] = None,
		attempt_step: Optional[int] = None,
	) -> list[dict[str, Any]]:
		query, parameters = self._resume_query(
			query_name=query_name,
			source_exp_id=source_exp_id,
			source_uuid=source_uuid,
			resume_step=resume_step,
			rollback_depth=rollback_depth,
			attempt_step=attempt_step,
		)
		return self._query_rows(query, parameters)

	def fetch_resume_data(
		self,
		source_exp_id: str,
		rollback_depth: int = 10,
		expected_agent_ids: Optional[set[int]] = None,
	) -> Optional[dict[str, Any]]:
		"""Fetch config, latest step, and latest static attributes for a source experiment."""
		resolved_expected_agent_ids = expected_agent_ids or set()
		if not self._is_connected():
			get_logger().error(
				f"{self.backend_name} backend is not connected. Cannot fetch resume data."
			)
			return None

		try:
			source_uuid = str(uuid.UUID(source_exp_id))
		except (ValueError, TypeError):
			get_logger().error(f"Invalid source experiment id: {source_exp_id}")
			return None

		exp_info_rows = self._run_resume_query(
			"latest_experiment_info",
			source_exp_id=source_exp_id,
			source_uuid=source_uuid,
		)
		if not exp_info_rows:
			return None

		latest_exp_info = exp_info_rows[0]

		step_rows = self._run_resume_query(
			"latest_step",
			source_exp_id=source_exp_id,
			source_uuid=source_uuid,
		)
		latest_step_raw = step_rows[0].get("max_step") if step_rows else None
		latest_step = int(latest_step_raw) if latest_step_raw is not None else 0

		kv_snapshots: dict[int, list[dict]] = {}
		stream_snapshots: dict[int, list[dict]] = {}
		spatial_snapshots: dict[int, list[dict]] = {}
		pending_messages: list[dict] = []
		resume_step = -1
		economy_checkpoint_path = ""

		(
			resume_step,
			kv_snapshots,
			stream_snapshots,
			spatial_snapshots,
			pending_messages,
			economy_checkpoint_path,
		) = self._fetch_checkpoint_snapshots(
			source_exp_id=source_exp_id,
			source_uuid=source_uuid,
			rollback_depth=rollback_depth,
			expected_agent_ids=resolved_expected_agent_ids,
		)

		return {
			"source_exp_id": source_exp_id,
			"config": str(latest_exp_info.get("config") or ""),
			"latest_experiment_info": latest_exp_info,
			"latest_step": latest_step,
			"last_mobility_safe_step": resume_step,
			"economy_checkpoint_path": economy_checkpoint_path,
			"kv_snapshots": kv_snapshots,
			"stream_snapshots": stream_snapshots,
			"spatial_snapshots": spatial_snapshots,
			"pending_messages": pending_messages,
		}

	def _fetch_checkpoint_snapshots(
		self,
		source_exp_id: str,
		source_uuid: str,
		rollback_depth: int,
		expected_agent_ids: set[int],
	) -> tuple[int, dict[int, list], dict[int, list], dict[int, list], list[dict], str]:
		"""Fetch KV/stream/spatial/message snapshots, iterating from the latest KV step backward."""
		candidate_rows = self._run_resume_query(
			"candidate_steps",
			source_exp_id=source_exp_id,
			source_uuid=source_uuid,
			rollback_depth=rollback_depth,
		)
		candidate_steps = [
			int(r["simulation_step"])
			for r in candidate_rows
			if r.get("simulation_step") is not None
		]

		first_failure_reason: Optional[str] = None

		for i, attempt_step in enumerate(candidate_steps):
			remaining = len(candidate_steps) - i - 1

			kv_rows = self._run_resume_query(
				"kv_rows",
				source_exp_id=source_exp_id,
				source_uuid=source_uuid,
				attempt_step=attempt_step,
			)

			kv_agent_ids = {int(r["agent_id"]) for r in kv_rows}
			if expected_agent_ids and not expected_agent_ids.issubset(kv_agent_ids):
				missing = expected_agent_ids - kv_agent_ids
				reason = (
					f"KV snapshot at step {attempt_step} is incomplete "
					f"(missing {len(missing)} agents)"
				)
				if first_failure_reason is None:
					first_failure_reason = reason
				get_logger().warning(
					reason
					+ (
						f". Trying older step ({remaining} remaining)."
						if remaining > 0
						else ". No more candidates."
					)
				)
				continue

			econ_path = str(
				self.checkpoint_home_dir
				/ "checkpoints"
				/ source_exp_id
				/ f"econ_step_{attempt_step}.bin"
			)
			if not Path(econ_path).exists():
				reason = f"Economy checkpoint missing on disk at step {attempt_step}: {econ_path}"
				if first_failure_reason is None:
					first_failure_reason = reason
				get_logger().warning(
					reason
					+ (
						f". Trying older step ({remaining} remaining)."
						if remaining > 0
						else ". No more candidates."
					)
				)
				continue

			kv_snapshots: dict[int, list[dict]] = {}
			for row in kv_rows:
				aid = int(row["agent_id"])
				kv_snapshots.setdefault(aid, []).append(
					{"key": row["key"], "value_json": row["value_json"]}
				)

			stream_rows = self._run_resume_query(
				"stream_rows",
				source_exp_id=source_exp_id,
				source_uuid=source_uuid,
				attempt_step=attempt_step,
			)
			stream_snapshots: dict[int, list[dict]] = {}
			for row in stream_rows:
				aid = int(row["agent_id"])
				stream_snapshots.setdefault(aid, []).append(row)

			spatial_rows = self._run_resume_query(
				"spatial_rows",
				source_exp_id=source_exp_id,
				source_uuid=source_uuid,
				attempt_step=attempt_step,
			)
			spatial_snapshots: dict[int, list[dict]] = {}
			for row in spatial_rows:
				aid = int(row["agent_id"])
				spatial_snapshots.setdefault(aid, []).append(row)

			pending_messages = self._run_resume_query(
				"pending_messages",
				source_exp_id=source_exp_id,
				source_uuid=source_uuid,
				attempt_step=attempt_step,
			)

			if i > 0:
				get_logger().warning(
					f"Resumed from rolled-back checkpoint at step {attempt_step} "
					f"(rolled back {i} step(s) from the latest available)"
				)
			get_logger().info(f"Loaded checkpoint snapshots at step {attempt_step}")
			return (
				attempt_step,
				kv_snapshots,
				stream_snapshots,
				spatial_snapshots,
				pending_messages,
				econ_path,
			)

		n = len(candidate_steps)
		detail = f" First error: {first_failure_reason}" if first_failure_reason else ""
		raise RuntimeError(
			f"Resume failed: no valid checkpoint found for experiment '{source_exp_id}'. "
			f"All {n} candidate step(s) were rejected.{detail}"
		)
