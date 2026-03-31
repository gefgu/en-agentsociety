import argparse
import asyncio
import logging
import sys
from pathlib import Path

import os

# Must be set before importing ray.
os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"

import ray
from testcontainers.clickhouse import ClickHouseContainer

from agentsociety.cityagent import default  # type: ignore
from agentsociety.configs import Config  # type: ignore
from agentsociety.configs.utils import load_config_from_file  # type: ignore
from agentsociety.simulation import AgentSociety  # type: ignore

DEFAULT_CONFIG = Path(__file__).parent / "configs/002_run_e2e_with_clickhouse.yaml"

CLICKHOUSE_IMAGE = "clickhouse/clickhouse-server:latest"
CLICKHOUSE_USERNAME = "test"
CLICKHOUSE_PASSWORD = "test"
CLICKHOUSE_DATABASE = "testing"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AgentSociety ClickHouse end-to-end test"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    return parser.parse_args()


async def run(config: Config) -> None:
    society = AgentSociety.create(config)
    try:
        await society.init()
        await society.run()
        logging.info(
            "E2E ClickHouse test PASSED — simulation completed without exceptions."
        )
    finally:
        await society.close()


def main() -> None:
    args = parse_args()

    if not args.config.exists():
        print(f"ERROR: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    # Start the throwaway ClickHouse container. The context manager blocks until
    # the HTTP port 8123 returns "Ok" (ClickHouseContainer._connect wait strategy).
    with ClickHouseContainer(
        image=CLICKHOUSE_IMAGE,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        dbname=CLICKHOUSE_DATABASE,
    ) as clickhouse:
        host = clickhouse.get_container_host_ip()
        port = int(clickhouse.get_exposed_port(8123))

        logging.info(f"ClickHouse container ready at {host}:{port}")

        # Load the YAML config, then overwrite the ClickHouse coordinates so the
        # simulation connects to our throwaway container instead of a real server.
        config: Config = load_config_from_file(str(args.config), Config)
        config = default(config)

        config.env.monitoring_enabled = True
        config.env.clickhouse.host = host
        config.env.clickhouse.port = port
        config.env.clickhouse.username = CLICKHOUSE_USERNAME
        config.env.clickhouse.password = CLICKHOUSE_PASSWORD
        config.env.clickhouse.database = CLICKHOUSE_DATABASE

        ray.init()

        try:
            asyncio.run(run(config))
        except Exception as e:
            logging.exception(f"E2E ClickHouse test FAILED: {e}")
            sys.exit(1)
        finally:
            ray.shutdown()


if __name__ == "__main__":
    main()