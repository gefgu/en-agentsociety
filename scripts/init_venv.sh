#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

cd ${PROJECT_DIR}

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install .
