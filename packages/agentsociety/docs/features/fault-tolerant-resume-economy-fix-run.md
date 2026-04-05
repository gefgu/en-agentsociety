# Fault-Tolerant Resume — Economy Checkpoint Check Fix — Run Tracking

Plan: `docs/features/fault-tolerant-resume-economy-fix.md`
Test command: `python -m py_compile`

## Steps

- [ ] Step 1: `clickhouse.py` — `_fetch_checkpoint_snapshots()`: remove `has_economy` param, add `AND simulation_step >= 1`, replace economy guard with unconditional `econ_path` assignment
- [ ] Step 2: `clickhouse.py` — `fetch_resume_data()`: remove `has_economy=bool(economy_checkpoint_path)` from call
- [ ] Step 3: `duckdb.py` — `_fetch_checkpoint_snapshots()`: mirror Step 1
- [ ] Step 4: `duckdb.py` — `fetch_resume_data()`: mirror Step 2
- [ ] Step 5: `simulationengine.py` — `_restore_external_simulator_state()`: replace `RuntimeError` with WARNING log
