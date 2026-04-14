# Cache Persistence
> On shutdown, serialize in-memory cache state to a pickle file named after the LLM model; on startup, reload that file if it exists so the cache survives experiment restarts.

---

## Purpose & Motivation

The `QdrantCacheActor` builds its championship model in RAM on top of vectors already persisted in Qdrant. On every `close()`, the actor calls `_rebuild_model()` for each collection to ensure the model is current, then discards it. On the next startup, `_load_existing_rows()` (`qdrant_cache.py:114`) sets `_bootstrap_rebuild_needed = True`, which schedules a cold rebuild. That rebuild requires at least `n_neighbors` Qdrant points to already exist, requires fetching up to 5 000 rows from disk, and cannot produce a cache hit until it completes.

The `GlobalDispatcherCacheActor` is simpler but shares the same problem: its `self.cache` dict (`dispatcher_cache_actor.py:12`) is pure in-memory Python and is thrown away every time the simulation exits.

Persisting both caches to pickle means:
- The Qdrant cache resumes with a warmed championship model immediately, eliminating the cold-start rebuild pass at the start of each simulation.
- The dispatcher cache carries across its accumulated block-selection votes, so agents benefit from previously observed routing consensus without replaying hundreds of ticks.

The motivation is particularly strong for iterative workflows where the same model and the same set of prompts are used across repeated short experiments — the cache is valuable the moment it exceeds the bootstrap threshold, and that value should not be thrown away every run.

---

## Success Criteria

1. After a clean simulation run, a pickle file exists at the expected path named for the LLM model (e.g. `qdrant_champion_Qwen_Qwen2_5_32B_Instruct_AWQ.pkl`).
2. A subsequent run loads that file without error; the Qdrant cache skips the bootstrap rebuild for any collection whose championship state was reloaded.
3. A subsequent run without the pickle file (or with `persist_cache: false`) starts cleanly without error — no regression for existing users.
4. If the pickle file is corrupt or incompatible (version mismatch), the actor logs a warning and falls back to cold-start without crashing.
5. The dispatcher cache pickle is similarly saved and reloaded.
6. The `data/` directory is created automatically if it does not exist.

---

## Scope

**In scope:**
- Serialize `QdrantCacheActor` championship state (per-collection `QdrantCacheChampionship` objects: `active_feature`, `max_neighbor_distance`, `last_feature_scores`, `rebuild_count`) to a pickle file inside the existing Qdrant data directory.
- Load that pickle on `QdrantCacheActor.__init__` before any `_load_existing_rows()` call, restoring championship state in-place so the bootstrap rebuild flag is suppressed.
- Serialize `GlobalDispatcherCacheActor.cache` dict to a separate pickle file.
- Load that pickle on `GlobalDispatcherCacheActor.__init__`.
- A new `persist_cache: bool` field on `QdrantCacheConfig` (default `True`) to opt out of pickle persistence.
- File naming: sanitized LLM model name for the Qdrant actor; a fixed name for the dispatcher actor (it has no model dependency).
- The pickle directory for the Qdrant actor defaults to the same directory as `qdrant_path` (already `data_dir/qdrant/` or config-overridden).
- The pickle directory for the dispatcher actor defaults to `data_dir/`.

**Out of scope:**
- Persisting the raw Qdrant vector data (that is already handled by Qdrant's on-disk storage).
- Versioned migration of pickle files across code changes.
- Encryption or signing of pickle files.
- A UI or dashboard for cache persistence state.
- Distributing the pickle file across machines (local filesystem only).
- Adding a `persist_cache` field to the dispatcher cache (it has no config; apply a sensible unconditional default, or add the flag to `QdrantCacheConfig` since the manager controls both actors).

---

## Constraints

- The Qdrant actor already receives its `qdrant_path` and `llm_model_name` at construction (`ray_actor.py:44–72`); both are available for constructing the pickle path at `__init__` time.
- `_sanitize_collection_name()` at `ray_actor.py:16` is the existing helper for producing filesystem-safe strings from model names; it must be reused for the pickle filename.
- The dispatcher actor currently accepts no constructor arguments (`dispatcher_cache_actor.py:10`). Adding a `persist_path: Optional[str]` argument will require a one-line change in `_init_dispatcher_cache_actor` (`infrastructuremanager.py:385`).
- `InfrastructureManager._init_dispatcher_cache_actor` does not currently pass `data_dir` to the actor. It must be threaded through.
- Both `close()` methods are already called in `InfrastructureManager.close()` (`infrastructuremanager.py:483–496`). No new lifecycle hook is needed.
- The `QdrantCacheConfig` Pydantic model lives at `llm/cache/config.py:6`. New fields must be added there, not inline.
- `pickle` is already used in the project (`environment/mapdata.py:3`) so no new dependency is required.

---

## Architecture & Integration Points

### QdrantCacheActor (primary target)

- `agentsociety/llm/cache/ray_actor.py:22` — `QdrantCacheActor.__init__` — receives `qdrant_path` and `llm_model_name`. **New: load pickle here.**
- `agentsociety/llm/cache/ray_actor.py:74` — `self._caches: dict[str, MultiFeatureQdrantChampionCache]` — keys are collection names. The `championship` sub-object of each entry holds the serializable in-RAM state.
- `agentsociety/llm/cache/ray_actor.py:388` — `QdrantCacheActor.close()` — already calls `_flush_buffer()` and `_rebuild_model()` on every cache. **New: pickle dump here, after rebuilding.**
- `agentsociety/llm/cache/championship.py:37` — `QdrantCacheChampionship` — four attributes to capture: `active_feature` (str or None), `max_neighbor_distance` (float or None), `last_feature_scores` (dict), `rebuild_count` (int). All are plain Python types; they pickle trivially.
- `agentsociety/llm/cache/qdrant_cache.py:61` — `self.championship = QdrantCacheChampionship(...)` — the championship is constructed at `__init__`. After construction, its state fields can be overwritten from the pickle before any data arrives.
- `agentsociety/llm/cache/qdrant_cache.py:116` — `_load_existing_rows` — sets `_bootstrap_rebuild_needed = True` if enough points exist. **The pickle load must happen before the collection is opened so this flag is never set for collections whose championship was restored.**
- `agentsociety/llm/cache/config.py:6` — `QdrantCacheConfig` — **New: `persist_cache: bool = True`**.
- `agentsociety/simulation/infrastructuremanager.py:398` — `_init_llm_cache_actor` — passes args to `QdrantCacheActor.remote(...)`. **New: pass `persist_cache` flag.**

### GlobalDispatcherCacheActor (secondary target)

- `agentsociety/agent/dispatcher_cache_actor.py:7` — `GlobalDispatcherCacheActor.__init__` — currently takes only `min_sample_size` and `agreement_threshold`. **New: add `persist_path: Optional[str] = None`; load pickle if path is provided and file exists.**
- `agentsociety/agent/dispatcher_cache_actor.py:12` — `self.cache: dict[tuple[...], dict]` — the full in-memory state. Plain Python; pickles trivially.
- `agentsociety/agent/dispatcher_cache_actor.py:55` — `close()` — currently calls `self.cache.clear()`. **New: dump pickle before clearing.**
- `agentsociety/simulation/infrastructuremanager.py:385` — `_init_dispatcher_cache_actor` — constructs the actor. **New: compute dispatcher pickle path from `self._config.env.data_dir` and pass it.**

### Config chain

```
EnvConfig.qdrant_cache (configs/env.py:79)
    → QdrantCacheConfig.persist_cache (llm/cache/config.py)  [NEW]

InfrastructureManager._init_llm_cache_actor (infrastructuremanager.py:398)
    → QdrantCacheActor.remote(..., persist_cache=cfg.persist_cache)

InfrastructureManager._init_dispatcher_cache_actor (infrastructuremanager.py:385)
    → GlobalDispatcherCacheActor.remote(..., persist_path=<data_dir>/dispatcher_cache.pkl)
```

---

## Similar Patterns & Reuse

- **`environment/mapdata.py:3` — `pickle.load` / `pickle.dump`**
  Reads and writes a large Python object to disk with `rb`/`wb` open modes and an existence check before loading. This is the exact pattern to replicate: check existence, open in `rb`, `pickle.load`; on close, open in `wb`, `pickle.dump`. No new pattern is being invented.

- **`ray_actor.py:16` — `_sanitize_collection_name(name: str) -> str`**
  Already converts any string (including model names with `/` and `.`) to `[a-zA-Z0-9_-]`. Used for Qdrant collection names. Reuse it to build the pickle filename from `llm_model_name`.

- **`ray_actor.py:57–59` — `os.makedirs(self._qdrant_path, exist_ok=True)`**
  The actor already creates its own storage directory at construction. The same pattern applies for the pickle directory — call `os.makedirs` with `exist_ok=True` before attempting to write.

- **`ray_actor.py:388–408` — `QdrantCacheActor.close()`**
  The existing `close()` already flushes buffers, rebuilds models, and writes a JSON stats file. Adding a `pickle.dump` call in the same method after the rebuild loop keeps all persistence in one place.

---

## Implementation Strategy

### Step 1 — Extend `QdrantCacheConfig` with `persist_cache`

**Before:** `llm/cache/config.py` has 7 fields ending at `skip_mode`.
**After:** Add `persist_cache: bool = Field(default=True)`. No other file changes needed for this step.

### Step 2 — Add pickle save/load to `QdrantCacheActor`

**Before:**
- `ray_actor.py:44` — `__init__` opens the Qdrant client and constructs the embedding model. No pickle logic.
- `ray_actor.py:388` — `close()` calls `_flush_buffer()`, `_rebuild_model()`, writes JSON stats.

**After:**
- Add `self._persist_cache: bool` and `self._pickle_path: str` in `__init__`. The pickle path is `os.path.join(self._qdrant_path, f"champion_{_sanitize_collection_name(llm_model_name)}.pkl")`.
- After `self._caches` is declared (line 74), call `self._load_champion_state()` — a new private method that opens the pickle if it exists, and for each `collection_name` in the pickle, calls `_get_or_create_cache(collection_name, feature_names)` then overwrites `cache.championship` attributes in-place (`active_feature`, `max_neighbor_distance`, `last_feature_scores`, `rebuild_count`). If the collection does not yet exist in Qdrant (it will be created lazily on first record), the championship state is stored aside and applied when the cache is first touched.
- In `close()`, after the rebuild loop and before writing the JSON stats, call `self._save_champion_state()` — a new private method that collects `{collection_name: {feature_names, championship_state_dict}}` for every cache in `self._caches` and calls `pickle.dump`. The directory is guaranteed to exist (created at `__init__` line 57).

**Callers unchanged:** `_get_or_create_cache` (`ray_actor.py:210`) calls `cache.consume_bootstrap_rebuild_flag()`. If the championship state was already restored, the flag will never be set, so the rebuild is suppressed.

**Key detail about bootstrap suppression:** `_load_existing_rows` (`qdrant_cache.py:114`) sets `_bootstrap_rebuild_needed` only if the collection has enough points. If we restore championship state from pickle, the model is already ready (`model_ready()` checks `active_feature is not None`). We must also ensure the restored state does not conflict with `_bootstrap_rebuild_needed`. The cleanest approach: after writing championship attributes, also set `cache._bootstrap_rebuild_needed = False` explicitly.

### Step 3 — Add pickle save/load to `GlobalDispatcherCacheActor`

**Before:**
- `dispatcher_cache_actor.py:10` — `__init__(self, min_sample_size, agreement_threshold)`.
- `dispatcher_cache_actor.py:55` — `close()` clears the cache dict.

**After:**
- Add `persist_path: Optional[str] = None` to `__init__`. Store as `self._persist_path`.
- At end of `__init__`, call `self._load_cache()` — load pickle from `persist_path` if it exists and is not empty.
- In `close()`, before `self.cache.clear()`, call `self._save_cache()` — dump `self.cache` to pickle at `self._persist_path` if it is set.

### Step 4 — Wire persist path into `InfrastructureManager`

**Before:**
- `infrastructuremanager.py:385` — `GlobalDispatcherCacheActor.remote()` called with no args beyond defaults.
- `infrastructuremanager.py:398` — `QdrantCacheActor.remote(...)` called without `persist_cache`.

**After:**
- In `_init_dispatcher_cache_actor` (`infrastructuremanager.py:385`): compute `dispatcher_pickle_path = os.path.join(self._config.env.data_dir, "dispatcher_cache.pkl")` and pass `persist_path=dispatcher_pickle_path` to `GlobalDispatcherCacheActor.remote(...)`.
- In `_init_llm_cache_actor` (`infrastructuremanager.py:398`): pass `persist_cache=cfg.persist_cache` to `QdrantCacheActor.remote(...)`.

No other callers need to change. `LLM`, `AgentManager`, and all block files are unaffected.

---

## Trade-Offs

| Gained | Sacrificed / Risked |
|---|---|
| Qdrant cache is warm immediately on restart; no rebuild latency at tick 1 | Pickle files can become stale if Qdrant data is deleted manually without deleting the pickle |
| Dispatcher cache retains accumulated vote counts across runs | `pickle` is not version-safe: a code change to `QdrantCacheChampionship` or the cache dict structure will silently produce wrong behaviour if the pickle format is not validated |
| Zero regression for users who set `persist_cache: false` | Adds two new I/O operations to `close()` (mitigated: they are sequential and at shutdown, not on the hot path) |
| Uses existing `pickle` infrastructure already present in `mapdata.py` | The pickle file is tied to `qdrant_path`, which means it moves if the user changes `qdrant_cache.path` — old pickle would not be found |

---

## Rejected Approaches

- **Approach: Use `joblib.dump` / `joblib.load` instead of `pickle`.**
  **Why rejected:** `joblib` is not a declared dependency. `pickle` is already used in `environment/mapdata.py:3` and is sufficient for the small dict structures being serialized. No need to add a dependency.

- **Approach: Store championship state in the Qdrant collection metadata / payload.**
  **Why rejected:** Qdrant's payload is per-point; collection-level metadata is not a first-class concept in `qdrant-client`. Reading all points to reconstruct the state is exactly what the existing `_rebuild_model` already does, which is what this feature aims to avoid.

- **Approach: Add a `save()` / `load()` method to `QdrantCacheChampionship` for self-serialization.**
  **Why rejected:** `QdrantCacheChampionship` is a pure in-process value object with no knowledge of the filesystem. Keeping I/O out of it maintains the clean separation already present in the architecture. The `QdrantCacheActor` is the correct owner of persistence decisions.

- **Approach: Persist at every `_rebuild_model()` call (i.e., after every batch flush), not only at `close()`.**
  **Why rejected:** Rebuilds happen frequently during a simulation run (every `batch_size` records). Writing a pickle on every rebuild would add per-batch I/O on the hot path. Shutdown-only persistence is a good trade: worst case is losing the state of the last partial batch if the process crashes, which is the same situation as today.

- **Approach: Add a new `data/` subdirectory distinct from `qdrant_path`.**
  **Why rejected:** The `qdrant_path` directory is already created and managed by the actor itself (line 57 of `ray_actor.py`). Placing the pickle alongside the Qdrant data keeps them co-located; deleting the cache directory removes both atomically. A separate `data/` path would require the user to manage two directories.

---

## Assumptions & Open Questions

1. **Version compatibility sentinel.** The plan relies on a `try/except` around `pickle.load` with a warning + fallback on any error. No explicit version field is added to the pickle payload. If the `QdrantCacheChampionship` dataclass structure changes in future work, the fallback will silently trigger. An explicit version key in the pickle dict (e.g. `{"version": 1, "state": ...}`) would make this safer. This is left as an open question for the implementor.

2. **Multi-model setups.** `InfrastructureManager._init_llm_cache_actor` takes the model name from `self._config.llm[0].model` (line 424 of `infrastructuremanager.py`). If a run uses multiple LLM configs (load-balanced across models), only the first model's name is used to scope the cache. The same simplification applies to the pickle filename. This is consistent with existing behaviour and documented as a known limitation.

3. **Dispatcher cache naming.** The dispatcher cache is model-agnostic (it maps `(possible_blocks, intention)` → `block_name`, not LLM outputs). The filename `dispatcher_cache.pkl` is fixed. If the set of agents or blocks changes across runs, the loaded cache may contain stale or irrelevant entries. The existing `min_sample_size` and `agreement_threshold` checks in `check_cache` (`dispatcher_cache_actor.py:18`) mean stale entries are unlikely to cause wrong routing, but they waste memory. This is acceptable for the current scope.

4. **`IndividualEngine` scope.** `IndividualEngine` (`simulation/individualengine.py`) does not use `InfrastructureManager` and does not instantiate either cache actor. This feature is therefore scoped to `SimulationEngine` only. If `IndividualEngine` later gains cache support, the same persistence pattern applies.

5. **Atomic write.** The plan does not specify an atomic write (write to a `.tmp` file then rename). A crash mid-write would leave a corrupt pickle file that triggers the fallback on the next run. If robustness to mid-write crashes is required, a `tempfile` + `os.replace` pattern (as used in the mapdata path) should be adopted. Left as an open question for the implementor.

---

## Code That Could Be Refactored *(informational)*

- `agentsociety/agent/dispatcher_cache_actor.py:55` — `close()` calls `self.cache.clear()`. After adding pickle persistence, clearing the in-memory dict is no longer strictly necessary (the actor is about to be garbage collected). The clear is harmless but could be removed for clarity.
- `agentsociety/llm/cache/ray_actor.py:74–81` — The eight `self._*` dicts/sets are all `defaultdict(int)` or plain `dict`. If the actor is ever extended to support warm reload of hit/miss counts across experiments, these should be included in the pickle. Currently they are intentionally left out (counts are per-experiment, not cumulative across runs).

---

## Proposed Next Steps

1. Add `persist_cache: bool = Field(default=True)` to `QdrantCacheConfig` at `agentsociety/llm/cache/config.py`.
2. Implement `_save_champion_state()` and `_load_champion_state()` private methods on `QdrantCacheActor` at `agentsociety/llm/cache/ray_actor.py`, and call them from `close()` and `__init__` respectively.
3. Add `persist_path: Optional[str] = None` to `GlobalDispatcherCacheActor.__init__` at `agentsociety/agent/dispatcher_cache_actor.py`, and add `_save_cache()` / `_load_cache()` private helpers called from `close()` / `__init__`.
4. Thread `persist_cache` and `dispatcher_pickle_path` through `InfrastructureManager._init_llm_cache_actor` and `_init_dispatcher_cache_actor` at `agentsociety/simulation/infrastructuremanager.py`.
5. Validate with the existing e2e test `tests/e2e/006_qdrant_cache.py` by running two consecutive simulations and asserting the second run's cache hits a collection whose championship state was loaded from pickle (i.e., `rebuild_count` starts at the value from the first run rather than 0).
