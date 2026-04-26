"""
E2E test: Mistral model robustness.

Runs a single SocietyAgent for 10 steps using the Mistral model via vllm.
The first forward() call triggers thought_update() (cross_day() returns True
on first invocation), which is the exact call site of the KeyError: 'thought'
crash. Test passes if no KeyError or other exception is raised.

Usage:
    python tests/e2e/010_mistral_robustness.py
    python tests/e2e/010_mistral_robustness.py --config /path/to/config.yaml
"""

import argparse
import logging
from pathlib import Path

from agentsociety.simulation import AgentSociety  # type: ignore

from utils import ensure_config_exists, load_default_config, run_with_ray

DEFAULT_CONFIG = Path(__file__).parent / "configs/010_mistral_robustness.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mistral model robustness e2e test")
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
        logging.info("E2E test PASSED — Mistral simulation completed without KeyError.")
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
