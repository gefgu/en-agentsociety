import argparse
import asyncio
import logging
from pathlib import Path
import uuid
from typing import Any

from clickhouse_connect.driver.client import Client  # type: ignore

from agentsociety.configs import Config  # type: ignore
from agentsociety.simulation import AgentSociety  # type: ignore

from utils import (
    build_clickhouse_config,
    create_clickhouse_client,
    ensure_config_exists,
    run_society,
    run_with_ray,
    start_clickhouse_container,
)


DEFAULT_CONFIG = Path(__file__).parent / "configs/003_resume_10_agents_local.yaml"

RESUME_TIMEOUT_SECONDS = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AgentSociety ClickHouse lane_position resume end-to-end test"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--lane-check-interval-seconds",
        type=float,
        default=5.0,
        help="How often to query ClickHouse for lane_position detection in run 1 (default: 5.0).",
    )
    parser.add_argument(
        "--wait-for-lane-timeout-seconds",
        type=int,
        default=300,
        help=(
            "Maximum wait time for lane_position detection in run 1 before failing "
            "(default: 300)."
        ),
    )
    parser.add_argument(
        "--min-steps-before-crash",
        type=int,
        default=2,
        help=(
            "Minimum simulation step before allowing a crash trigger "
            "(default: 2)."
        ),
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace, host: str, port: int, exp_id: str) -> Config:
    return build_clickhouse_config(args.config, host, port, exp_id=exp_id)


def lane_position_detected(client: Client, exp_id: str, min_steps: int) -> bool:
    max_snapshot_step = client.query_np(
        """
    SELECT MAX(simulation_step)
    FROM agent_kv_snapshot
    WHERE exp_id = {exp_id:String}
    """,
        parameters={"exp_id": exp_id},
    )[0][0]

    if max_snapshot_step is None or max_snapshot_step < min_steps:
        logging.debug(
            f"Not checking for lane_position yet since max snapshot step {max_snapshot_step} "
            f"is less than required minimum {min_steps}."
        )
        return False

    lane_count = client.query_np(
        """
    SELECT count()
    FROM agent_kv_snapshot
    WHERE exp_id = {exp_id:String}
      AND simulation_step = {snapshot_step:Int32}
      AND key = 'position'
      AND positionCaseInsensitive(value_json, '"lane_position"') > 0
    """,
        parameters={"exp_id": exp_id, "snapshot_step": int(max_snapshot_step)},
    )[0][0]

    if lane_count > 0:
        logging.info(
            f"Detected lane_position for {lane_count} agent position snapshots at step {max_snapshot_step}."
        )
        return True

    return False


async def run_until_lane_position_detected(
    config: Config,
    client: Client,
    exp_id: str,
    poll_interval_seconds: float,
    wait_timeout_seconds: int,
    min_steps_before_crash: int,
) -> None:
    society = AgentSociety.create(config)
    run_task: asyncio.Task[Any] | None = None
    try:
        await society.init()
        logging.info("Starting run 1. Waiting for lane_position to appear in ClickHouse snapshots...")
        run_task = asyncio.create_task(society.run())

        loop = asyncio.get_running_loop()
        start = loop.time()
        while True:
            if run_task.done():
                await run_task
                raise RuntimeError(
                    "Simulation ended before lane_position was detected; cannot validate resume from in-lane state."
                )

            elapsed = loop.time() - start
            if elapsed > wait_timeout_seconds:
                raise TimeoutError(
                    "Timed out waiting for lane_position in ClickHouse during run 1."
                )

            try:
                if lane_position_detected(client, exp_id, min_steps_before_crash):
                    logging.info("lane_position detected in snapshots. Simulating crash now.")
                    run_task.cancel()
                    try:
                        await run_task
                    except asyncio.CancelledError:
                        pass
                    break
            except Exception as query_error:
                # Tables may not exist yet in early startup; keep polling.
                logging.debug(f"lane_position query not ready yet: {query_error}")

            await asyncio.sleep(poll_interval_seconds)
    finally:
        await society.close()


def main() -> None:
    args = parse_args()
    exp_id = str(uuid.uuid4())

    ensure_config_exists(args.config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    with start_clickhouse_container() as (host, port):
        clickhouse_client = create_clickhouse_client(host, port)

        try:
            # ==========================================
            # RUN 1: The Initial (Crashing) Run
            # ==========================================
            logging.info("=== INITIATING RUN 1 (WILL CRASH ON lane_position) ===")
            config_run1 = build_config(args, host, port, exp_id)
            try:
                run_with_ray(
                    run_until_lane_position_detected(
                        config=config_run1,
                        client=clickhouse_client,
                        exp_id=exp_id,
                        poll_interval_seconds=args.lane_check_interval_seconds,
                        wait_timeout_seconds=args.wait_for_lane_timeout_seconds,
                        min_steps_before_crash=args.min_steps_before_crash,
                    )
                )
                logging.info("Run 1 simulated crash after lane_position detection completed.")
            except Exception as e:
                logging.exception(f"Run 1 encountered an unexpected error: {e}")
                raise SystemExit(1) from e

            # Brief pause to let sockets/ports settle before Ray restarts
            import time
            time.sleep(10)

            # ==========================================
            # RUN 2: The Resume Run
            # ==========================================
            logging.info("=== INITIATING RUN 2 (RESUME TEST) ===")
            config_run2 = build_config(args, host, port, exp_id)

            try:
                # Resume must finish within a bounded window.
                run_with_ray(
                    run_society(
                        config_run2,
                        timeout=RESUME_TIMEOUT_SECONDS,
                        raise_on_timeout=True,
                    )
                )
                logging.info("E2E ClickHouse lane_position RESUME test PASSED — simulation completed without crashing.")
            except (TimeoutError, asyncio.TimeoutError) as timeout_error:
                logging.exception(
                    "E2E ClickHouse lane_position RESUME test FAILED: resume did not complete within "
                    f"{RESUME_TIMEOUT_SECONDS} seconds."
                )
                raise SystemExit(1) from timeout_error
            except Exception as e:
                logging.exception(f"E2E ClickHouse lane_position RESUME test FAILED: {e}")
                raise SystemExit(1) from e
        finally:
            clickhouse_client.close()


if __name__ == "__main__":
    main()