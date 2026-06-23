#!/bin/sh

# Unit test runner for AgentSociety (no LLM/Ray required)

set -e

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
E2E_VENV="${SCRIPT_DIR}/e2e/.venv"
PYTHON="${E2E_VENV}/bin/python"

if [ ! -x "${PYTHON}" ]; then
    echo "ERROR: e2e venv not found at ${E2E_VENV}" >&2
    echo "Run sh tests/run_e2e_tests.sh once first to create it." >&2
    exit 1
fi

# Install pytest and pytest-asyncio into e2e venv if not present
if ! "${PYTHON}" -m pytest --version >/dev/null 2>&1; then
    echo "Installing pytest..."
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "${PYTHON}" pytest pytest-asyncio --quiet
    else
        echo "ERROR: uv not found. Cannot install pytest." >&2
        exit 1
    fi
fi

# Run from the package root so en_agentsociety imports resolve
cd "${SCRIPT_DIR}/.."
echo "Running unit tests from: $(pwd)"
"${PYTHON}" -m pytest tests/unit/ -v "$@"
