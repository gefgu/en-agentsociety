"""Run only the sibling (our modified) variant — no original binary needed.

Reuses build_sibling_binary, build_idf_config, and run_variant from the
013 comparison test, so the scenario is byte-for-byte identical.

Usage:
    python run_sibling_only.py [run_timeout_seconds]
"""
from __future__ import annotations

import importlib
import json
import logging
import sys
import tempfile
import time
import uuid
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Import the 013 module by file path
import importlib.util

spec = importlib.util.spec_from_file_location(
    "_013", Path(__file__).parent / "013_citysim_idf_binary_comparison.py"
)
m013 = importlib.util.module_from_spec(spec)  # type: ignore
# Don't exec the module (it would run everything at import time), so we
# instead import only the helpers we need directly:
from utils import apply_duckdb_overrides, run_society, run_with_ray  # noqa: E402

from en_agentsociety.cityagent import default  # type: ignore
from en_agentsociety.configs import Config, WorkflowStepConfig, WorkflowType  # type: ignore
from en_agentsociety.configs.utils import load_config_from_file  # type: ignore

import stat
import subprocess
import uuid
from dataclasses import dataclass

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_IDF_CONFIG = (REPO_ROOT / "../cultural_agents/experiments/09_citysim/configs/03_500_idf.yaml").resolve()
DEFAULT_SIM_REPO   = (REPO_ROOT / "../agentsociety-sim-oss").resolve()
DEFAULT_DATA_ROOT  = (REPO_ROOT / "../cultural_agents/agentsociety_data").resolve()

run_timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 14400
work_dir = Path(tempfile.mkdtemp(prefix="sibling-only-"))
logging.info("Work dir: %s  timeout: %ds", work_dir, run_timeout)


@dataclass(frozen=True)
class Variant:
    name: str
    label: str
    bin_name: str
    home_dir: Path
    data_dir: Path
    exp_id: str


sibling = Variant(
    name="sibling",
    label="sibling agentsociety-sim-oss",
    bin_name="agentsociety-sim-oss_sibling",
    home_dir=work_dir / "sibling" / "home",
    data_dir=work_dir / "sibling" / "data",
    exp_id=str(uuid.uuid4()),
)

# Build sibling binary
sibling.home_dir.mkdir(parents=True, exist_ok=True)
out_bin = sibling.home_dir / sibling.bin_name
logging.info("Building sibling: go build -o %s .", out_bin)
subprocess.run(["go", "build", "-o", str(out_bin), "."], cwd=DEFAULT_SIM_REPO, check=True)
out_bin.chmod(out_bin.stat().st_mode | stat.S_IXUSR)
logging.info("Build complete")

# Config — identical to 013 build_idf_config
config: Config = load_config_from_file(str(DEFAULT_IDF_CONFIG), Config)
config.env.home_dir     = str(sibling.home_dir)
config.env.data_dir     = str(sibling.data_dir)
config.env.sim_bin_name = sibling.bin_name
config.env.qdrant_cache.enabled = False
config.env.monitoring_enabled   = False
config.env.database_enabled     = True
config.map.file_path               = str(DEFAULT_DATA_ROOT / "studied_idf_only_osm.pb")
config.map.neighborhood_file_path  = str(DEFAULT_DATA_ROOT / "idf_neighborhoods.json")
for citizen_config in config.agents.citizens:
    citizen_config.number           = 5
    citizen_config.memory_from_file = str(DEFAULT_DATA_ROOT / "idf_500_demographic.json")
config.exp.name     = f"013_citysim_idf_binary_comparison_sibling"
config.exp.workflow = [WorkflowStepConfig(type=WorkflowType.RUN, days=1, ticks_per_step=600)]
config.logging_level = "INFO"
config = default(config)
config = apply_duckdb_overrides(config, exp_id=sibling.exp_id)
config.env.home_dir     = str(sibling.home_dir)
config.env.data_dir     = str(sibling.data_dir)
config.env.sim_bin_name = sibling.bin_name

# Run
logging.info("=== Running sibling (exp_id=%s) ===", sibling.exp_id)
t0 = time.time()
run_with_ray(run_society(config, timeout=run_timeout, raise_on_timeout=True))
elapsed = time.time() - t0
logging.info("Sibling run complete in %.1fs (%.1f min)", elapsed, elapsed / 60)

time.sleep(3)
duckdb_file = sibling.data_dir / "duckdb" / f"{sibling.exp_id}.duckdb"
assert duckdb_file.exists(), f"DuckDB not found: {duckdb_file}"

from en_agentsociety.webapi.api.visits import build_visits_from_frames  # type: ignore
from en_agentsociety.webapi.datasource import load_experiment_frames     # type: ignore
from en_agentsociety.webapi.mobility import trajdf_from_visits_df        # type: ignore

status_df, location_type_df = load_experiment_frames(sibling.exp_id, duckdb_path=str(duckdb_file))
assert not status_df.empty, "no step_agent_status rows"
visits_df = build_visits_from_frames(status_df, location_type_df)
assert not visits_df.empty, "no visits extracted"
traj = trajdf_from_visits_df(visits_df)

summary = {
    "exp_id":             sibling.exp_id,
    "elapsed_seconds":    round(elapsed, 1),
    "status_rows":        len(status_df),
    "location_type_rows": len(location_type_df),
    "visit_rows":         len(visits_df),
    "trajectory_rows":    len(traj),
    "agent_count":        int(traj["uid"].nunique()) if not traj.empty else 0,
    "duckdb_file":        str(duckdb_file),
    "work_dir":           str(work_dir),
}
print(json.dumps(summary, indent=2))
logging.info("Sibling-only run PASSED.")
