#!/bin/sh

# End-to-end test runner for AgentSociety

set -e

# 1. Resolve the directory of this script (the e2e folder)
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
# If the script is already IN the e2e folder, SCRIPT_DIR is your e2e folder.
# If this script is in the ROOT, use E2E_DIR="$SCRIPT_DIR/e2e"
E2E_DIR="${SCRIPT_DIR}/e2e"

# 2. Change to the e2e directory specifically
cd "${E2E_DIR}"

echo "Running end-to-end tests from: $(pwd)"

# Keep Ray from inheriting runtime env packaging behavior from external launchers.
export RAY_ENABLE_UV_RUN_RUNTIME_ENV=0
export RAY_RUNTIME_ENV_IGNORE_GITIGNORE=1

# 3. Run the script. Since we are already in the folder,
# we can refer to the python file directly.

# Prefer local venv Python to avoid uv-injected runtime_env packaging of tests/e2e.
if [ -x "${E2E_DIR}/.venv/bin/python" ]; then
	PYTHON_BIN="${E2E_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
	PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
	PYTHON_BIN="$(command -v python)"
elif command -v uv >/dev/null 2>&1; then
	PYTHON_BIN=""
else
	echo "ERROR: no Python interpreter found (and uv is unavailable)" >&2
	exit 1
fi

if [ -n "${PYTHON_BIN}" ]; then
	# "$PYTHON_BIN" "001_run_simplest_e2e.py" "$@"
	# "$PYTHON_BIN" "002_run_e2e_with_clickhouse.py" "$@"
	"${PYTHON_BIN}" "003_resume_agent_state.py" "--config" "$E2E_DIR/configs/003_resume_single_agent_with_local.yaml" "$@"
	# "${PYTHON_BIN}" "007_resume_with_duckdb.py" "--config" "$E2E_DIR/configs/007_resume_with_duckdb.yaml" "$@"
	# "${PYTHON_BIN}" "008_sqlite_corruption_recovery.py" "$@"
	"${PYTHON_BIN}" "009_agentsociety_mode.py" "--config" "$E2E_DIR/configs/009_agentsociety_mode.yaml" "$@"
	# "${PYTHON_BIN}" "003_resume_agent_state.py" "--config" "$E2E_DIR/configs/003_resume_10_agents_local.yaml" "$@"
	# "${PYTHON_BIN}" "004_resume_moving_agent_state.py" "--config" "$E2E_DIR/configs/003_resume_10_agents_local.yaml" "--wait-for-movement-timeout-seconds" "9000" "$@"
	# "${PYTHON_BIN}" "004_resume_moving_agent_state.py" "--config" "${E2E_DIR}/configs/003_resume_100_agents_local.yaml" "--wait-for-movement-timeout-seconds" "9000" "$@"
	# "${PYTHON_BIN}" "005_resume_lane_position_state.py" "--config" "$E2E_DIR/configs/003_resume_10_agents_local.yaml" "--wait-for-lane-timeout-seconds" "9000" "$@"
	# "${PYTHON_BIN}" "005_resume_lane_position_state.py" "--config" "$E2E_DIR/configs/003_resume_100_agents_local.yaml" "--wait-for-lane-timeout-seconds" "9000" "$@"
	# "$PYTHON_BIN" "006_qdrant_cache.py" "$@"
	# "$PYTHON_BIN" "006_qdrant_cache.py" "--config" "$E2E_DIR/configs/006_qdrant_cache_with_modal.yaml" "$@"
	# "$PYTHON_BIN" "001_run_simplest_e2e.py" "--config" "$E2E_DIR/configs/007_run_traffic_simulator.yaml" "$@"
fi

# It takes about 5-10 minutes to run fully each script
