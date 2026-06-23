"""
End-to-end simulation test.

Runs a single SocietyAgent for 10 steps (600 ticks each) and exits 0 if no
exception is raised, 1 otherwise.

Usage:
    python tests/e2e/run_e2e.py
    python tests/e2e/run_e2e.py --config /path/to/my_config.yaml
"""

import argparse
import logging
from pathlib import Path

from en_agentsociety.simulation import AgentSociety  # type: ignore

from utils import ensure_config_exists, load_default_config, run_with_ray

DEFAULT_CONFIG = Path(__file__).parent / "configs/001_run_simplest_e2e.yaml"

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
    config = load_default_config(config_path)

    society = AgentSociety.create(config)
    try:
        await society.init()
        await society.run()
        logging.info("E2E test PASSED — simulation completed without exceptions.")
    finally:
        await society.close()


def main() -> None:
    args = parse_args()

    ensure_config_exists(args.config)

    try:
        run_with_ray(run(args.config))
    except Exception as e:
        logging.exception(f"E2E test FAILED: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
