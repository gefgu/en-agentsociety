import argparse
import asyncio
import logging
import sys
from pathlib import Path
import os
import uuid

# Must be set before importing ray.
os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"

import ray
from testcontainers.clickhouse import ClickHouseContainer

from agentsociety.cityagent import default  # type: ignore
from agentsociety.configs import Config  # type: ignore
from agentsociety.configs.utils import load_config_from_file  # type: ignore
from agentsociety.simulation import AgentSociety  # type: ignore

# DEFAULT_CONFIG = Path(__file__).parent / "configs/002_run_e2e_with_clickhouse.yaml"
DEFAULT_CONFIG = Path(__file__).parent / "configs/003_resume_single_agent_with_modal.yaml"

CLICKHOUSE_IMAGE = "clickhouse/clickhouse-server:latest"
CLICKHOUSE_USERNAME = "test"
CLICKHOUSE_PASSWORD = "test"
CLICKHOUSE_DATABASE = "testing"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AgentSociety ClickHouse end-to-end resume test"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--crash-after-seconds",
        type=int,
        default=300, # 5 minutes default
        help="How many seconds to run before simulating a crash (default: 300).",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace, host: str, port: int, exp_id: str) -> Config:
    """Helper to generate a fresh config for each run."""
    config: Config = load_config_from_file(str(args.config), Config)
    config = default(config)

    config.env.exp_id = exp_id
    config.env.monitoring_enabled = False
    config.env.clickhouse.host = host
    config.env.clickhouse.port = port
    config.env.clickhouse.username = CLICKHOUSE_USERNAME
    config.env.clickhouse.password = CLICKHOUSE_PASSWORD
    config.env.clickhouse.database = CLICKHOUSE_DATABASE
    
    return config


async def run(config: Config, timeout: int | None = None) -> None:
    society = AgentSociety.create(config)
    try:
        await society.init()
        if timeout:
            logging.info(f"Starting run. Simulating a crash in {timeout} seconds...")
            # wait_for aborts the task and throws a TimeoutError when time expires
            await asyncio.wait_for(society.run(), timeout=timeout)
        else:
            logging.info("Starting run normally (Resume mode)...")
            await society.run()
            
        logging.info("Simulation completed normally.")
    except (TimeoutError, asyncio.TimeoutError):
        logging.warning(f"--- SIMULATED CRASH: Simulation aborted after {timeout} seconds ---")
        # Depending on how hard you want the crash to be, you might skip society.close() here. 
        # But to avoid lingering asyncio tasks/Ray actors blocking the second run, a close is usually safe.
    finally:
        await society.close()


def main() -> None:
    args = parse_args()
    exp_id = str(uuid.uuid4())

    if not args.config.exists():
        print(f"ERROR: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Start the throwaway ClickHouse container.
    with ClickHouseContainer(
        image=CLICKHOUSE_IMAGE,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        dbname=CLICKHOUSE_DATABASE,
    ) as clickhouse:
        host = clickhouse.get_container_host_ip()
        port = int(clickhouse.get_exposed_port(8123))

        logging.info(f"ClickHouse container ready at {host}:{port}")

        # ==========================================
        # RUN 1: The Initial (Crashing) Run
        # ==========================================
        logging.info("=== INITIATING RUN 1 (WILL CRASH) ===")
        config_run1 = build_config(args, host, port, exp_id)
        ray.init()
        try:
            asyncio.run(run(config_run1, timeout=args.crash_after_seconds))
        except Exception as e:
            logging.exception(f"Run 1 encountered an unexpected error: {e}")
        finally:
            ray.shutdown()

        # Brief pause to let sockets/ports settle before Ray restarts
        import time
        time.sleep(3)

        # ==========================================
        # RUN 2: The Resume Run
        # ==========================================
        logging.info("=== INITIATING RUN 2 (RESUME TEST) ===")
        # Note: If your framework requires a specific flag in the config to trigger "resume" 
        # (e.g. `config.resume = True`), make sure to set it inside `build_config` or right here.
        config_run2 = build_config(args, host, port, exp_id)
        
        ray.init()
        try:
            # Running without a timeout so it runs to completion
            asyncio.run(run(config_run2, timeout=None))
            logging.info("E2E ClickHouse RESUME test PASSED — simulation completed without crashing.")
        except Exception as e:
            logging.exception(f"E2E ClickHouse RESUME test FAILED: {e}")
            sys.exit(1)
        finally:
            ray.shutdown()


if __name__ == "__main__":
    main()