import argparse
import logging
from pathlib import Path
import uuid

from en_agentsociety.configs import Config  # type: ignore

from utils import build_clickhouse_config, ensure_config_exists, run_society, run_with_ray, start_clickhouse_container

# DEFAULT_CONFIG = Path(__file__).parent / "configs/002_run_e2e_with_clickhouse.yaml"
DEFAULT_CONFIG = Path(__file__).parent / "configs/003_resume_single_agent_with_modal.yaml"

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
    return build_clickhouse_config(args.config, host, port, exp_id=exp_id)


def main() -> None:
    args = parse_args()
    exp_id = str(uuid.uuid4())

    ensure_config_exists(args.config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    with start_clickhouse_container() as (host, port):

        # ==========================================
        # RUN 1: The Initial (Crashing) Run
        # ==========================================
        logging.info("=== INITIATING RUN 1 (WILL CRASH) ===")
        config_run1 = build_config(args, host, port, exp_id)
        try:
            run_with_ray(run_society(config_run1, timeout=args.crash_after_seconds))
        except Exception as e:
            logging.exception(f"Run 1 encountered an unexpected error: {e}")

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

        try:
            # Running without a timeout so it runs to completion
            run_with_ray(run_society(config_run2, timeout=args.crash_after_seconds))
            logging.info("E2E ClickHouse RESUME test PASSED — simulation completed without crashing.")
        except Exception as e:
            logging.exception(f"E2E ClickHouse RESUME test FAILED: {e}")
            raise SystemExit(1) from e


if __name__ == "__main__":
    main()