import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pytest

from en_agentsociety.database.base_database import BaseSimulationDatabase, TableRecord
from en_agentsociety.simulation.checkpointmanager import CheckpointManager


class FakeSimulationDatabase(BaseSimulationDatabase):
    def __init__(
        self,
        tmp_path: Path,
        *,
        exp_id: Optional[str] = None,
        checkpoint_home_dir: Optional[Path] = None,
        latest_exp_info: Optional[dict[str, Any]] = None,
        latest_step: int = 0,
        kv_rows_by_step: Optional[dict[int, list[dict[str, Any]]]] = None,
    ) -> None:
        self.latest_exp_info = latest_exp_info
        self.latest_step = latest_step
        self.kv_rows_by_step = kv_rows_by_step or {}
        super().__init__(
            exp_id=exp_id or str(uuid.uuid4()),
            home_dir=str(tmp_path),
            db_subdir="db",
            checkpoint_home_dir=str(checkpoint_home_dir) if checkpoint_home_dir else None,
        )

    @property
    def backend_name(self) -> str:
        return "fake"

    def is_available(self) -> bool:
        return True

    def _is_connected(self) -> bool:
        return True

    def _create_tables(self) -> None:
        return None

    def _flush_records(
        self, table_name: str, records: list[TableRecord], column_names: list[str]
    ) -> None:
        return None

    def _close_connection(self) -> None:
        return None

    def _query_rows(
        self, query: str, parameters: Optional[Any] = None
    ) -> list[dict[str, Any]]:
        params = parameters or {}
        if query == "latest_experiment_info":
            return [self.latest_exp_info] if self.latest_exp_info is not None else []
        if query == "latest_step":
            return [{"max_step": self.latest_step}]
        if query == "kv_rows":
            return self.kv_rows_by_step.get(int(params["attempt_step"]), [])
        if query in {"stream_rows", "spatial_rows", "pending_messages"}:
            return []
        if query == "candidate_steps":
            return [
                {"simulation_step": step}
                for step in sorted(self.kv_rows_by_step, reverse=True)
            ]
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
        return (
            query_name,
            {
                "source_exp_id": source_exp_id,
                "source_uuid": source_uuid,
                "resume_step": resume_step,
                "rollback_depth": rollback_depth,
                "attempt_step": attempt_step,
            },
        )


def _latest_exp_info(exp_id: str) -> dict[str, Any]:
    now = datetime.now()
    return {
        "id": exp_id,
        "tenant_id": "",
        "name": "test",
        "num_day": 1,
        "status": 1,
        "cur_day": 0,
        "cur_t": 0.0,
        "config": "{}",
        "error": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "created_at": now,
        "updated_at": now,
    }


def test_metric_and_task_result_tables_normalize(tmp_path: Path) -> None:
    db = FakeSimulationDatabase(tmp_path, exp_id=str(uuid.uuid4()))

    metric = db._normalize_record(
        "metric",
        {"key": "step.duration", "value": 1.25, "step": 7},
    )
    assert metric is not None
    assert metric["exp_id"] == db.exp_id
    assert metric["key"] == "step.duration"
    assert metric["value"] == 1.25
    assert metric["step"] == 7

    task_result = db._normalize_record(
        "task_result",
        {
            "agent_id": 3,
            "context": "ctx",
            "ground_truth": "truth",
            "result": "ok",
        },
    )
    assert task_result is not None
    assert task_result["exp_id"] == db.exp_id
    assert task_result["agent_id"] == 3

    assert db._normalize_record("unknown_table", {"x": 1}) is None


def test_resume_fallback_uses_disk_checkpoint_with_matching_kv_snapshot(
    tmp_path: Path,
) -> None:
    exp_id = str(uuid.uuid4())
    checkpoint_dir = tmp_path / "checkpoints" / exp_id
    checkpoint_dir.mkdir(parents=True)
    (checkpoint_dir / "econ_step_445.bin").write_bytes(b"economy")

    db = FakeSimulationDatabase(
        tmp_path,
        exp_id=exp_id,
        latest_exp_info=_latest_exp_info(exp_id),
        latest_step=445,
        kv_rows_by_step={
            445: [{"agent_id": 1, "key": "position", "value_json": "{}"}],
        },
    )

    resume_data = db.fetch_resume_data(exp_id)

    assert resume_data is not None
    assert resume_data["last_mobility_safe_step"] == 445
    assert resume_data["economy_checkpoint_path"] == str(
        tmp_path / "checkpoints" / exp_id / "econ_step_445.bin"
    )
    assert resume_data["kv_snapshots"] == {
        1: [{"key": "position", "value_json": "{}"}]
    }


def test_resume_uses_checkpoint_home_dir_not_database_dir(
    tmp_path: Path,
) -> None:
    """Checkpoints are found in checkpoint_home_dir even when it differs from the DB home_dir."""
    exp_id = str(uuid.uuid4())
    db_dir = tmp_path / "db"
    checkpoint_dir_root = tmp_path / "home"
    checkpoint_dir = checkpoint_dir_root / "checkpoints" / exp_id
    checkpoint_dir.mkdir(parents=True)
    (checkpoint_dir / "econ_step_445.bin").write_bytes(b"economy")

    db = FakeSimulationDatabase(
        db_dir,
        exp_id=exp_id,
        checkpoint_home_dir=checkpoint_dir_root,
        latest_exp_info=_latest_exp_info(exp_id),
        latest_step=445,
        kv_rows_by_step={
            445: [{"agent_id": 1, "key": "position", "value_json": "{}"}],
        },
    )

    resume_data = db.fetch_resume_data(exp_id)

    assert resume_data is not None
    assert resume_data["last_mobility_safe_step"] == 445
    assert resume_data["economy_checkpoint_path"] == str(
        checkpoint_dir_root / "checkpoints" / exp_id / "econ_step_445.bin"
    )


def test_resume_rolls_back_when_latest_economy_file_missing(
    tmp_path: Path,
) -> None:
    """If the newest KV step has no economy file on disk, roll back to the previous step."""
    exp_id = str(uuid.uuid4())
    checkpoint_dir = tmp_path / "checkpoints" / exp_id
    checkpoint_dir.mkdir(parents=True)
    # Only step 444 has an economy file; step 445 does not.
    (checkpoint_dir / "econ_step_444.bin").write_bytes(b"economy")

    db = FakeSimulationDatabase(
        tmp_path,
        exp_id=exp_id,
        latest_exp_info=_latest_exp_info(exp_id),
        latest_step=445,
        kv_rows_by_step={
            445: [{"agent_id": 1, "key": "position", "value_json": "{}"}],
            444: [{"agent_id": 1, "key": "position", "value_json": "{}"}],
        },
    )

    resume_data = db.fetch_resume_data(exp_id)

    assert resume_data is not None
    assert resume_data["last_mobility_safe_step"] == 444
    assert resume_data["economy_checkpoint_path"] == str(
        tmp_path / "checkpoints" / exp_id / "econ_step_444.bin"
    )


def test_resume_fails_when_no_kv_snapshots_exist(
    tmp_path: Path,
) -> None:
    """If there are no KV snapshots at all, resume raises RuntimeError."""
    exp_id = str(uuid.uuid4())
    checkpoint_dir = tmp_path / "checkpoints" / exp_id
    checkpoint_dir.mkdir(parents=True)
    (checkpoint_dir / "econ_step_445.bin").write_bytes(b"economy")

    db = FakeSimulationDatabase(
        tmp_path,
        exp_id=exp_id,
        latest_exp_info=_latest_exp_info(exp_id),
        latest_step=445,
        # No kv_rows_by_step → candidate_steps returns nothing
    )

    with pytest.raises(RuntimeError, match="no valid checkpoint found"):
        db.fetch_resume_data(exp_id)


class FakeDbActor:
    def __init__(self, call_log: list[str]) -> None:
        self.flush_all_batches = _RemoteCall(call_log, "db_flush")


class _RemoteCall:
    def __init__(self, call_log: list[str], name: str) -> None:
        self.call_log = call_log
        self.name = name

    async def remote(self, **kwargs: Any) -> None:
        self.call_log.append(self.name)


class FakeDataRecorder:
    def __init__(self, call_log: list[str]) -> None:
        self.call_log = call_log

    async def enqueue_kv_snapshot(self, records: list[dict[str, Any]]) -> None:
        self.call_log.append("enqueue_kv")

    async def enqueue_stream_snapshot(self, records: list[dict[str, Any]]) -> None:
        self.call_log.append("enqueue_stream")

    async def enqueue_spatial_snapshot(self, records: list[dict[str, Any]]) -> None:
        self.call_log.append("enqueue_spatial")

    async def enqueue_message_snapshot(self, records: list[dict[str, Any]]) -> None:
        self.call_log.append("enqueue_message")

    async def flush(self, step: Optional[int] = None) -> None:
        self.call_log.append("recorder_flush")


class FakeEconomyClient:
    def __init__(self, call_log: list[str]) -> None:
        self.call_log = call_log

    async def save(self, path: str) -> None:
        self.call_log.append("economy_save")


class FakeEnvironment:
    def __init__(self, call_log: list[str]) -> None:
        self.economy_client = FakeEconomyClient(call_log)


class FakeMemory:
    async def create_snapshot_records(
        self,
        exp_id: str,
        simulation_step: int,
        agent_id: int,
        day: int,
        t: int,
    ) -> dict[str, Any]:
        return {
            "kv": [
                {
                    "exp_id": exp_id,
                    "simulation_step": simulation_step,
                    "agent_id": agent_id,
                    "key": "position",
                    "value_json": "{}",
                }
            ],
            "stream": [],
            "spatial": [],
            "status": {},
        }


class FakeAgent:
    id = 1
    memory = FakeMemory()


class FakeAgentManager:
    agents = {1: FakeAgent()}


class FakeMessager:
    _pending_messages: list[Any] = []


@pytest.mark.asyncio
async def test_checkpoint_save_writes_economy_file_and_enqueues_kv(
    tmp_path: Path,
) -> None:
    """save_checkpoint enqueues KV snapshots then saves the economy file to disk."""
    calls: list[str] = []
    manager = CheckpointManager(
        exp_id=str(uuid.uuid4()),
        home_dir=str(tmp_path),
        start_tick=0,
    )

    await manager.save_checkpoint(
        day=0,
        t=0,
        total_steps=445,
        agent_manager=FakeAgentManager(),
        messager=FakeMessager(),
        data_recorder=FakeDataRecorder(calls),
        db_actor=FakeDbActor(calls),
        environment=FakeEnvironment(calls),
    )

    assert calls == [
        "enqueue_kv",
        "economy_save",
    ]
