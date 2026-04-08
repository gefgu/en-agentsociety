# Fault-Tolerant Resume — Economy Checkpoint Check Fix — Run Tracking

Plan: `docs/features/fault-tolerant-resume-economy-fix.md`
Test command: `cd /mnt/raid5/gustavo/citysim/packages/agentsociety && sh tests/run_e2e_tests.sh`

## Steps

- [x] Step 1: `base_database.py` — `_fetch_checkpoint_snapshots()`: remove `has_economy` param, replace economy guard block with unconditional `econ_path` assignment, replace silent fallback with `RuntimeError`
- [x] Step 2: `base_database.py` — `fetch_resume_data()`: remove `has_economy=bool(economy_checkpoint_path)` from call
- [x] Step 3: `clickhouse.py` and `duckdb.py` — `_resume_query("candidate_steps", ...)`: add `AND simulation_step >= 1` to WHERE clause in both backends
