#!/bin/sh

# End-to-end test runner for AgentSociety

set -e

# 1. Resolve the directory of this script (the e2e folder)
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# If the script is already IN the e2e folder, SCRIPT_DIR is your e2e folder.
# If this script is in the ROOT, use E2E_DIR="$SCRIPT_DIR/e2e"
E2E_DIR="$SCRIPT_DIR/e2e"

# 2. Change to the e2e directory specifically
cd "$E2E_DIR"

# Fix permissions on Docker-owned data dirs so Ray can traverse them and the test can write
sudo chmod -R o+rwx "$E2E_DIR/data/*" 2>/dev/null || true

echo "Running end-to-end tests from: $(pwd)"

if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv is not installed or not in PATH" >&2
    exit 1
fi

# 3. Run the script. Since we are already in the folder, 
# we can refer to the python file directly.

# uv run python "001_run_simplest_e2e.py" "$@"
uv run python "002_run_e2e_with_clickhouse.py" "$@"

# It takes about 5-10 minutes to run fully each script 