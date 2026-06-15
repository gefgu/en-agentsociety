"""End-to-end test for the mobility-metrics comparison report.

Runs a tiny simulation (3 citizens, one 24h day) to DuckDB, then exercises the
webapi mobility pipeline:

    load_experiment_frames (DuckDB) -> build_visits_from_frames
        -> trajdf_from_visits_df -> build_comparison_payload

and asserts that metrics + skmob-vis ECharts options are produced and are
JSON-serialisable. Requires a local vLLM endpoint (see the config).

Usage:
    python 012_mobility_metrics.py
    python 012_mobility_metrics.py --config configs/012_mobility_3agents_1day.yaml
"""

import argparse
import json
import logging
import time
import uuid
from pathlib import Path

import numpy as np

from utils import build_duckdb_config, ensure_config_exists, run_society, run_with_ray

DEFAULT_CONFIG = Path(__file__).parent / "configs/012_mobility_3agents_1day.yaml"
# Upper bound on the run; if the day does not finish in time we still assert on
# whatever data was recorded (the pipeline must work on a partial day too).
RUN_TIMEOUT_SECONDS = 2400


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mobility-metrics e2e test")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-timeout-seconds", type=int, default=RUN_TIMEOUT_SECONDS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_config_exists(args.config)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    exp_id = str(uuid.uuid4())
    config = build_duckdb_config(args.config, exp_id=exp_id)

    logging.info("=== Running 3-agent / 1-day simulation (exp_id=%s) ===", exp_id)
    run_with_ray(run_society(config, timeout=args.run_timeout_seconds, raise_on_timeout=False))
    time.sleep(3)  # let file handles close after Ray shutdown

    duckdb_file = Path(config.env.data_dir) / "duckdb" / f"{exp_id}.duckdb"
    assert duckdb_file.exists(), f"DuckDB file not created: {duckdb_file}"

    # --- exercise the webapi mobility pipeline against the DuckDB backend ---
    from agentsociety.webapi.api.visits import build_visits_from_frames  # type: ignore
    from agentsociety.webapi.datasource import load_experiment_frames  # type: ignore
    from agentsociety.webapi.mobility import (  # type: ignore
        build_comparison_payload,
        trajdf_from_visits_df,
    )

    status_df, location_type_df = load_experiment_frames(exp_id, duckdb_path=str(duckdb_file))
    logging.info(
        "Loaded %d step_agent_status rows, %d agent_location_type rows",
        len(status_df), len(location_type_df),
    )
    assert not status_df.empty, "no step_agent_status rows were recorded"

    visits_df = build_visits_from_frames(status_df, location_type_df)
    assert not visits_df.empty, "no visits extracted from the simulation"
    logging.info("Extracted %d visits", len(visits_df))

    df_a = trajdf_from_visits_df(visits_df)

    # Second source: a spatially jittered copy, so the comparison is non-trivial
    # and both code branches run.
    rng = np.random.default_rng(42)
    df_b = df_a.copy()
    df_b["lat"] = df_b["lat"] + rng.normal(0, 0.002, len(df_b))
    df_b["lng"] = df_b["lng"] + rng.normal(0, 0.002, len(df_b))

    payload = build_comparison_payload(df_a, df_b, "sim", "sim (jitter)")

    # --- assertions ---
    assert payload["labels"] == ["sim", "sim (jitter)"]
    assert isinstance(payload["metrics"], dict)
    assert "wasserstein" in payload["metrics"]
    charts = payload["charts"]
    assert isinstance(charts, dict) and len(charts) >= 1, "no charts produced"
    for key, chart in charts.items():
        assert "option" in chart and isinstance(chart["option"], dict), f"chart {key} missing option"
    # The whole payload must be serialisable for the HTTP response.
    serialized = json.dumps(payload)
    assert len(serialized) > 0

    logging.info("Charts produced: %s", sorted(charts.keys()))
    logging.info("Wasserstein: %s", payload["metrics"]["wasserstein"])
    logging.info("Jensen-Shannon: %s", payload["metrics"]["jensen_shannon"])
    logging.info("CPC: %s", payload["metrics"]["cpc"])
    if payload["warnings"]:
        logging.info("Warnings (skipped charts/metrics): %s", payload["warnings"])

    logging.info("E2E mobility-metrics test PASSED.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        logging.exception("E2E mobility-metrics test FAILED: %s", e)
        raise SystemExit(1) from e
