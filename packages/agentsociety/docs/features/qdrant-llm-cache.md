# Qdrant-Backed LLM Semantic Cache (Ray Actor)
> A Ray actor that intercepts eligible LLM calls, uses a multi-feature Qdrant championship algorithm to return cached responses when confidence is high, and collects prompt/response pairs as labeled training data.

---

## Implementation Status (as of 2026-04-12)

All 10 original implementation steps are **complete** as of commit `6464b53` ("feat: codex implementation of qdrant cache system (to be improved)").

**One significant design divergence from the original plan exists** — see "Shadow-Validation vs. Skip Mode" below. This divergence affects success criteria and is resolved by the new Step 11 below: adding a `skip_mode` config field that lets callers opt into real skip behavior without changing the existing default.

**One structural decision was made after initial implementation** — see "Step 13: Move cache files to `llm/cache/` subfolder" below. The two flat files `llm/qdrant_cache_actor.py` and `llm/qdrant_cache_config.py` are being reorganised into a proper subpackage.

**One new design decision (2026-04-12)** — see "Step 14: Include LLM model name in collection name" below. The Qdrant collection name must encode the LLM model so that cached results from one model are never served to a different model.

---

## Purpose & Motivation

The simulation runs hundreds of agents in parallel, each making dozens of LLM calls per tick. Many prompts are structurally near-identical across agents (same block, same situation, slightly different numeric state). The LLM call is the dominant cost — both latency and API spend.

This feature builds a **semantic similarity cache** that:
1. Embeds the text-type input fields declared in each prompt TOML separately.
2. Uses the championship algorithm to select the best-performing feature vector and return cached labels when confidence is high.
3. Falls back to the live LLM on cache misses, records the label, and periodically rebuilds the KNN model.
4. Collects all prompt+label pairs as labeled training data for future fine-tuning.

The cache only applies to prompts whose TOML declares `[outputs]` with all-categorical or all-numeric output fields. Prompts with free-text outputs are excluded from response serving — they are recorded as dataset samples only.

---

## Success Criteria

- Cache actor starts and stops cleanly alongside other Ray actors in `InfrastructureManager`.
- **For eligible prompts, a cache hit short-circuits the live LLM call and returns the cached label without paying LLM cost.** Achieved when `skip_mode=True` (Step 11). Shadow-validation mode remains the default.
- Probe latency is logged each call so its cost is observable.
- Hit/miss counters are written to a JSON file on `close()` and emitted to Prometheus when monitoring is enabled.
- All prompt TOML files have `[outputs]` sections so the cache can decide eligibility at load time.
- Feature is opt-in: disabled by default, zero impact on existing runs unless `env.qdrant_cache.enabled: true` is set.
- An end-to-end test in `tests/e2e/006_qdrant_cache.py` asserts that after 51+ near-identical prompts are submitted, at least one call returns a cached result (functional cache hit via `get_stats()`).
- **Collections are model-scoped: a collection built with model A is never queried when the active LLM model is model B.** Verified by inspection of collection names in `stats.json` (Step 14).

---

## Scope

**In scope:**
- `agentsociety/llm/cache/qdrant_cache.py` — pure Python cache system: `MultiFeatureQdrantChampionCache` class (KNN championship logic, Qdrant storage, no Ray dependency). **[DONE — currently at `llm/qdrant_cache_actor.py:22`; Step 13 moves it here]**
- `agentsociety/llm/cache/ray_actor.py` — Ray actor wrapper: `QdrantCacheActor` (`@ray.remote` class wrapping `MultiFeatureQdrantChampionCache`). **[DONE — currently at `llm/qdrant_cache_actor.py:364`; Step 13 moves it here]**
- `agentsociety/llm/cache/config.py` — Pydantic config: `QdrantCacheConfig`. **[DONE — currently at `llm/qdrant_cache_config.py`; Step 13 moves it here]**
- `agentsociety/llm/cache/__init__.py` — re-exports for clean imports. **[NEW — Step 13 creates it]**
- `LLMContext` TypedDict extended with: `prompt_identity`, `prompt_inputs`, `prompt_input_schema`, `prompt_output_schema`. **[DONE — note: plan specified 2 new fields; implementation added 4]**
- `PromptManager` exposes output schema and identity. **[DONE]**
- `LLM.atext_request` probes and records via the cache actor when context carries `prompt_identity`. **[DONE — currently in shadow-validation mode; skip mode gated by new `skip_mode` field]**
- Wire-up in `InfrastructureManager`. **[DONE]**
- Cache config in `EnvConfig`. **[DONE]**
- `[outputs]` sections in all 33 eligible prompt TOML files. **[DONE]**
- Cache hit/miss and hit-validation metrics in `PrometheusActor` / `MetricsTracker`. **[DONE]**
- Stats persistence: JSON file on `close()`. **[DONE]**
- `QdrantCacheActor` and `QdrantCacheConfig` exported from `agentsociety/llm/__init__.py`. **[DONE — exports will be preserved via `llm/cache/__init__.py` re-export chain after Step 13]**
- **Step 11: `skip_mode: bool` field on `QdrantCacheConfig` and corresponding branch in `LLM._maybe_serve_probe_result()`. [PENDING]**
- **Step 12: End-to-end test `tests/e2e/006_qdrant_cache.py` wired into `tests/run_e2e_tests.sh`. [PENDING]**
- **Step 13: Reorganise `llm/qdrant_cache_actor.py` and `llm/qdrant_cache_config.py` into the `llm/cache/` subpackage. [PENDING]**
- **Step 14: Include LLM model name in the Qdrant collection name. [PENDING]**

**Out of scope:**
- Multi-machine / distributed Qdrant (local path only).
- Caching tool-call responses (calls where `tools=...` is passed are skipped).
- A UI or dashboard for cache stats.
- Disk eviction / capacity management (unlimited for now).
- Changing the existing `prompt_responses` table in ClickHouse.
- Automatic migration of existing on-disk collections to the new model-scoped naming scheme (users with pre-Step-14 caches get a fresh empty cache — acceptable, documented in Trade-Offs).

---

## Constraints

- `qdrant-client[fastembed]>=1.12.1` is already declared in `pyproject.toml`. No new package dependency required.
- Dense embedding model: `BAAI/bge-small-en-v1.5` (384-dim via fastembed). Same library already used for sparse BM25 in `InfrastructureManager._init_embedding()`.
- The actor must be a Ray remote actor (agents run in isolated Ray actors and cannot share Python objects).
- The actor must not call back into the LLM (infinite-loop risk).
- `LLMContext` uses `TypedDict(total=False)`, so adding fields is backward-compatible.
- Qdrant path defaults to `<data_dir>/qdrant/`, where `data_dir` is `EnvConfig.data_dir` (`configs/env.py:56`). Configurable via `env.qdrant_cache.path` override.
- Collection names must be unique per (prompt, model) pair. Qdrant collection names allow `[a-zA-Z0-9_-]` only; slashes and dots in model identifiers must be sanitised. The existing `_sanitize_collection_name()` helper (`qdrant_cache_actor.py:18`) already applies `re.sub(r"[^a-zA-Z0-9_-]", "_", name)` and is sufficient for this purpose.

---

## Architecture & Integration Points

```
Block._make_llm_context(prompt_name, state_dict, ...)
    → LLMContext with:
        prompt_identity        = PromptManager.get_prompt_identity(prompt_name)
        prompt_inputs          = {field: value for typed fields in state_dict}
        prompt_input_schema    = PromptManager.get_input_schema(prompt_name)
        prompt_output_schema   = PromptManager.get_output_schema(prompt_name)

LLM.atext_request(dialog, ..., context=LLMContext):
    _should_probe_cache() → True if cache_actor set, prompt_identity present, not a tool call
    _probe_semantic_cache() → calls cache_actor.query_and_maybe_serve.remote(...)

    [skip_mode=False — default / shadow-validation]
    live LLM call always happens
    _maybe_serve_probe_result() → if probe hit AND live result matches, return cached value

    [skip_mode=True]
    if probe hit → return cached value immediately (LLM skipped)
    else → live LLM call, then _record_cache_miss()
```

Integration point citations (all confirmed present in code):

- `agentsociety/llm/llm.py:33` — `LLMContext(TypedDict, total=False)` has `prompt_identity`, `prompt_inputs`, `prompt_input_schema`, `prompt_output_schema`.
- `agentsociety/llm/llm.py:115` — `LLM.__init__` accepts `cache_actor: Optional[Any] = None`.
- `agentsociety/llm/llm.py:197` — `_should_probe_cache()` helper.
- `agentsociety/llm/llm.py:209` — `_probe_semantic_cache()` — awaited before the live LLM call.
- `agentsociety/llm/llm.py:296` — `_maybe_serve_probe_result()` — shadow-validation comparison; returns cached value only when probe hit AND normalized outputs match live result. **Step 11 adds a skip-mode branch here (or just before the `while True:` loop at `llm.py:437`).**
- `agentsociety/llm/llm.py:321` — `_record_cache_miss()` — fire-and-forget record to actor.
- `agentsociety/llm/llm.py:424` — probe executed before `while True:` loop; `cache_hit_probe` set here.
- `agentsociety/llm/llm.py:437` — `while True:` retry loop begins; **Step 11 inserts an early-return guard between line 434 and 437**.
- `agentsociety/agent/block.py:174` — `Block._make_llm_context()` populates all four context keys using `PromptManager`.
- `agentsociety/cityagent/societyagent.py:241` — `SocietyAgent._build_context()` does the same for agent-level calls.
- `agentsociety/prompts/prompt_manager.py:156` — `get_prompt_identity(name)` → `(name, origin, version)`.
- `agentsociety/prompts/prompt_manager.py:165` — `get_input_schema(name)` → `{field: {type, ...}}`.
- `agentsociety/prompts/prompt_manager.py:176` — `get_typed_input_fields(name)`.
- `agentsociety/prompts/prompt_manager.py:188` — `get_text_input_fields(name)`.
- `agentsociety/prompts/prompt_manager.py:201` — `get_output_schema(name)` → `{field: {type, ...}}`.
- `agentsociety/prompts/prompt_manager.py:208` — `is_cache_eligible(name)`.
- `agentsociety/simulation/infrastructuremanager.py:56` — `self._llm_cache_actor`.
- `agentsociety/simulation/infrastructuremanager.py:60` — `self._llm_cache_tool`.
- `agentsociety/simulation/infrastructuremanager.py:109` — `llm_cache_tool` property.
- `agentsociety/simulation/infrastructuremanager.py:398` — `_init_llm_cache_actor()`.
- `agentsociety/simulation/infrastructuremanager.py:477` — called in `initialize_all()`.
- `agentsociety/simulation/infrastructuremanager.py:439` — `LLM(...)` receives `cache_actor=self._llm_cache_actor`.
- `agentsociety/simulation/infrastructuremanager.py:489` — `close()` awaits `_llm_cache_actor.close.remote()`.
- `agentsociety/simulation/simulationengine.py:157` — `_llm_cache_tool` retrieved from infrastructure manager.
- `agentsociety/simulation/simulationengine.py:203` — `llm_cache_tool` added to `agent_toolbox`.
- `agentsociety/configs/env.py:79` — `EnvConfig.qdrant_cache: QdrantCacheConfig`.
- `agentsociety/performance/prometheusActor.py:68` — `record_cache_stats(prompt_name, hit)`.
- `agentsociety/performance/prometheusActor.py:72` — `record_cache_hit_validation(prompt_name, right)`.
- `agentsociety/performance/MetricsTracker.py:19` — `cache_hits` Prometheus Counter.
- `agentsociety/performance/MetricsTracker.py:25` — `cache_misses` Prometheus Counter.
- `agentsociety/performance/MetricsTracker.py:31` — `cache_hit_right` / `cache_hit_wrong` Counters.
- `agentsociety/llm/__init__.py:4` — `QdrantCacheActor` and `QdrantCacheConfig` exported (currently from flat files; after Step 13, re-exported through `llm/cache/__init__.py`).

### Collection naming (current vs. after Step 14)

The Qdrant collection name is constructed by `QdrantCacheActor._collection_name()` at `agentsociety/llm/qdrant_cache_actor.py:399–402` (this method moves to `llm/cache/ray_actor.py` after Step 13):

```python
# CURRENT (qdrant_cache_actor.py:399)
def _collection_name(self, prompt_identity: tuple[str, str, str]) -> str:
    name, origin, version = prompt_identity
    raw = f"{name}__{origin}__{version}"
    return _sanitize_collection_name(raw)
```

After Step 14, the method becomes model-aware. The model name is stored as `self._llm_model_name` (set in `QdrantCacheActor.__init__` from a new `llm_model_name: str` constructor parameter):

```python
# AFTER Step 14
def _collection_name(self, prompt_identity: tuple[str, str, str]) -> str:
    name, origin, version = prompt_identity
    raw = f"{name}__{origin}__{version}__{self._llm_model_name}"
    return _sanitize_collection_name(raw)
```

`_sanitize_collection_name()` at `qdrant_cache_actor.py:18` replaces every character outside `[a-zA-Z0-9_-]` with `_`. A model string like `gpt-4o` becomes `gpt-4o` (already clean). A model string like `meta-llama/Llama-3-8b-instruct` becomes `meta-llama_Llama-3-8b-instruct` (slash replaced). No additional sanitisation logic is needed.

Example collection names after Step 14:

| Prompt name | Model | Collection name |
|---|---|---|
| `needs_evaluation` / `citysim` / `1.0` | `gpt-4o` | `needs_evaluation__citysim__1_0__gpt-4o` |
| `needs_evaluation` / `citysim` / `1.0` | `meta-llama/Llama-3-8b-instruct` | `needs_evaluation__citysim__1_0__meta-llama_Llama-3-8b-instruct` |

---

## Key Design Divergence: Shadow-Validation Mode vs. Skip Mode

### What the plan specified

The original plan described a **skip mode**: if `query_and_maybe_serve()` returns a result, `atext_request` returns it immediately without calling the live LLM. This is how cost savings are achieved.

```
plan: probe → hit? → return cached value (LLM skipped)
```

### What was implemented

The implementation uses a **shadow-validation mode**: the probe runs before the `while True:` loop, but the live LLM is **always called regardless of probe result**. Only after the live LLM succeeds is `_maybe_serve_probe_result()` (`llm.py:296`) invoked. It returns the cached value only if the cache probe hit AND the normalized cached output matches the live output.

```
actual: probe → [LLM always called] → hit AND match? → return cached value, else return live
```

This means:
- **Zero LLM cost savings.** Every request still pays LLM latency and API cost.
- **The probe adds latency on top of the LLM call** rather than replacing it.
- The cache hit metric (`record_cache_stats(..., hit=True)`) fires when the probe hits, before the live result is available — meaning it records speculative hits, not actual serving events.
- The `cache_hit_validation` metric (`record_cache_hit_validation`) does track actual correctness of probe hits.

### Resolution: `skip_mode` config field (Step 11)

Rather than changing the default behavior (which would be a breaking change for anyone relying on shadow-validation correctness logging), the resolution is to add `skip_mode: bool = False` to `QdrantCacheConfig`. When `skip_mode=True`, a cache hit short-circuits the LLM call entirely. When `skip_mode=False` (the default), the existing shadow-validation path is preserved.

The `LLM` class receives the cache config (or just the `skip_mode` flag) at construction time so `atext_request` can branch accordingly.

---

## Similar Patterns & Reuse (implemented)

- **`agentsociety/agent/dispatcher_cache_actor.py:8 — GlobalDispatcherCacheActor`** — Ray actor boilerplate used as template for `QdrantCacheActor`.
- **`agentsociety/simulation/infrastructuremanager.py:376 — _init_dispatcher_cache_actor()`** — structural template for `_init_llm_cache_actor()`.
- **`agentsociety/prompts/prompt_manager.py:152 — get_required_fields()`** — pattern used for the new `get_prompt_identity()`, `get_input_schema()`, `get_output_schema()`.

---

## Implementation Strategy

### Steps 1–10: Complete

All 10 steps from the original plan are complete in commit `6464b53`. Summary:

| Step | Description | Status | Notes |
|---|---|---|---|
| 1 | `[outputs]` sections in all 33 TOML files | Done | 33 TOMLs have outputs; 1 (block_dispatcher) intentionally excluded |
| 2 | `QdrantCacheConfig` + `EnvConfig.qdrant_cache` | Done | `configs/env.py:79` |
| 3 | `QdrantCacheActor` in `llm/qdrant_cache_actor.py` | Done | 629 lines; includes `MultiFeatureQdrantChampionCache` |
| 4 | `LLMContext` extended + `LLM.atext_request` probe/record | Done | Shadow-validation mode (see divergence above) |
| 5 | `PromptManager` new methods | Done | 6 new methods added |
| 6 | Block call sites pass `prompt_identity` etc. | Done | Central helper in `Block` and `SocietyAgent`; blocks use it |
| 7 | `InfrastructureManager` wiring | Done | `_init_llm_cache_actor()` + init/close lifecycle |
| 8 | `llm_cache_tool` added to agent toolbox | Done | `simulationengine.py:203` |
| 9 | Prometheus metrics | Done | `MetricsTracker` has 4 new counters |
| 10 | `__init__.py` exports | Done | `llm/__init__.py` exports both classes |

### Step 11: Add `skip_mode` to `QdrantCacheConfig` and wire into `LLM`

**What changes:**

**Before — `agentsociety/llm/qdrant_cache_config.py` (current path; `llm/cache/config.py` after Step 13):**
```python
class QdrantCacheConfig(BaseModel):
    enabled: bool = Field(default=False)
    path: Optional[str] = Field(default=None)
    probability_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    batch_size: int = Field(default=1000, ge=1)
    n_neighbors: int = Field(default=50, ge=1)
    distance_quantile: float = Field(default=0.95, ge=0.0, le=1.0)
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_cache_dir: Optional[str] = Field(default=None)
```

**After — add one field:**
```python
    skip_mode: bool = Field(default=False)
```

**Before — `agentsociety/llm/llm.py:115`:** `LLM.__init__` accepts `cache_actor: Optional[Any] = None` but does not accept a cache config object.

**After:** Pass `cache_skip_mode: bool = False` as a new constructor parameter (or pass the full `QdrantCacheConfig`). Store it as `self._cache_skip_mode`. The constructor call site is `agentsociety/simulation/infrastructuremanager.py:439`.

**Before — `agentsociety/llm/llm.py:424–437`:** After the probe, the code falls straight into `while True:` regardless of `cache_hit_probe`.

**After — insert between line 434 and 437:**
```python
# Skip mode: if probe hit, return immediately without calling LLM.
if self._cache_skip_mode and cache_hit_probe and probe_result is not None:
    if isinstance(probe_result, str):
        return probe_result
    return json.dumps(probe_result, ensure_ascii=True)
```

This is a 4-line insertion. The shadow-validation path in `_maybe_serve_probe_result()` (`llm.py:296`) is untouched; it remains active when `skip_mode=False`.

**What calls it:** `InfrastructureManager._init_llm_cache_actor()` (`infrastructuremanager.py:398`) constructs the `LLM` instance at `infrastructuremanager.py:439`. It already has access to `self._config.env.qdrant_cache`, so passing `cache_skip_mode=self._config.env.qdrant_cache.skip_mode` is a one-word addition.

### Step 12: End-to-end test `tests/e2e/006_qdrant_cache.py`

See the Test Plan section below for the full specification. The test file is added to `tests/e2e/` and a corresponding run line is added to `tests/run_e2e_tests.sh`.

### Step 13: Reorganise `llm/cache/` subpackage

#### Motivation

`llm/qdrant_cache_actor.py` (629 lines) contains two logically distinct classes — the pure-Python championship cache and the Ray actor wrapper — in one file. Splitting them by responsibility makes each easier to test, read, and extend. Placing both under `llm/cache/` keeps the cache implementation self-contained and avoids polluting the `llm/` namespace.

#### Current file layout (before Step 13)

```
agentsociety/llm/
    __init__.py                   # exports QdrantCacheActor, QdrantCacheConfig
    llm.py
    qdrant_cache_actor.py         # MultiFeatureQdrantChampionCache (line 22) + QdrantCacheActor (line 364)
    qdrant_cache_config.py        # QdrantCacheConfig
```

#### Target file layout (after Step 13)

```
agentsociety/llm/
    __init__.py                   # unchanged public API — re-exports via llm/cache/__init__.py
    llm.py
    cache/
        __init__.py               # re-exports: QdrantCacheActor, QdrantCacheConfig, MultiFeatureQdrantChampionCache
        qdrant_cache.py           # MultiFeatureQdrantChampionCache only (no ray import)
        ray_actor.py              # QdrantCacheActor (@ray.remote wrapper)
        config.py                 # QdrantCacheConfig (Pydantic model)
```

#### Class-to-file mapping

| Class | Source line (current file) | Target file |
|---|---|---|
| `MultiFeatureQdrantChampionCache` | `llm/qdrant_cache_actor.py:22` | `llm/cache/qdrant_cache.py` |
| `_sanitize_collection_name` (module-level helper) | `llm/qdrant_cache_actor.py:18` | `llm/cache/qdrant_cache.py` (used by both classes; lives alongside the class it primarily serves) |
| `QdrantCacheActor` | `llm/qdrant_cache_actor.py:364` | `llm/cache/ray_actor.py` |
| `QdrantCacheConfig` | `llm/qdrant_cache_config.py:6` | `llm/cache/config.py` |

#### `llm/cache/__init__.py` content

```python
"""Qdrant-backed LLM semantic cache — public re-exports."""

from .config import QdrantCacheConfig
from .qdrant_cache import MultiFeatureQdrantChampionCache
from .ray_actor import QdrantCacheActor

__all__ = [
    "MultiFeatureQdrantChampionCache",
    "QdrantCacheActor",
    "QdrantCacheConfig",
]
```

#### `llm/cache/ray_actor.py` import change

`ray_actor.py` imports `MultiFeatureQdrantChampionCache` from the sibling module rather than from the same file:

```python
from .qdrant_cache import MultiFeatureQdrantChampionCache, _sanitize_collection_name
```

The relative import to the logger (`from ..logger import get_logger`) becomes `from ...logger import get_logger` (one extra level up because the file moves into the `cache/` subdirectory).

#### `llm/cache/qdrant_cache.py` import change

Similarly, `from ..logger import get_logger` becomes `from ...logger import get_logger`.

#### `llm/__init__.py` — no public API change

The existing exports in `agentsociety/llm/__init__.py` (lines 4–5) change their source module but the exported names stay identical:

**Before:**
```python
from .qdrant_cache_actor import QdrantCacheActor
from .qdrant_cache_config import QdrantCacheConfig
```

**After:**
```python
from .cache import QdrantCacheActor, QdrantCacheConfig
```

#### Files that import from the old paths — all changes required

| File | Current import | Required change |
|---|---|---|
| `agentsociety/llm/__init__.py:4-5` | `from .qdrant_cache_actor import QdrantCacheActor` / `from .qdrant_cache_config import QdrantCacheConfig` | `from .cache import QdrantCacheActor, QdrantCacheConfig` |
| `agentsociety/configs/env.py:6` | `from ..llm.qdrant_cache_config import QdrantCacheConfig` | `from ..llm.cache.config import QdrantCacheConfig` |
| `agentsociety/simulation/infrastructuremanager.py:20` | `from ..llm import LLM, QdrantCacheActor` | No change — `QdrantCacheActor` is still exported from `..llm` |

`infrastructuremanager.py` imports `QdrantCacheActor` through `agentsociety/llm/__init__.py`, not directly from the flat file, so it requires no import-path change. Only `configs/env.py` imports `QdrantCacheConfig` from the flat file path directly and must be updated.

#### Old files to delete

After Step 13 is complete and all imports are updated:
- `agentsociety/llm/qdrant_cache_actor.py` — deleted
- `agentsociety/llm/qdrant_cache_config.py` — deleted

#### Step 11 interaction

If Step 11 (adding `skip_mode`) is implemented before Step 13, the `skip_mode` field is added to `llm/qdrant_cache_config.py` and then that file is moved to `llm/cache/config.py` as part of Step 13 — no conflict. If Step 13 runs first, add `skip_mode` to the new `llm/cache/config.py`. Either order is safe.

### Step 14: Include LLM model name in Qdrant collection name

#### Problem

The current collection name scheme (`<name>__<origin>__<version>`) is scoped only to the prompt identity. Two simulation runs that use different LLM models but the same prompt identity will share a single Qdrant collection. Cached responses from model A will be served to model B — incorrect, because different models produce different output distributions for the same input.

#### What changes

**File:** `agentsociety/llm/qdrant_cache_actor.py:399–402` (this method lives at `llm/cache/ray_actor.py:_collection_name()` after Step 13).

**Before (current code at `qdrant_cache_actor.py:399`):**
```python
def _collection_name(self, prompt_identity: tuple[str, str, str]) -> str:
    name, origin, version = prompt_identity
    raw = f"{name}__{origin}__{version}"
    return _sanitize_collection_name(raw)
```

**After:**
```python
def _collection_name(self, prompt_identity: tuple[str, str, str]) -> str:
    name, origin, version = prompt_identity
    raw = f"{name}__{origin}__{version}__{self._llm_model_name}"
    return _sanitize_collection_name(raw)
```

#### Where `_llm_model_name` comes from

The model name is available at `LLMConfig.model` (`agentsociety/llm/llm.py:80`). `LLM.__init__` receives `configs: List[LLMConfig]` (`llm.py:111`) and stores them as `self.configs` (`llm.py:132`). A round-robin load-balanced `LLM` instance may hold multiple configs, but in practice all configs in a single `LLM` instance represent the same model (they differ by API key / concurrency slot, not by model). The model name for collection naming is taken from `configs[0].model`.

The `QdrantCacheActor.__init__` currently receives no model name (`qdrant_cache_actor.py:368–376`). A new `llm_model_name: str` parameter is added to its constructor. The actor stores it as `self._llm_model_name`.

#### Sanitisation

`_sanitize_collection_name()` at `qdrant_cache_actor.py:18` uses `re.sub(r"[^a-zA-Z0-9_-]", "_", name)`. This handles all problematic characters in model identifiers:

| Character | Example source | Result |
|---|---|---|
| `/` | `meta-llama/Llama-3-8b-instruct` | replaced with `_` |
| `.` | `gpt-4.5` | replaced with `_` |
| `:` | hypothetical `provider:model` | replaced with `_` |
| `-` | `gpt-4o` | kept as-is (allowed) |

No additional sanitisation logic is needed.

#### Constructor call site

`QdrantCacheActor` is instantiated in `InfrastructureManager._init_llm_cache_actor()` at `agentsociety/simulation/infrastructuremanager.py:398`. The `InfrastructureManager` already holds the full LLM configs via `self._config` (the simulation config object). The model name is passed as:

```python
llm_model_name=self._config.llm[0].model
```

(or whichever attribute path resolves to the `LLMConfig.model` field for the primary LLM config in the infrastructure manager's config object — confirm the exact attribute path before implementing.)

#### Migration note: existing on-disk collections

Users who have run the cache before Step 14 will have collections named without the model suffix (e.g., `needs_evaluation__citysim__1_0`). After Step 14, the new name includes the model (e.g., `needs_evaluation__citysim__1_0__gpt-4o`). The old collection is not renamed or read — it is simply ignored. The new collection starts empty and warms up from scratch. This is an acceptable tradeoff: the cache is a performance optimisation, not a source of truth. Losing the warm state costs a few hundred requests until the new collection crosses the `n_neighbors` threshold. No data is corrupted.

Users who want to preserve warm state manually can rename the old Qdrant collection directory, but this is not automated and not documented as a supported migration path.

#### Step 13 interaction

- If Step 14 is implemented before Step 13: add `llm_model_name: str` to `QdrantCacheActor.__init__` in `llm/qdrant_cache_actor.py:368`. The parameter and `self._llm_model_name` assignment move to `llm/cache/ray_actor.py` as part of Step 13 — no conflict.
- If Step 13 runs first: add `llm_model_name: str` to `llm/cache/ray_actor.py:QdrantCacheActor.__init__` directly.

Either order is safe.

---

### Notable implementation details that differ from the original plan

1. **`LLMContext` gained 4 fields instead of 2.** Plan specified `prompt_identity` and `prompt_inputs`. Implementation also added `prompt_input_schema` and `prompt_output_schema`. These are passed to `query_and_maybe_serve()` and `record()`, allowing the actor to interpret field types without consulting TOML files directly.

2. **`query_and_maybe_serve()` signature changed.** Plan: `(prompt_identity, prompt_inputs, output_schema)`. Actual: `(prompt_identity, prompt_inputs, input_schema, output_schema)`. The `input_schema` parameter was added to enable typed embedding (numeric fields get scalar encoding; text fields get dense embedding).

3. **`record()` signature changed.** Plan: `(prompt_identity, prompt_inputs, llm_response)`. Actual: `(prompt_identity, prompt_inputs, input_schema, llm_response, output_schema)`.

4. **Shadow-validation mode.** The live LLM is always called by default. Opt-in skip behavior is now provided by `skip_mode=True` (Step 11).

5. **`cache_hit_validation` metric added.** Not in original plan. Records whether each probe hit that went through shadow-validation actually matched the live result. This is a useful correctness signal.

6. **Numeric fields get scalar encoding, not text embedding.** `_encode_numeric_field()` (`qdrant_cache_actor.py:426`, moving to `llm/cache/ray_actor.py` after Step 13) encodes numeric inputs as a 1-D float array `[value]` rather than embedding the string. This uses Qdrant named vectors with size=1 for numeric features. This is a significant design detail absent from the original plan.

---

## Trade-Offs

| Gain | Cost / Risk |
|---|---|
| Full architecture is in place; `skip_mode` is a small, isolated addition to `QdrantCacheConfig` and `llm.py` | Shadow-validation mode means zero cost savings until `skip_mode=True` is set |
| Shadow-validation provides a correctness signal before committing to real skipping | Every request pays probe latency on top of LLM latency in default mode |
| `skip_mode` is opt-in: existing users are unaffected | Users must consciously enable `skip_mode` to get cost savings — the default looks like it "works" but doesn't save money |
| Per-prompt feature championship selects the best input signal automatically | Championship model rebuild is CPU-intensive; default `batch_size=1000` means rebuild deferred until 1000 samples per collection |
| Cache correctness validated live via `cache_hit_validation` metric | Cache never serves a response until `n_neighbors=50` samples are accumulated per prompt; effectively no hits in short simulations |
| `enabled: false` default — zero impact on existing runs | `[outputs]` sections added to 33 TOML files is a large mechanical diff; errors in type classification would cause wrong eligibility decisions |
| Stats written to JSON on `close()` | In-memory counters lost on actor crash; JSON only written on clean shutdown |
| `llm/cache/` subpackage separates pure-Python logic from Ray dependency | Step 13 is a pure rename/split with no logic changes, but requires updating 2 import sites (`llm/__init__.py`, `configs/env.py`) |
| Model-scoped collection names prevent cross-model cache poisoning | Users with pre-Step-14 on-disk caches lose their warm state — the cache restarts cold. No data corruption, but the warmup cost is paid again. |
| `_sanitize_collection_name()` already handles slashes and dots — no new helper needed | Collection names become slightly longer; Qdrant has no documented name length limit but very long model identifiers could produce unwieldy names (not a practical concern for known provider model strings) |

---

## Rejected Approaches

- **In-process cache (not a Ray actor)**: Agents run as isolated Ray remote actors. Cannot share a Python dict or an in-process Qdrant client. Rejected.
- **Fire-and-forget probe (non-blocking)**: A non-blocking probe cannot short-circuit the LLM call. The probe must be awaited.
- **Use `block_name`/`func_name` as collection key**: These strings are set inconsistently across blocks. Prompt identity `(name, origin, version)` from TOML metadata is the stable canonical key.
- **Embed the full rendered dialog**: Conflates all features into one vector, making feature championship impossible.
- **BM25 sparse embeddings**: Keyword overlap is a poor signal for numeric-heavy agent state strings. Dense embeddings are more robust.
- **One `QdrantCacheActor` per agent**: Would multiply actor count by agent count; each instance would have too few samples to build a reliable model. Cross-agent learning is the point.
- **Extend `PromptManager.format_prompt_to_dialog()` return type**: Would break all 30+ call sites. New opt-in methods are backward-compatible.
- **Record dataset in existing ClickHouse `prompt_responses` table**: That table has no vector index and cannot support nearest-neighbor queries.
- **`embed = true` marker in TOML input fields**: All `type = "text"` fields are automatically embedded. No explicit marker needed.
- **Change `skip_mode` default to `True`**: The current shadow-validation mode provides a safety net — the LLM still runs and its result is returned even when the cache probe hits. Flipping the default silently to skip mode could serve incorrect cached results to users who never read the changelog. An opt-in flag is safer.
- **Use `QdrantClient(":memory:")` for the e2e test**: The `QdrantCacheActor` constructor hard-codes `QdrantClient(path=...)`. Supporting in-memory mode would require a constructor change and a new config flag. A real on-disk client in a temp directory works today with no code changes.
- **Keep `QdrantCacheConfig` in `configs/` rather than `llm/cache/`**: `QdrantCacheConfig` is already in `llm/qdrant_cache_config.py` (inside the `llm/` package), not in `configs/`. Moving it to `llm/cache/config.py` continues that convention and keeps the cache subpackage self-contained. `configs/env.py` already imports it from `llm/`; the import path change is minimal.
- **Keep `MultiFeatureQdrantChampionCache` and `QdrantCacheActor` in the same file**: The single-file approach was the initial implementation choice for speed. At 629 lines with two logically independent classes (one with no Ray dependency), the file is already past the point where a split improves readability and testability with no risk.
- **Pass the model name through `prompt_identity` as a 4th tuple element**: `prompt_identity` is a `(name, origin, version)` triple defined by `PromptManager.get_prompt_identity()` (`prompts/prompt_manager.py:156`). It is a prompt-level concept, not a model-level concept. Folding model identity into it conflates two independent axes. Keeping model name as a separate actor-level attribute is cleaner and avoids changing the `prompt_identity` contract at every call site.
- **Use the full `LLMConfig` object (not just `model`) for collection scoping**: Provider + model together could theoretically distinguish fine-tuned variants hosted at the same endpoint. In practice, model name is the stable, human-readable discriminant. Provider differences rarely produce different output distributions for the same model name. Using only `model` keeps the collection name short and readable.
- **Automatically rename existing collections on first startup**: Renaming requires reading all existing collection names, inferring which model they belong to, and renaming them — but the old name contains no model information, so inference is impossible without external metadata. Silent rename is not feasible. A clean restart is the correct behavior.

---

## Assumptions

- The `LLM` constructor change (accepting `cache_skip_mode: bool`) is backward-compatible because it has a default of `False`.
- The `InfrastructureManager` already has `self._config.env.qdrant_cache` available at the point where `LLM(...)` is constructed (`infrastructuremanager.py:439`), so no new dependency injection is needed.
- LLM API credentials will be available in the test environment (live LLM is used in the e2e test).
- The e2e test environment has network access to download the `BAAI/bge-small-en-v1.5` fastembed model on first run, or the model is already cached.
- Step 13 is a pure mechanical refactor (rename + split + import update). No logic changes. All existing tests and example runs remain valid after Step 13 because `agentsociety/llm/__init__.py` continues to export `QdrantCacheActor` and `QdrantCacheConfig` under the same names.
- All `LLMConfig` entries in a single `LLM` instance reference the same model name. If a heterogeneous multi-model `LLM` setup were introduced in future, the collection naming scheme would need revisiting. For now, `configs[0].model` is authoritative.
- The `InfrastructureManager` has access to the primary `LLMConfig.model` value at the point where `QdrantCacheActor.remote(...)` is called. The exact config attribute path should be confirmed before Step 14 implementation — look at how `_init_llm_cache_actor()` (`infrastructuremanager.py:398`) accesses the simulation config object.

---

## Test Plan

### Location and runner

- File: `tests/e2e/006_qdrant_cache.py`
- Runner: add `"$PYTHON_BIN" "006_qdrant_cache.py" "$@"` to `tests/run_e2e_tests.sh` alongside the existing `001_run_simplest_e2e.py` invocation.

### Environment

- **Ray**: `ray.init()` called in test setup; `QdrantCacheActor.remote(...)` used directly. Same pattern as other e2e tests in `tests/e2e/utils.py`.
- **Qdrant**: real `QdrantClient` writing to a `tempfile.mkdtemp()` directory. Directory cleaned up in teardown.
- **LLM**: live LLM using credentials from the test environment. No mocking.
- **n_neighbors**: default of 50 (no override). The test submits 51+ near-identical prompts to cross the threshold naturally.

### Test scenario: functional cache hit

**Setup:**
- Start Ray (`ray.init()`).
- Create a `QdrantCacheActor` via `.remote()` with `path=<tempdir>`, `n_neighbors=50`, `batch_size=50`, `probability_threshold=0.9`, default `embedding_model`, and `llm_model_name="gpt-4o"` (or the test environment's model name).
- Prompt identity: any eligible prompt with a categorical or float output, e.g., `("needs_evaluation", "citysim", "1.0")`.
- Input schema: one text field (e.g., `{"activity": {"type": "text"}}`).
- Output schema: one categorical field (e.g., `{"hunger_satisfaction": {"type": "float"}}`).

**Phase 1 — warm the cache (51 near-identical records):**
- Call `actor.record.remote(prompt_identity, {"activity": "eating lunch at home"}, input_schema, "0.8", output_schema)` 51 times with minor lexical variation (e.g., "eating lunch at home", "having lunch at home", "lunch at home again", ...).
- After 51 records, the actor's internal `batch_size` threshold is crossed; the KNN model rebuilds.
- `ray.get(actor.get_stats.remote())` — assert that the collection for this prompt identity has `>= 51` total records.
- Assert the collection name in `get_stats()` output contains `gpt-4o` (verifies model scoping is in effect).

**Phase 2 — assert functional cache hit:**
- Call `ray.get(actor.query_and_maybe_serve.remote(prompt_identity, {"activity": "eating lunch"}, input_schema, output_schema))`.
- Assert the return value is not `None` (i.e., the cache returned a result rather than a miss).
- Assert the returned value is parseable as a float in [0.0, 1.0].

**Phase 3 — stats integrity:**
- Call `ray.get(actor.close.remote())`.
- Assert `<tempdir>/stats.json` exists.
- Parse the JSON and assert it contains a `"collections"` key with at least one entry whose `hits > 0`.
- Assert all collection names in `stats.json` contain `gpt-4o`.

**Passing criteria:**
The test passes if Phase 2 returns a non-None result (the cache hit is functional) and Phase 3 finds `hits > 0` in `stats.json`. This is the "functional" level from the original Q-E options.

### What the test does NOT cover

- Skip-mode (`skip_mode=True`) LLM bypass — this requires constructing a full `LLM` instance with a live provider and asserting LLM actor call count. That is a separate, more invasive test that can be added once Step 11 is implemented and the functional test above is green.
- Prometheus counters — `MetricsTracker` is not initialized in the e2e test; only `get_stats()` and `stats.json` are checked.
- Multi-feature championship (only one text feature used in this test; championship is implicitly exercised but not explicitly asserted).
- Cross-model isolation (verifying that a cache built with `llm_model_name="gpt-4o"` does NOT serve results when queried with `llm_model_name="gpt-3.5-turbo"`) — this is structurally enforced by the naming scheme and does not require a runtime test, but could be added as a unit test against `_collection_name()` directly.

---

## Code That Could Be Refactored *(informational)*

- `agentsociety/simulation/infrastructuremanager.py:329-440` — `_init_metrics_actor()`, `_init_clickhouse_actor()`, `_init_dispatcher_cache_actor()`, `_init_llm_cache_actor()` are structurally near-identical. A generic `_init_actor(...)` helper would eliminate the repetition.
- `agentsociety/llm/llm.py` — `atext_request` body is long and has multiple named helper methods that break up the logic. The shadow-validation path in `_maybe_serve_probe_result()` (`llm.py:296`) will become simpler once `skip_mode=True` is used in production (the comparison logic can be dropped or made conditional).
- `agentsociety/llm/qdrant_cache_actor.py:544` — `query_and_maybe_serve()` checks `_is_cache_eligible(output_schema)` after calling `_embed_typed_fields()` and constructing the cache. Eligibility check should happen first, before the expensive embedding step, to short-circuit ineligible prompts with zero work. (This note applies to the same method in `llm/cache/ray_actor.py` after Step 13.)

---

## Proposed Next Steps

1. **Step 13 — Create `llm/cache/` subpackage:**
   - Create `agentsociety/llm/cache/` directory.
   - Create `agentsociety/llm/cache/config.py`: move `QdrantCacheConfig` from `llm/qdrant_cache_config.py`. Update relative logger import: `from ...logger import get_logger` (no logger is actually used here; the pydantic model has no logger import, so this step is trivial — just move the class).
   - Create `agentsociety/llm/cache/qdrant_cache.py`: move `_sanitize_collection_name` (line 18) and `MultiFeatureQdrantChampionCache` (line 22) from `llm/qdrant_cache_actor.py`. Update logger import to `from ...logger import get_logger`.
   - Create `agentsociety/llm/cache/ray_actor.py`: move `QdrantCacheActor` (line 364) from `llm/qdrant_cache_actor.py`. Add `from .qdrant_cache import MultiFeatureQdrantChampionCache, _sanitize_collection_name` at the top. Update logger import to `from ...logger import get_logger`.
   - Create `agentsociety/llm/cache/__init__.py` with re-exports of `QdrantCacheConfig`, `MultiFeatureQdrantChampionCache`, `QdrantCacheActor`.
   - Update `agentsociety/llm/__init__.py:4-5`: replace `from .qdrant_cache_actor import QdrantCacheActor` and `from .qdrant_cache_config import QdrantCacheConfig` with `from .cache import QdrantCacheActor, QdrantCacheConfig`.
   - Update `agentsociety/configs/env.py:6`: replace `from ..llm.qdrant_cache_config import QdrantCacheConfig` with `from ..llm.cache.config import QdrantCacheConfig`.
   - Delete `agentsociety/llm/qdrant_cache_actor.py` and `agentsociety/llm/qdrant_cache_config.py`.
   - Verify: `agentsociety/simulation/infrastructuremanager.py:20` (`from ..llm import LLM, QdrantCacheActor`) requires no change.

2. **Step 14 — Add LLM model name to collection naming** (can run before or after Step 13):
   - Add `llm_model_name: str` parameter to `QdrantCacheActor.__init__` (`qdrant_cache_actor.py:368`, or `llm/cache/ray_actor.py` if Step 13 ran first). Store as `self._llm_model_name`.
   - Update `_collection_name()` (`qdrant_cache_actor.py:399`, or `llm/cache/ray_actor.py`) to append `__{self._llm_model_name}` to the raw name before sanitisation.
   - In `InfrastructureManager._init_llm_cache_actor()` (`infrastructuremanager.py:398`), pass `llm_model_name=<primary_llm_config>.model` when calling `QdrantCacheActor.remote(...)`. Confirm the exact config attribute path by reading `infrastructuremanager.py:398–440` before implementing.
   - Confirm the existing `_sanitize_collection_name()` helper (`qdrant_cache_actor.py:18`) is sufficient (it is — slashes and dots are already replaced with `_`).
   - Document the migration note in operator-facing release notes: existing on-disk Qdrant caches will not be read after this change; the cache restarts cold.

3. **Step 11 — Add `skip_mode` to `QdrantCacheConfig` and `LLM`** (can run before or after Steps 13/14):
   - Add `skip_mode: bool = Field(default=False)` to `QdrantCacheConfig` (in `llm/cache/config.py` if Step 13 ran first, otherwise `llm/qdrant_cache_config.py`).
   - Add `cache_skip_mode: bool = False` parameter to `LLM.__init__` (`llm.py:115`); store as `self._cache_skip_mode`.
   - Insert the early-return guard between `llm.py:434` and `llm.py:437` (between probe result assignment and the `while True:` loop).
   - Pass `cache_skip_mode=self._config.env.qdrant_cache.skip_mode` in the `LLM(...)` constructor call at `infrastructuremanager.py:439`.

4. **Step 12 — Write `tests/e2e/006_qdrant_cache.py`** per the test plan above (including the `llm_model_name` constructor argument and the collection-name assertions added by Step 14).

5. **Wire into `tests/run_e2e_tests.sh`:** add `"$PYTHON_BIN" "006_qdrant_cache.py" "$@"` after the `001_run_simplest_e2e.py` line.

6. **Fix the eligibility check order** in `QdrantCacheActor.query_and_maybe_serve()` (line 544 in the current file; same method in `llm/cache/ray_actor.py` after Step 13): move `_is_cache_eligible(output_schema)` before the `_embed_typed_fields()` call to avoid unnecessary embedding work on ineligible prompts. (Low priority; correctness-neutral.)

7. **End-to-end validation with a full simulation**: run a short simulation with `env.qdrant_cache.enabled: true`, `env.qdrant_cache.skip_mode: true`, and `env.qdrant_cache.n_neighbors: 10` (lower threshold for quick validation). Inspect Qdrant collection sizes via `get_stats()`. Verify collection names contain the model name. Verify `stats.json` is written on shutdown. Verify Prometheus metrics visible in Grafana.
