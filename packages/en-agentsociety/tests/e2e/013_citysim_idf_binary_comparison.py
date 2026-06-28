"""Report-only e2e comparison for original vs sibling CitySim binaries.

Runs a derived 5-agent / 1-day IDF scenario twice, once with the original
``agentsociety-sim-oss`` binary and once with a sibling implementation built
from source. The resulting DuckDB trajectories are compared with the same
mobility-metrics pipeline used by the Charts UI.

Usage:
    python 013_citysim_idf_binary_comparison.py
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from en_agentsociety.cityagent import default  # type: ignore
from en_agentsociety.configs import Config, WorkflowStepConfig, WorkflowType  # type: ignore
from en_agentsociety.configs.utils import load_config_from_file  # type: ignore

from utils import apply_duckdb_overrides, ensure_config_exists, run_society, run_with_ray

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_IDF_CONFIG = (
    REPO_ROOT / "../cultural_agents/experiments/09_citysim/configs/03_500_idf.yaml"
).resolve()
DEFAULT_SIM_REPO = (REPO_ROOT / "../agentsociety-sim-oss").resolve()
DEFAULT_DATA_ROOT = (REPO_ROOT / "../cultural_agents/agentsociety_data").resolve()
DEFAULT_ORIGINAL_BIN = DEFAULT_DATA_ROOT / "agentsociety-sim-oss"
DEFAULT_REPORT_OUT = (
    Path(tempfile.gettempdir()) / "agentsociety_013_citysim_idf_binary_comparison_report.json"
)
RUN_TIMEOUT_SECONDS = 3600


@dataclass(frozen=True)
class Variant:
    name: str
    label: str
    bin_name: str
    home_dir: Path
    data_dir: Path
    exp_id: str


@dataclass(frozen=True)
class RunResult:
    variant: Variant
    duckdb_file: Path
    status_rows: int
    location_type_rows: int
    visit_rows: int
    trajectory_rows: int
    agent_count: int
    trajectory: Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare IDF CitySim outputs from original and sibling simulator binaries."
    )
    parser.add_argument("--idf-config", type=Path, default=DEFAULT_IDF_CONFIG)
    parser.add_argument("--sim-repo", type=Path, default=DEFAULT_SIM_REPO)
    parser.add_argument("--original-bin", type=Path, default=DEFAULT_ORIGINAL_BIN)
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    parser.add_argument("--run-timeout-seconds", type=int, default=RUN_TIMEOUT_SECONDS)
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Keep the generated working directory after the test completes.",
    )
    return parser.parse_args()


def _require_file(path: Path, label: str) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")


def _require_dir(path: Path, label: str) -> None:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"{label} not found: {path}")


def _copy_executable(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    dst.chmod(dst.stat().st_mode | stat.S_IXUSR)


def build_sibling_binary(sim_repo: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logging.info("Building sibling simulator: go build -o %s .", output_path)
    subprocess.run(
        ["go", "build", "-o", str(output_path), "."],
        cwd=sim_repo,
        check=True,
    )
    output_path.chmod(output_path.stat().st_mode | stat.S_IXUSR)


def make_work_dir(requested: Path | None) -> tuple[Path, bool]:
    if requested is not None:
        requested.mkdir(parents=True, exist_ok=True)
        return requested.resolve(), False
    return Path(tempfile.mkdtemp(prefix="agentsociety-idf-binary-compare-")).resolve(), True


def prepare_variant_dirs(work_dir: Path, original_bin: Path, sim_repo: Path) -> tuple[Variant, Variant]:
    original = Variant(
        name="original",
        label="original agentsociety-sim-oss",
        bin_name="agentsociety-sim-oss_original",
        home_dir=work_dir / "original" / "home",
        data_dir=work_dir / "original" / "data",
        exp_id=str(uuid.uuid4()),
    )
    sibling = Variant(
        name="sibling",
        label="sibling agentsociety-sim-oss",
        bin_name="agentsociety-sim-oss_sibling",
        home_dir=work_dir / "sibling" / "home",
        data_dir=work_dir / "sibling" / "data",
        exp_id=str(uuid.uuid4()),
    )

    _copy_executable(original_bin, original.home_dir / original.bin_name)
    build_sibling_binary(sim_repo, sibling.home_dir / sibling.bin_name)
    return original, sibling


def build_idf_config(config_path: Path, variant: Variant) -> Config:
    data_root = DEFAULT_DATA_ROOT
    config: Config = load_config_from_file(str(config_path), Config)

    config.env.home_dir = str(variant.home_dir)
    config.env.data_dir = str(variant.data_dir)
    config.env.sim_bin_name = variant.bin_name
    config.env.qdrant_cache.enabled = False
    config.env.monitoring_enabled = False
    config.env.database_enabled = True

    config.map.file_path = str(data_root / "studied_idf_only_osm.pb")
    config.map.neighborhood_file_path = str(data_root / "idf_neighborhoods.json")

    for citizen_config in config.agents.citizens:
        citizen_config.number = 5
        citizen_config.memory_from_file = str(data_root / "idf_500_demographic.json")

    config.exp.name = f"013_citysim_idf_binary_comparison_{variant.name}"
    config.exp.workflow = [
        WorkflowStepConfig(type=WorkflowType.RUN, days=1, ticks_per_step=600)
    ]
    config.logging_level = "INFO"

    config = default(config)
    config = apply_duckdb_overrides(config, exp_id=variant.exp_id)
    config.env.home_dir = str(variant.home_dir)
    config.env.data_dir = str(variant.data_dir)
    config.env.sim_bin_name = variant.bin_name
    return config


def run_variant(config_path: Path, variant: Variant, timeout: int) -> RunResult:
    logging.info("=== Running %s (exp_id=%s) ===", variant.label, variant.exp_id)
    config = build_idf_config(config_path, variant)
    run_with_ray(run_society(config, timeout=timeout, raise_on_timeout=True))
    time.sleep(3)

    duckdb_file = variant.data_dir / "duckdb" / f"{variant.exp_id}.duckdb"
    if not duckdb_file.exists():
        raise AssertionError(f"DuckDB file not created for {variant.name}: {duckdb_file}")

    from en_agentsociety.webapi.api.visits import build_visits_from_frames  # type: ignore
    from en_agentsociety.webapi.datasource import load_experiment_frames  # type: ignore
    from en_agentsociety.webapi.mobility import trajdf_from_visits_df  # type: ignore

    status_df, location_type_df = load_experiment_frames(
        variant.exp_id,
        duckdb_path=str(duckdb_file),
    )
    if status_df.empty:
        raise AssertionError(f"no step_agent_status rows recorded for {variant.name}")

    visits_df = build_visits_from_frames(status_df, location_type_df)
    if visits_df.empty:
        raise AssertionError(f"no visits extracted for {variant.name}")

    trajectory = trajdf_from_visits_df(visits_df)
    logging.info(
        "%s rows: status=%d location_type=%d visits=%d trajectory=%d agents=%d",
        variant.name,
        len(status_df),
        len(location_type_df),
        len(visits_df),
        len(trajectory),
        trajectory["uid"].nunique(),
    )
    return RunResult(
        variant=variant,
        duckdb_file=duckdb_file,
        status_rows=len(status_df),
        location_type_rows=len(location_type_df),
        visit_rows=len(visits_df),
        trajectory_rows=len(trajectory),
        agent_count=int(trajectory["uid"].nunique()),
        trajectory=trajectory,
    )


def _metric_rows_by_name(rows: list[dict[str, Any]], name_key: str = "name") -> dict[str, Any]:
    return {str(row[name_key]): row.get("value") for row in rows if name_key in row}


def build_report(original: RunResult, sibling: RunResult) -> dict[str, Any]:
    from en_agentsociety.webapi.mobility import build_comparison_payload  # type: ignore

    payload = build_comparison_payload(
        original.trajectory,
        sibling.trajectory,
        original.variant.label,
        sibling.variant.label,
    )
    serialized_payload = json.dumps(payload)

    metrics = payload.get("metrics", {})
    charts = payload.get("charts", {})
    report = {
        "summary": {
            "labels": payload.get("labels", []),
            "json_payload_bytes": len(serialized_payload),
            "chart_keys": sorted(charts.keys()),
            "warnings": payload.get("warnings", []),
        },
        "runs": {
            original.variant.name: {
                "label": original.variant.label,
                "exp_id": original.variant.exp_id,
                "duckdb_file": str(original.duckdb_file),
                "status_rows": original.status_rows,
                "location_type_rows": original.location_type_rows,
                "visit_rows": original.visit_rows,
                "trajectory_rows": original.trajectory_rows,
                "agent_count": original.agent_count,
            },
            sibling.variant.name: {
                "label": sibling.variant.label,
                "exp_id": sibling.variant.exp_id,
                "duckdb_file": str(sibling.duckdb_file),
                "status_rows": sibling.status_rows,
                "location_type_rows": sibling.location_type_rows,
                "visit_rows": sibling.visit_rows,
                "trajectory_rows": sibling.trajectory_rows,
                "agent_count": sibling.agent_count,
            },
        },
        "metrics": {
            "wasserstein": metrics.get("wasserstein", []),
            "jensen_shannon": metrics.get("jensen_shannon", []),
            "cpc": metrics.get("cpc", []),
        },
        "metric_lookup": {
            "wasserstein": _metric_rows_by_name(metrics.get("wasserstein", [])),
            "jensen_shannon": _metric_rows_by_name(metrics.get("jensen_shannon", [])),
            "cpc": _metric_rows_by_name(metrics.get("cpc", []), name_key="resolution"),
        },
    }
    return report


def write_report(report: dict[str, Any], report_out: Path) -> None:
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def log_report(report: dict[str, Any], report_out: Path) -> None:
    logging.info("Charts produced: %s", report["summary"]["chart_keys"])
    logging.info("Wasserstein: %s", report["metrics"]["wasserstein"])
    logging.info("Jensen-Shannon: %s", report["metrics"]["jensen_shannon"])
    logging.info("CPC: %s", report["metrics"]["cpc"])
    if report["summary"]["warnings"]:
        logging.info("Warnings: %s", report["summary"]["warnings"])
    logging.info("Comparison report written to: %s", report_out)


def main() -> None:
    args = parse_args()
    ensure_config_exists(args.idf_config)
    _require_dir(args.sim_repo, "sibling simulator repo")
    _require_file(args.original_bin, "original simulator binary")
    _require_file(DEFAULT_DATA_ROOT / "studied_idf_only_osm.pb", "IDF map")
    _require_file(DEFAULT_DATA_ROOT / "idf_neighborhoods.json", "IDF neighborhoods")
    _require_file(DEFAULT_DATA_ROOT / "idf_500_demographic.json", "IDF demographic profile")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    work_dir, cleanup_work_dir = make_work_dir(args.work_dir)
    logging.info("Working directory: %s", work_dir)
    try:
        original_variant, sibling_variant = prepare_variant_dirs(
            work_dir,
            args.original_bin.resolve(),
            args.sim_repo.resolve(),
        )
        original_result = run_variant(
            args.idf_config.resolve(),
            original_variant,
            args.run_timeout_seconds,
        )
        sibling_result = run_variant(
            args.idf_config.resolve(),
            sibling_variant,
            args.run_timeout_seconds,
        )
        report = build_report(original_result, sibling_result)
        write_report(report, args.report_out)
        log_report(report, args.report_out)
        logging.info("E2E IDF CitySim binary comparison PASSED.")
    finally:
        if cleanup_work_dir and not args.keep_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)
        elif args.keep_work_dir:
            logging.info("Kept working directory: %s", work_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        logging.exception("E2E IDF CitySim binary comparison FAILED: %s", e)
        raise SystemExit(1) from e
