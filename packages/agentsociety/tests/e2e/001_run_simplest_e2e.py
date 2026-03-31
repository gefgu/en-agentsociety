"""
End-to-end simulation test.

Runs a single SocietyAgent for 10 steps (600 ticks each) and exits 0 if no
exception is raised, 1 otherwise.

Usage:
    python tests/e2e/run_e2e.py
    python tests/e2e/run_e2e.py --config /path/to/my_config.yaml
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import os

# Must be set before importing ray — the constant is evaluated at import time.
# Disables Ray's automatic uv-run environment replication, which packages the
# working directory (including Docker-owned data/) and fails on permission errors.
os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"

import ray
from agentsociety.cityagent import default  # type: ignore
from agentsociety.configs import Config  # type: ignore
from agentsociety.configs.utils import load_config_from_file  # type: ignore
from agentsociety.simulation import AgentSociety  # type: ignore

DEFAULT_CONFIG = Path(__file__).parent / "001_run_simplest_e2e"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AgentSociety end-to-end test")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    return parser.parse_args()


async def run(config_path: Path) -> None:
    logging.info(f"Loading config from {config_path}")
    config: Config = load_config_from_file(str(config_path), Config)
    config = default(config)

    society = AgentSociety.create(config)
    try:
        await society.init()
        await society.run()
        logging.info("E2E test PASSED — simulation completed without exceptions.")
    finally:
        await society.close()


def main() -> None:
    args = parse_args()

    if not args.config.exists():
        print(f"ERROR: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    ray.init()

    try:
        asyncio.run(run(args.config))
    except Exception as e:
        logging.exception(f"E2E test FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
