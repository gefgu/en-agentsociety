import argparse
import asyncio
import logging
from pathlib import Path
import uuid
from typing import Any

from clickhouse_connect.driver.client import Client # type: ignore

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
        description="AgentSociety ClickHouse end-to-end resume test"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--movement-check-interval-seconds",
        type=float,
        default=5.0,
        help="How often to query ClickHouse for movement detection in run 1 (default: 5.0).",
    )
    parser.add_argument(
        "--wait-for-movement-timeout-seconds",
        type=int,
        default=300,
        help=(
            "Maximum wait time for movement detection in run 1 before failing "
            "(default: 300)."
        ),
    )
    parser.add_argument(
        "--min-steps-before-crash",
        type=int,
        default=2,
        help=(
            "Minimum number of steps to run before crashing "
            "(default: 2)."
        ),
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace, host: str, port: int, exp_id: str) -> Config:
    return build_clickhouse_config(args.config, host, port, exp_id=exp_id)


def movement_detected(client: Client, exp_id: str, min_steps: int) -> bool:
    max_simulation_step = client.query_np(
        """
    SELECT MAX(simulation_step)
    FROM step_agent_status
    WHERE exp_id = {exp_id:String}
    """,
    parameters={"exp_id": exp_id},
    )[0][0]
    if max_simulation_step is None or max_simulation_step < min_steps:
        logging.debug(
            f"Not checking for movement yet since max simulation step {max_simulation_step} "
            f"is less than the required minimum {min_steps}."
        )
        return False

    query_result = client.query_np(
        """
SELECT EXISTS (
    SELECT 1
    FROM (
        SELECT
            lat,
            lng,
            LAG(lat) OVER (PARTITION BY agent_id ORDER BY simulation_step) AS prev_lat,
            LAG(lng) OVER (PARTITION BY agent_id ORDER BY simulation_step) AS prev_lng
        FROM step_agent_status
        WHERE exp_id = {exp_id:String}
    ) sub
    WHERE (lat != prev_lat OR lng != prev_lng)
) AS any_movement_detected
""",
        parameters={"exp_id": exp_id},
    )
    return bool(query_result[0][0])


async def run_until_movement_detected(
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
        logging.info("Starting run 1. Waiting for movement to appear in ClickHouse...")
        run_task = asyncio.create_task(society.run())

        loop = asyncio.get_running_loop()
        start = loop.time()
        while True:
            if run_task.done():
                await run_task
                raise RuntimeError(
                    "Simulation ended before movement was detected; cannot validate resume from moving state."
                )

            elapsed = loop.time() - start
            if elapsed > wait_timeout_seconds:
                raise TimeoutError(
                    "Timed out waiting for movement in ClickHouse during run 1."
                )

            try:
                if movement_detected(client, exp_id, min_steps_before_crash):
                    logging.info("Movement detected in ClickHouse. Simulating crash now.")
                    run_task.cancel()
                    try:
                        await run_task
                    except asyncio.CancelledError:
                        pass
                    break
            except Exception as query_error:
                # Tables may not exist yet in early startup; keep polling.
                logging.debug(f"Movement query not ready yet: {query_error}")

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
            logging.info("=== INITIATING RUN 1 (WILL CRASH) ===")
            config_run1 = build_config(args, host, port, exp_id)
            try:
                run_with_ray(
                    run_until_movement_detected(
                        config=config_run1,
                        client=clickhouse_client,
                        exp_id=exp_id,
                        poll_interval_seconds=args.movement_check_interval_seconds,
                        wait_timeout_seconds=args.wait_for_movement_timeout_seconds,
                        min_steps_before_crash=args.min_steps_before_crash,
                    )
                )
                logging.info("Run 1 simulated crash after movement detection completed.")
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
            # Note: If your framework requires a specific flag in the config to trigger "resume"
            # (e.g. `config.resume = True`), make sure to set it inside `build_config` or right here.
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
                logging.info("E2E ClickHouse RESUME test PASSED — simulation completed without crashing.")
            except (TimeoutError, asyncio.TimeoutError) as timeout_error:
                logging.exception(
                    "E2E ClickHouse RESUME test FAILED: resume did not complete within "
                    f"{RESUME_TIMEOUT_SECONDS} seconds."
                )
                raise SystemExit(1) from timeout_error
            except Exception as e:
                logging.exception(f"E2E ClickHouse RESUME test FAILED: {e}")
                raise SystemExit(1) from e
        finally:
            clickhouse_client.close()


if __name__ == "__main__":
    main()