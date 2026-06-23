"""
Test: SQLite corruption detection, recovery, and retry in DatabaseWriter.

Verifies that when sqlite.db is replaced with garbage mid-simulation:
  1. The corrupt file is renamed to a timestamped backup.
  2. A fresh database is created automatically.
  3. The write that triggered corruption is retried and succeeds.
  4. Subsequent writes also succeed.
  5. No exception propagates out of write_dialogs.
"""
import asyncio
import logging
import sys
import uuid
from datetime import datetime, UTC
from pathlib import Path
import tempfile

# Adjust sys.path so this script can import en_agentsociety when run from tests/e2e/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from en_agentsociety.storage.database import DatabaseConfig, DatabaseWriter  # type: ignore
from en_agentsociety.storage.type import StorageDialog, StorageDialogType  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _make_dialog(agent_id: int, seq: int) -> StorageDialog:
    return StorageDialog(
        id=agent_id * 1000 + seq,
        day=1,
        t=float(seq),
        type=int(StorageDialogType.Thought),
        speaker="",
        content=f"dialog {seq}",
        created_at=datetime.now(),
    )


async def run_test(tmp_dir: Path) -> None:
    config = DatabaseConfig(db_type="sqlite")
    exp_id = str(uuid.uuid4())
    writer = DatabaseWriter(
        tenant_id="test_tenant",
        exp_id=exp_id,
        config=config,
        home_dir=str(tmp_dir),
    )
    await writer.init()

    sqlite_path = tmp_dir / "sqlite" / f"{exp_id}.db"
    assert sqlite_path.exists(), f"{sqlite_path.name} not created by init()"

    # Write some rows successfully.
    await writer.write_dialogs([_make_dialog(1, i) for i in range(5)])
    logging.info("Initial write succeeded.")

    # Corrupt the database file.
    sqlite_path.write_bytes(b"THIS IS NOT A SQLITE DATABASE FILE")
    # Flush the connection pool so the next write opens a fresh connection to the
    # corrupt file rather than reusing the existing (still-valid) pooled connection.
    await writer._engine.dispose()
    logging.info(f"Corrupted {sqlite_path.name} and cleared connection pool.")

    # This write should trigger detection, recovery, and retry — no exception.
    await writer.write_dialogs([_make_dialog(2, i) for i in range(5)])
    logging.info("Post-corruption write completed without exception.")

    # A backup of the corrupt file should exist in the same directory.
    sqlite_dir = tmp_dir / "sqlite"
    backups = list(sqlite_dir.glob(f"{exp_id}.db.corrupt.*"))
    assert backups, f"Expected a .corrupt.* backup file in {sqlite_dir} but none found."
    logging.info(f"Corrupt file backed up as: {backups[0].name}")

    # The database file should be recreated at the same path after recovery.
    assert sqlite_path.exists(), f"{sqlite_path.name} was not recreated after recovery."

    # Subsequent writes must also succeed.
    await writer.write_dialogs([_make_dialog(3, i) for i in range(3)])
    logging.info("Subsequent write after recovery succeeded.")

    await writer._engine.dispose()
    logging.info("TEST PASSED.")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            asyncio.run(run_test(Path(tmp)))
        except Exception as e:
            logging.exception(f"TEST FAILED: {e}")
            raise SystemExit(1) from e


if __name__ == "__main__":
    main()
