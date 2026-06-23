import asyncio
import logging
import os
import sys
from contextlib import contextmanager
from collections.abc import Awaitable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

from en_agentsociety.cityagent import default  # type: ignore
from en_agentsociety.configs import Config  # type: ignore
from en_agentsociety.configs.utils import load_config_from_file  # type: ignore
from en_agentsociety.simulation import AgentSociety  # type: ignore

if TYPE_CHECKING:
    from clickhouse_connect.driver.client import Client

# Must be set before importing ray.
# Force override to avoid inheriting a shell value that re-enables uv runtime env packaging.
os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"
# Avoid permission issues while scanning nested gitignored Docker volumes.
os.environ["RAY_RUNTIME_ENV_IGNORE_GITIGNORE"] = "1"

CLICKHOUSE_IMAGE = "clickhouse/clickhouse-server:latest"
CLICKHOUSE_USERNAME = "test"
CLICKHOUSE_PASSWORD = "test"
CLICKHOUSE_DATABASE = "testing"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ensure_config_exists(config_path: Path) -> None:
    if not config_path.exists():
        print(f"ERROR: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)


def load_default_config(config_path: Path) -> Config:
    config: Config = load_config_from_file(str(config_path), Config)
    return default(config)


def apply_clickhouse_overrides(
    config: Config,
    host: str,
    port: int,
    exp_id: str | None = None,
) -> Config:
    config.env.monitoring_enabled = False
    config.env.clickhouse.host = host
    config.env.clickhouse.port = port
    config.env.clickhouse.username = CLICKHOUSE_USERNAME
    config.env.clickhouse.password = CLICKHOUSE_PASSWORD
    config.env.clickhouse.database = CLICKHOUSE_DATABASE
    if exp_id is not None:
        config.env.exp_id = exp_id
    return config


def build_clickhouse_config(
    config_path: Path,
    host: str,
    port: int,
    exp_id: str | None = None,
) -> Config:
    config = load_default_config(config_path)
    return apply_clickhouse_overrides(config, host, port, exp_id=exp_id)


@contextmanager
def start_clickhouse_container() -> Generator[tuple[str, int], None, None]:
    from testcontainers.clickhouse import ClickHouseContainer

    with ClickHouseContainer(
        image=CLICKHOUSE_IMAGE,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        dbname=CLICKHOUSE_DATABASE,
    ) as clickhouse:
        host = clickhouse.get_container_host_ip()
        port = int(clickhouse.get_exposed_port(8123))
        logging.info(f"ClickHouse container ready at {host}:{port}")
        yield host, port


def apply_duckdb_overrides(
    config: Config,
    exp_id: str | None = None,
) -> Config:
    """Force the DatabaseActor to use DuckDB by pointing ClickHouse at an unreachable address.

    Also resolves data_dir to an absolute path so the DuckDB file is written to a
    persistent location instead of Ray's temporary working-directory copy.
    """
    config.env.clickhouse.host = "127.0.0.1"
    config.env.clickhouse.port = 1  # guaranteed unreachable
    config.env.monitoring_enabled = False
    # Ray actors run from a temp copy of working_dir; relative paths won't survive shutdown.
    data_dir = Path(config.env.data_dir)
    if not data_dir.is_absolute():
        config.env.data_dir = str((PROJECT_ROOT / data_dir).resolve())
    if exp_id is not None:
        config.env.exp_id = exp_id
    return config


def build_duckdb_config(
    config_path: Path,
    exp_id: str | None = None,
) -> Config:
    config = load_default_config(config_path)
    return apply_duckdb_overrides(config, exp_id=exp_id)


def query_duckdb(db_file: Path, sql: str, params: list | None = None) -> list[dict]:
    """Open a DuckDB file read-only and return rows as a list of dicts."""
    import duckdb

    conn = duckdb.connect(str(db_file), read_only=True)
    try:
        cursor = conn.execute(sql, params or [])
        rows = cursor.fetchall()
        cols = [d[0] for d in (cursor.description or [])]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def create_clickhouse_client(host: str, port: int) -> "Client":
    import clickhouse_connect

    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE,
    )


async def run_society(
    config: Config,
    timeout: int | None = None,
    raise_on_timeout: bool = False,
) -> None:
    society = AgentSociety.create(config)
    try:
        await society.init()
        if timeout:
            logging.info(f"Starting run with timeout={timeout} seconds...")
            await asyncio.wait_for(society.run(), timeout=timeout)
        else:
            logging.info("Starting run normally...")
            await society.run()
        logging.info("Simulation completed normally.")
    except (TimeoutError, asyncio.TimeoutError):
        logging.warning(f"Simulation aborted after {timeout} seconds.")
        if raise_on_timeout:
            raise
    finally:
        await society.close()


def run_with_ray(coro: Awaitable[Any]) -> None:
    import ray

    runtime_env = {
        # Package project code from repo root instead of tests/e2e cwd and skip large artifacts.
        "working_dir": str(PROJECT_ROOT),
        "excludes": [
            "tests/e2e/data/**",
            "tests/e2e/.venv/**",
            "tests/e2e/*.log",
            "tests/e2e/__pycache__/**",
            "tests/e2e/data",
            "tests/e2e/.venv",
            ".git/**",
        ]
    }

    try:
        ray.init(runtime_env=runtime_env)
    except Exception:
        # If Ray fails before asyncio.run starts, explicitly close coroutine objects
        # so Python does not emit an unawaited coroutine warning.
        close = getattr(coro, "close", None)
        if callable(close):
            close()
        raise

    try:
        asyncio.run(coro)
    finally:
        ray.shutdown()
