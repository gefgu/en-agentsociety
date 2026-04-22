# DuckDB Resume Tests — Run Tracking

Plan: duckdb-resume-tests.md
Test command: sh tests/run_e2e_tests.sh (do NOT run automatically — requires external services)

## Steps

- [ ] Step 1: Add `duckdb>=1.1.0` to `tests/e2e/pyproject.toml`
- [ ] Step 2: Add helpers to `tests/e2e/utils.py`
- [ ] Step 3: Create `tests/e2e/configs/007_resume_with_duckdb.yaml`
- [ ] Step 4: Write `tests/e2e/007_resume_with_duckdb.py`
- [ ] Step 5: Update `tests/run_e2e_tests.sh`
