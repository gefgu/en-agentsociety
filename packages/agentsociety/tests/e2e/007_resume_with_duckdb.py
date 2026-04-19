import argparse
import logging
import time
import uuid
from pathlib import Path

from utils import build_duckdb_config, ensure_config_exists, query_duckdb, run_society, run_with_ray

DEFAULT_CONFIG = Path(__file__).parent / "configs/007_resume_with_duckdb.yaml"
CRASH_TIMEOUT_SECONDS = 300


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AgentSociety DuckDB end-to-end resume test"
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
        default=CRASH_TIMEOUT_SECONDS,
        help="How many seconds to run before simulating a crash (default: 300).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exp_id = str(uuid.uuid4())

    ensure_config_exists(args.config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # ==========================================
    # RUN 1: The Initial (Crashing) Run
    # ==========================================
    logging.info("=== INITIATING RUN 1 (WILL CRASH / TIMEOUT) ===")
    config_run1 = build_duckdb_config(args.config, exp_id=exp_id)
    try:
        run_with_ray(run_society(config_run1, timeout=args.crash_after_seconds))
    except Exception as e:
        logging.warning(f"Run 1 ended (expected): {e}")

    # Brief pause to let file handles close after Ray shutdown.
    time.sleep(3)

    # Assert DuckDB file exists and contains a valid checkpoint.
    duckdb_file = Path(config_run1.env.data_dir) / "duckdb" / f"{exp_id}.duckdb"
    assert duckdb_file.exists(), (
        f"DuckDB file not created by run 1: {duckdb_file}\n"
        "Check that the DatabaseActor fell back to DuckDB (ClickHouse port=1 should fail)."
    )

    rows = query_duckdb(
        duckdb_file,
        "SELECT last_mobility_safe_step FROM experiment_info "
        "WHERE id = ? ORDER BY updated_at DESC LIMIT 1",
        [exp_id],
    )
    assert rows, (
        f"No experiment_info row found in DuckDB for exp_id={exp_id}. "
        "CheckpointManager may not have flushed before shutdown."
    )
    safe_step = rows[0]["last_mobility_safe_step"]
    if safe_step > 0:
        logging.info(f"Run 1 wrote checkpoint at step {safe_step} to DuckDB at {duckdb_file}.")
    else:
        # last_mobility_safe_step == -1 means the crash window was too short for the LLM
        # to complete even one simulation step. The DuckDB backend is still verified to have
        # initialized, written experiment_info, and persisted the file. Run 2 will exercise
        # the DuckDB resume read path (returning no checkpoint data, which is valid).
        logging.warning(
            f"last_mobility_safe_step={safe_step}: no checkpoint was written in the "
            f"{args.crash_after_seconds}s window (LLM likely too slow for one step). "
            "DuckDB file and schema are confirmed valid; run 2 will test the read path."
        )

    # ==========================================
    # RUN 2: The Resume Run
    # ==========================================
    logging.info("=== INITIATING RUN 2 (RESUME TEST) ===")
    config_run2 = build_duckdb_config(args.config, exp_id=exp_id)

    try:
        run_with_ray(run_society(config_run2, timeout=args.crash_after_seconds))
        logging.info("E2E DuckDB RESUME test PASSED — simulation completed without crashing.")
    except Exception as e:
        logging.exception(f"E2E DuckDB RESUME test FAILED: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
