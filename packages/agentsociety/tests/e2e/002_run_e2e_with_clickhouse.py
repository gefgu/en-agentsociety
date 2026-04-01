import argparse
import logging
from pathlib import Path

from utils import build_clickhouse_config, ensure_config_exists, run_society, run_with_ray, start_clickhouse_container

DEFAULT_CONFIG = Path(__file__).parent / "configs/002_run_e2e_with_clickhouse.yaml"


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

def main() -> None:
    args = parse_args()

    ensure_config_exists(args.config)

    logging.basicConfig(level=logging.INFO)

    with start_clickhouse_container() as (host, port):
        config = build_clickhouse_config(args.config, host, port)
        try:
            run_with_ray(run_society(config))
            logging.info(
                "E2E ClickHouse test PASSED — simulation completed without exceptions."
            )
        except Exception as e:
            logging.exception(f"E2E ClickHouse test FAILED: {e}")
            raise SystemExit(1) from e


if __name__ == "__main__":
    main()