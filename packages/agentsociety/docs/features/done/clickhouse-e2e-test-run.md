# ClickHouse E2E Test — Run Tracking

Plan: clickhouse-e2e-test.md
Test command: `cd /mnt/raid5/gustavo/citysim/packages/agentsociety/tests/e2e && uv run python run_e2e_clickhouse.py`

## Steps

- [ ] Step 1: Add `testcontainers[clickhouse]` to `tests/e2e/pyproject.toml` and regenerate `uv.lock`
- [ ] Step 2: Create `tests/e2e/config.clickhouse.yaml`
- [ ] Step 3: Create `tests/e2e/run_e2e_clickhouse.py`
- [ ] Step 4: Update `tests/run_e2e_tests.sh` with optional ClickHouse test (gated on `RUN_CLICKHOUSE_E2E=1`)
