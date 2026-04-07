# Resume Agent Count Fix
> Fix the `_validate_resume_agent_count` check so that it counts all agent types, and audit the entire resume/checkpoint pipeline for gaps and inconsistencies.

---

## Purpose & Motivation

When resuming a simulation that includes institution agents (firms, banks, NBS, government), the startup validation raises:

```
ValueError: Agent number mismatch for resume source experiment '...':
    configured citizens=10, kv snapshot agent count=14
```

The check at `agentsociety/simulation/infrastructuremanager.py:196–203` counts only agents whose class is a subclass of `CitizenAgentBase`, but the KV snapshot table stores snapshots for **all** agents — citizens and institutions alike — because `save_checkpoint` at `agentsociety/simulation/checkpointmanager.py:465–476` iterates over `agent_manager.agents.values()` unconditionally, without filtering by type.

The mismatch is structural: the writer is broader than the reader expects.

Beyond the immediate crash, a full read of the checkpoint/resume pipeline reveals additional gaps: institution agents have their KV memory saved but never restored on resume; the supervisor agent is neither snapshotted nor restored; the config-mismatch check is fragile against legal changes; and the rollback candidate query is susceptible to off-by-one issues with step numbering.

---

## Success Criteria

1. A simulation with N citizens + M institution agents resumes without a `ValueError`.
2. Institution agent memory is correctly restored from the KV snapshot (or there is an explicit, documented policy decision to skip it).
3. The supervisor agent's checkpoint/resume behavior is explicitly defined.
4. The validation error message accurately reports what was compared.
5. No existing passing test regresses.
6. All questions in the "Open Questions" section are answered and the resulting decisions are reflected in code.

---

## Scope

**In scope:**
- Fix `_validate_resume_agent_count` in `infrastructuremanager.py:188–203`.
- Decide and implement whether institution agent memory is restored on resume.
- Decide and implement the supervisor agent checkpoint/resume policy.
- Tighten or relax the config-mismatch check as needed.
- Document any known partial-write or async-flush races.
- Update or add the e2e test `tests/e2e/003_resume_agent_state.py` to cover a multi-agent-type scenario.

**Out of scope:**
- Rewriting the storage backend (ClickHouse / DuckDB).
- Changing the mobility/economy restore logic (unless a question below reveals an issue).
- Changing the `WorkflowType` enum or the workflow runner.

---

## Constraints

- All changes must be backward-compatible: existing snapshots written by the old code (citizens only) must still produce a valid resume, even if institution state is treated as "fresh" on those old snapshots.
- No test suite beyond the e2e scripts — changes must not break the example runs in `/mnt/raid5/gustavo/citysim/examples/`.
- The fix must work for both ClickHouse and DuckDB backends.

---

## Architecture & Integration Points

The full resume flow, with file:line anchors:

### Write path (checkpoint)

1. `SimulationEngine.step()` at `simulationengine.py:830–838` calls `CheckpointManager.save_checkpoint(...)` after every step.
2. `CheckpointManager.save_checkpoint()` at `checkpointmanager.py:437–535` iterates `agent_manager.agents.values()` (all types, no filter) and calls `agent.memory.create_snapshot_records(...)` for each agent, accumulating KV/stream/spatial records.
3. The records are enqueued to `DataRecorder` (`checkpointmanager.py:508–515`) which forwards them to `DatabaseActor` (`datarecorder.py:427–444`), which calls `db.insert_records("agent_kv_snapshot", ...)`.
4. After flushing memory records, the economy binary is saved to disk and `db_actor.update_experiment_info_checkpoint.remote(...)` is called (`checkpointmanager.py:524–530`) to record `last_mobility_safe_step` and the economy path — **this is fire-and-forget** (`.remote()` without `await`).

### Read path (resume)

1. `SimulationEngine.init()` at `simulationengine.py:224` calls `InfrastructureManager.load_resume_state()`.
2. `load_resume_state()` at `infrastructuremanager.py:205–241` calls `db_actor.fetch_resume_data.remote(source_exp_id, rollback_depth=...)`.
3. `DatabaseActor.fetch_resume_data()` at `database_actor.py:243–256` delegates to `BaseSimulationDatabase.fetch_resume_data()` at `base_database.py:389–462`.
4. That method reads `kv_snapshots` as a `dict[int, list[dict]]` — **keyed by agent_id for ALL agents** (citizens + institutions) because the `kv_rows` SQL query has no agent-type filter.
5. Back in `SimulationEngine.init()` at `simulationengine.py:252`, **before agents are initialized**, `_validate_resume_agent_count(agents)` is called.
6. `_validate_resume_agent_count` at `infrastructuremanager.py:188–203` counts only `CitizenAgentBase` subclasses in the `agents` list, but compares against `len(kv_snapshots)` which includes ALL agent types. This is the immediate bug.
7. Agent memory is restored at `agentmanager.py:534–547`, but only for `CitizenAgentBase` agents (`if resume_state is not None and issubclass(agent_class, CitizenAgentBase)`). Institution agent memory is silently skipped.
8. External simulators and messager state are restored by `CheckpointManager.restore_external_simulator_state()` and `restore_messager_state()` at `checkpointmanager.py:76` and `401`.

### Candidate step rollback query

Both backends (`clickhouse.py:262–271`, `duckdb.py:303–309`) query:

```sql
SELECT DISTINCT simulation_step FROM agent_kv_snapshot
WHERE simulation_step >= 1 AND simulation_step <= {resume_step}
ORDER BY simulation_step DESC
LIMIT {rollback_depth}
```

The `simulation_step >= 1` guard is intentional (see git commit `f01c5f2`) to exclude step 0. This means the resume/rollback will never land on step 0, even if it is the only snapshot available.

---

## Problems Found

### Problem 1 — The Immediate Bug: `_validate_resume_agent_count` counts citizens only

**File:** `agentsociety/simulation/infrastructuremanager.py:179–203`

`_count_citizen_agents()` uses `issubclass(agent_class, CitizenAgentBase)` to count, producing N.
`len(kv_snapshots)` is the number of **unique agent IDs** in the KV table, which is N + M (citizens + institutions).
These are compared directly, producing a false mismatch for any experiment with institution agents.

**Fix direction:** Count total agents in the `agents` list (not just citizens), OR count only citizen agent IDs in `kv_snapshots`. The choice depends on answers to Question 1–3 below.

---

### Problem 2 — Institution agent memory is snapshotted but never restored

**Files:**
- Write: `checkpointmanager.py:465` — `for agent in agent_manager.agents.values()` (no type filter).
- Read: `agentmanager.py:535` — `if resume_state is not None and issubclass(agent_class, CitizenAgentBase)`.

Institution agents (Firm, Bank, NBS, Government) have their KV memory snapshotted on every step, but when `initialize_agents()` is called during resume, the `issubclass(..., CitizenAgentBase)` guard silently skips them. Their memory is re-initialized from the config's `memory_config_func`, effectively losing any state changes from the crashed run.

This is a silent data loss. Whether it matters depends on whether institution agent memory is expected to evolve during a run and whether that evolution needs to be restored.

---

### Problem 3 — The supervisor agent is neither snapshotted nor restored

**Files:**
- `agentmanager.py:420–491` — `_init_supervisor_from_memory_file` creates the supervisor directly and stores it only in `message_interceptor`, not in `_id2agent`.
- `agentmanager.py:279–284` — For normal (non-file) supervisors, they are added to `supervisor_ids` but **not added to `agents`**.
- `checkpointmanager.py:465` — `for agent in agent_manager.agents.values()` — the supervisor is never in `agents`, so it is never snapshotted.
- `agentmanager.py:534–547` — Resume restore only processes agents in the `agents` list; supervisor never appears.

The supervisor is effectively invisible to the checkpoint and resume system.

---

### Problem 4 — `_count_citizen_agents` is duplicated in two classes

**Files:**
- `infrastructuremanager.py:179–186` — `InfrastructureManager._count_citizen_agents()`
- `agentmanager.py:128–135` — `AgentManager._count_citizen_agents()`

These are identical static methods doing the same thing. Only the `InfrastructureManager` version is ever called (at `simulationengine.py:252`). The `AgentManager` copy is dead code, never invoked anywhere.

---

### Problem 5 — `update_experiment_info_checkpoint` is fire-and-forget

**File:** `checkpointmanager.py:524–530`

```python
db_actor.update_experiment_info_checkpoint.remote(
    exp_id=self._exp_id,
    last_mobility_safe_step=step,
    prev_mobility_safe_step=prev_checkpoint,
    economy_checkpoint_path=econ_path,
)
```

This Ray `.remote()` call is not `await`ed. The KV/stream/spatial records are already enqueued to the `DataRecorder` queue, but the experiment-info checkpoint update happens asynchronously. If the process crashes between the KV flush and this remote call completing, `last_mobility_safe_step` will not be updated in the database, and the next resume will either use a stale `last_mobility_safe_step` or fall back via the rollback mechanism.

Whether this is actually a problem depends on the gap between "enqueued to DataRecorder" and "flushed to database" relative to when the experiment-info update completes — but the ordering is not guaranteed.

---

### Problem 6 — DataRecorder flush happens after the checkpoint write but before the economy file + DB update

**File:** `simulationengine.py:830–838` (checkpoint call) vs. `simulationengine.py:924` (DataRecorder flush)

The order in a single step is:
1. `save_checkpoint(...)` — enqueues KV/stream/spatial records to DataRecorder queue, saves economy file to disk, and **fires-and-forgets** `update_experiment_info_checkpoint`.
2. `await self._flush_data_recorder(step=self._total_steps)` — waits for the DataRecorder queue to drain.

The flush at step 2 waits for KV records but **not** for the `update_experiment_info_checkpoint` remote call (which goes through a Ray actor queue, not through `DataRecorder`). The `flush_all_batches` called by the DataRecorder flush covers the KV snapshot batches but not the experiment_info batch, unless `flush_all_batches` happens to time out the experiment_info batch at the same moment.

---

### Problem 7 — The config-mismatch check normalizes but has no tolerance for legitimate additions

**File:** `infrastructuremanager.py:230–236` (`load_resume_state`)

The config comparison normalizes both old and new configs and requires them to be equal. This means that even a cosmetic addition — like adding a log level or changing a monitoring flag — will cause resume to fail with a `ValueError: Configuration mismatch`. There is no ability to whitelist fields that are allowed to differ between runs.

---

### Problem 8 — `latest_step` is read from `step_agent_status`, not from `agent_kv_snapshot`

**File:** `base_database.py:416–421`

`latest_step` is determined by `max(simulation_step)` from the `step_agent_status` table. However, `step_agent_status` is written via `DataRecorder.save_statuses()` at `datarecorder.py:126`, which only writes `CitizenAgentBase` rows to SQLite/PgSQL and skips institution agents for that particular path. More importantly, `step_agent_status` records are written by a separate async queue path than the KV snapshots — there is no guarantee they are in sync.

The KV snapshot step and the `step_agent_status` max step could disagree if one flush succeeds and the other doesn't before a crash.

---

### Problem 9 — The rollback candidate query excludes step 0 but there is no fallback for step 0 crashes

**Files:** `clickhouse.py:263`, `duckdb.py:305`

```sql
WHERE simulation_step >= 1 AND simulation_step <= {resume_step}
```

If the experiment writes its only checkpoint at step 0 and then crashes, the candidate query returns no rows, and resume raises `RuntimeError: Resume failed: no valid checkpoint found`. The `last_mobility_safe_step` guard in `base_database.py:435` prevents even entering `_fetch_checkpoint_snapshots` unless `resume_step >= 0`, but if `last_mobility_safe_step` is 0 the query is still invoked and returns nothing because step 0 is excluded.

The git commit `f01c5f2` explicitly excludes step 0 with the rationale "resuming from it produces a semantically empty state." This means the system has a deliberate policy of not allowing step-0 resumes, but the error message when this happens is confusing (`no valid checkpoint found`).

---

### Problem 10 — `expected_agent_ids` is always an empty set, disabling completeness validation

**File:** `base_database.py:447–449`, `_fetch_checkpoint_snapshots` at `base_database.py:499`

`fetch_resume_data` calls `_fetch_checkpoint_snapshots` with `expected_agent_ids=set()`. Inside `_fetch_checkpoint_snapshots`, the completeness check `if expected_agent_ids and not expected_agent_ids.issubset(kv_agent_ids)` at `base_database.py:499` is guarded by `if expected_agent_ids`, so it **always short-circuits** because the set is empty. The validation that was clearly designed to detect partial writes is permanently disabled.

---

## Similar Patterns & Reuse

- **What it is:** `agentmanager.py:128–135` — `AgentManager._count_citizen_agents(agents)`
- **What it does:** Counts citizen agents in an init-tuple list.
- **How this feature uses it:** This method is dead code and should be removed; the fix should live only in `InfrastructureManager._validate_resume_agent_count`.

- **What it is:** `agentmanager.py:534–547` — resume restore branch inside `initialize_agents`
- **What it does:** Applies KV/stream/spatial snapshots to citizen agent memory on resume.
- **How this feature uses it:** The institution agent restore (if decided) should follow the same pattern, guarded by an `issubclass(agent_class, InstitutionAgentBase)` branch.

---

## Implementation Strategy

The strategy below is ordered from smallest to largest blast radius. Each step must be completed before the next.

### Step 1 — Fix the validation (the minimal unblock)

**Before:** `infrastructuremanager.py:188–203` counts only `CitizenAgentBase` in `agents` and compares to `len(kv_snapshots)`.

**After (option A — count all agents):**
```python
expected_total = len(agents)
available_total = len(kv_snapshots)
if expected_total != available_total:
    raise ValueError(...)
```

**After (option B — count only citizens in both sides):**
```python
expected_citizens = self._count_citizen_agents(agents)
citizen_ids_in_snapshot = {
    aid for aid, entries in kv_snapshots.items()
    if any_entry_belongs_to_citizen(...)  # requires knowing which IDs are citizens
}
available_citizens = len(citizen_ids_in_snapshot)
```

Option A is simpler but requires that institution agents ARE snapshotted (which they currently are). Option B requires knowing at validation time which snapshot IDs belong to citizens, which is not available without a type lookup. **Answer to Question 1 determines which option to take.**

Also remove the dead `AgentManager._count_citizen_agents` static method at `agentmanager.py:128–135`.

### Step 2 — Decide and implement institution agent memory restore

**Before:** `agentmanager.py:535` — `if resume_state is not None and issubclass(agent_class, CitizenAgentBase)`.

**After (if restoring institution state):** Add an `elif issubclass(agent_class, InstitutionAgentBase)` branch that calls `memory_init.resume_from_snapshots(...)` with the same pattern as citizens. The `InstitutionAgentBase` class is already imported in `datarecorder.py:8` and available in the same package.

**After (if NOT restoring institution state):** Leave the restore logic as-is, but change the checkpoint write to skip institution agents, OR accept silent re-initialization and document it clearly.

### Step 3 — Define supervisor checkpoint/resume behavior

**Before:** The supervisor is not in `agent_manager.agents` and is therefore invisible to the checkpoint system.

**After:** Either (a) add the supervisor to `_id2agent` so it participates in the normal snapshot/restore cycle, or (b) explicitly document that the supervisor is always re-initialized from config on resume, which is safe if the supervisor is stateless.

### Step 4 — Make `update_experiment_info_checkpoint` synchronous or explicitly ordered

**Before:** `checkpointmanager.py:525` — fire-and-forget `.remote()` call.

**After:** Either `await` the call (requires converting `save_checkpoint` to await the Ray ref), or add the experiment-info update to the `DataRecorder` flush path so it is covered by the `flush_all_batches` call.

### Step 5 — Re-enable the `expected_agent_ids` completeness check

**Before:** `base_database.py:447` — `_fetch_checkpoint_snapshots(..., expected_agent_ids=set())`.

**After:** Pass the actual set of expected agent IDs (derived from the config) into `fetch_resume_data`, and thread it through to `_fetch_checkpoint_snapshots`. This re-enables the rollback mechanism as designed.

### Step 6 — Improve the step-0 resume error message

**Before:** Cryptic `RuntimeError: Resume failed: no valid checkpoint found`.

**After:** Detect the `last_mobility_safe_step == 0` case and emit a clear message explaining that step-0 checkpoints are not resumable by design.

---

## Trade-Offs

| Decision | Gain | Cost |
|---|---|---|
| Count all agents in validation | Simple, correct immediately | Requires institution restore to be decided |
| Restore institution memory | Accurate state after resume | More code, possible compatibility issues with old snapshots |
| Add supervisor to `_id2agent` | Uniform checkpoint coverage | Changes supervisor lifecycle; may affect `MessageInterceptor` linkage |
| Await `update_experiment_info_checkpoint` | Removes async gap | Adds latency to every checkpoint step |
| Re-enable `expected_agent_ids` check | Catches partial writes | May cause legitimate rollbacks if some agents write faster than others |

---

## Rejected Approaches

- **Remove the count validation entirely.** Rejected because the check does catch real mismatches (e.g., the user changes the number of citizens between runs). The fix should make it accurate, not remove it.
- **Filter institution agents out of the KV snapshot write.** Technically solves the count mismatch, but silently loses institution state snapshots that are already being written. This is a regression in checkpoint completeness.
- **Use a separate count field in experiment_info to track total snapshotted agents.** Adds complexity and a new schema migration without solving the underlying asymmetry between writer and reader.

---

## Assumptions & Open Questions

The following questions **must be answered before implementation begins**, as they determine the shape of every significant change.

### Question group 1: Scope of validation fix

**Q1.** Should the validation compare total agent count (citizens + institutions) vs. total KV snapshot agent count? Or should it compare only citizen count vs. citizen snapshot count (ignoring institution entries in the snapshot)?

**Q2.** If the answer to Q1 is "total vs. total": what happens when a user runs an old simulation (snapshot has only citizens) and resumes with a config that adds institution agents? Should this be allowed, blocked, or warned?

**Q3.** Is it acceptable for the resume validation to differ in behavior depending on whether `kv_snapshots` includes institution agents or not (i.e., the old-snapshot backward-compat case)?

### Question group 2: Institution agent memory on resume

**Q4.** Do institution agents (Firm, Bank, NBS, Government) have KV memory that evolves meaningfully during a run? If yes, is it important to restore that memory on resume, or is re-initializing from config acceptable?

**Q5.** If institution memory should be restored: should the same `resume_from_snapshots` path used for citizens be used, or does institution memory have a different schema that needs a different restore path?

**Q6.** If institution memory should NOT be restored: should the checkpoint write be changed to skip institution agents (so the snapshot only contains citizens), or should institutions continue to be snapshotted but just never restored?

### Question group 3: Supervisor checkpoint/resume

**Q7.** Is the supervisor agent stateful in a way that matters across a crash/resume? Or is it always effectively stateless (initialized fresh from config each time)?

**Q8.** If the supervisor has meaningful state: should it be added to `agent_manager.agents` so it participates in the normal snapshot cycle? Are there reasons it was kept out of `_id2agent` originally (e.g., it doesn't participate in `run_all_agents()`)?

**Q9.** What should happen if a simulation has a supervisor in the original run but NOT in the resume config, or vice versa? Raise an error? Warn and skip?

### Question group 4: Checkpoint write ordering and flush guarantees

**Q10.** Is the fire-and-forget nature of `update_experiment_info_checkpoint.remote(...)` at `checkpointmanager.py:524–530` an acceptable risk? Concretely: if the process crashes in the window between the KV flush completing and the experiment-info update landing in the database, the next resume will not know the correct `last_mobility_safe_step`. Is that acceptable, or does `last_mobility_safe_step` need to be reliably up-to-date?

**Q11.** Should `save_checkpoint` be changed to `await` the `update_experiment_info_checkpoint` call? This would require either making `CheckpointManager.save_checkpoint` hold a `ray.get()` call (adding latency) or routing the update through `DataRecorder` (requiring a new event type).

**Q12.** Is the current flush ordering (KV records enqueued, economy file saved, DB update fired-and-forgot, then DataRecorder flush) correct and intentional? Or was the flush ordering designed without the async DB update gap in mind?

### Question group 5: Config-mismatch check

**Q13.** The current config comparison at `infrastructuremanager.py:230–236` requires full equality (minus a few stripped keys). Is it intentional that adding a new field to the config (e.g., changing `logging_level`) would prevent resuming an existing run? Should certain fields be excluded from the comparison?

**Q14.** Should the config comparison be relaxed to allow resume even when non-structural fields (e.g., monitoring flags, logging levels, `data_dir`) differ? If so, what is the list of fields that ARE required to match?

### Question group 6: Completeness validation (expected_agent_ids)

**Q15.** `_fetch_checkpoint_snapshots` at `base_database.py:499` has a completeness check that is permanently disabled because `expected_agent_ids` is always passed as an empty set. Should this be re-enabled? If yes, which agent IDs should be considered "expected" — all agent IDs from the config, or only citizen IDs?

**Q16.** If completeness validation is re-enabled and a checkpoint at step N is found to be missing some agent IDs, should the system: (a) roll back to step N-1, (b) raise an error, or (c) proceed with partial state and log a warning?

### Question group 7: Step-0 resume behavior

**Q17.** Is the policy of "step 0 checkpoints are never resumable" correct and intentional? If a run crashes during step 0 (e.g., during agent initialization), the user gets `no valid checkpoint found` with no way to recover. Is the correct resolution "run from scratch" in that case?

**Q18.** Should the error message when step-0 is the only candidate be improved to explicitly state "step 0 checkpoints are excluded by design; please start a new experiment"?

### Question group 8: Test coverage

**Q19.** The existing test `tests/e2e/003_resume_agent_state.py` uses config `003_resume_single_agent_with_modal.yaml`. Does that config include institution agents? If not, the test would not have caught this bug. Should the test be updated to always include at least one of each agent type (firm + bank + nbs + government)?

**Q20.** Should there be a unit test (not just an e2e test) that verifies `_validate_resume_agent_count` works correctly for each of: (a) citizens-only, (b) citizens + institutions, (c) count mismatch, (d) empty snapshot?

---

## Code That Could Be Refactored *(informational)*

- `agentmanager.py:128–135` — `AgentManager._count_citizen_agents()` is dead code, never called. Should be deleted once the validation fix is in place and the method in `InfrastructureManager` is updated.
- `infrastructuremanager.py:179–186` — `InfrastructureManager._count_citizen_agents()` could be renamed `_count_all_agents()` or removed entirely if the validation logic is simplified to `len(agents)`.
- `agentmanager.py:311–362` — `_split_agent_configs_by_memory_source()` produces 6-key dicts with `"supervisor"` always included. The supervisor is then handled separately in `_init_supervisor_from_memory_file`. This double-path for the supervisor makes the lifecycle hard to follow; unifying it under the normal agent init path (with a type gate for the `MessageInterceptor` binding) would simplify the code.
- `checkpointmanager.py:118–223` — The KV-parsing helper functions (`_parse_kv_value`, `_parse_kv_int`, etc.) are defined as closures inside `restore_external_simulator_state`. They could be module-level helpers or `@staticmethod`s to make them testable independently.

---

## Proposed Next Steps

1. **Answer all 20 questions above.** No code should be written until Q1–Q6 (validation scope and institution restore policy) are resolved.
2. **Fix Problem 1** — Update `_validate_resume_agent_count` in `infrastructuremanager.py:188–203` based on the answers to Q1–Q3. Remove the dead `AgentManager._count_citizen_agents` method.
3. **Fix Problem 2** — Based on the answers to Q4–Q6, either add institution agent restore in `agentmanager.py:534–547`, or change the checkpoint write to skip non-citizens, with explicit documentation of the policy.
4. **Fix Problem 3** — Based on Q7–Q9, define and implement the supervisor checkpoint/resume contract.
5. **Fix Problem 5** — Based on Q10–Q12, decide whether to await `update_experiment_info_checkpoint` or accept the fire-and-forget risk.
6. **Fix Problem 10** — Based on Q15–Q16, pass a real `expected_agent_ids` set through the resume query path.
7. **Address Problem 7** — Based on Q13–Q14, widen or document the config comparison exclusion list.
8. **Update the e2e test** — Based on Q19–Q20, extend `tests/e2e/003_resume_agent_state.py` to cover multi-type agent scenarios.
