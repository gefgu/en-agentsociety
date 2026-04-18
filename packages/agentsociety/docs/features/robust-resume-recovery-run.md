# Robust Resume Recovery — Run Tracking

Plan: `docs/features/robust-resume-recovery.md`
Test command: `sh tests/run_e2e_tests.sh` (from `packages/agentsociety/`)

## Steps

- [ ] Step 1: Add `resume_config_mismatch_action` field to `EnvConfig` in `configs/env.py`
- [ ] Step 2: Strip `home_dir` in `_normalize_resume_config` in `infrastructuremanager.py`
- [ ] Step 3: Add `_compute_config_diff` helper and update mismatch error handling in `infrastructuremanager.py`
- [ ] Step 4: Add `_is_sqlite_corruption_error` helper in `storage/database.py`
- [ ] Step 5: Add `_rename_corrupt_sqlite` helper in `storage/database.py`
- [ ] Step 6: Wrap `_create_tables` with corruption detection and retry logic
- [ ] Step 7: Run e2e tests to verify no regressions
