# Qdrant-Backed LLM Semantic Cache (Ray Actor)
> A Ray actor that intercepts eligible LLM calls, uses a multi-feature Qdrant championship algorithm to return cached responses when confidence is high, and collects prompt/response pairs as labeled training data.

## Purpose & Motivation

The simulation runs hundreds of agents in parallel, each making dozens of LLM calls per tick. Many prompts are structurally near-identical across agents (same block, same situation, slightly different numeric state). The LLM call is the dominant cost — both latency and API spend.

This feature builds a **semantic similarity cache** that:
1. Embeds the text-type input fields declared in each prompt TOML separately.
2. Uses the championship algorithm from the code-snippets file to select the best-performing feature vector and return cached labels when confidence is high.
3. Falls back to the live LLM on cache misses, records the label, and periodically rebuilds the KNN model.
4. Collects all prompt+label pairs as labeled training data for future fine-tuning.

The cache only applies to prompts whose TOML declares `[outputs]` with all-categorical or all-numeric output fields. Prompts with free-text outputs (like status summaries) are excluded — they are cached only for dataset collection, not for response serving.

## Success Criteria

- Cache actor starts and stops cleanly alongside other Ray actors in `InfrastructureManager`.
- For eligible prompts, a cache hit short-circuits the live LLM call and returns the cached label.
- Probe latency is logged each call so its cost is observable.
- Hit/miss counters are written to a JSON file on `close()` and emitted to Prometheus when monitoring is enabled.
- All prompt TOML files have `[outputs]` sections so the cache can decide eligibility at load time.
- Feature is opt-in: disabled by default, zero impact on existing runs unless `env.qdrant_cache.enabled: true` is set.

## Scope

**In scope:**
- New file `agentsociety/llm/qdrant_cache_actor.py` — Ray remote actor wrapping the championship cache logic, with one Qdrant collection per `(name, origin, version)` tuple.
- New file `agentsociety/llm/qdrant_cache_config.py` — Pydantic config model for the cache.
- Extend `LLMContext` TypedDict with two new optional fields: `prompt_identity` and `prompt_inputs`.
- Extend `PromptManager` to expose output schema and pass `prompt_identity` + `prompt_inputs` to callers.
- Modify `LLM.atext_request` to probe and record via the cache actor when context carries `prompt_identity`.
- Wire-up in `InfrastructureManager` following the pattern established by `GlobalDispatcherCacheActor`.
- Add cache config to `EnvConfig`.
- Add `[outputs]` sections to all existing prompt TOML files (33 files).
- Add cache hit/miss metrics to `PrometheusActor`.
- Stats persistence: JSON file on `close()`, Prometheus gauges when monitoring is enabled.

**Out of scope:**
- Multi-machine / distributed Qdrant (local path only).
- Caching tool-call responses (calls where `tools=...` is passed are skipped).
- A UI or dashboard for cache stats.
- Disk eviction / capacity management (unlimited for now).
- Changing the existing `prompt_responses` table in ClickHouse.

## Constraints

- `qdrant-client[fastembed]>=1.12.1` is already declared in `pyproject.toml`. No new package dependency required.
- Dense embedding model: `BAAI/bge-small-en-v1.5` (384-dim via fastembed). This is the same library already used for sparse BM25 in `InfrastructureManager._init_embedding()`.
- The actor must be a Ray remote actor (agents run in isolated Ray actors and cannot share Python objects).
- The actor must not call back into the LLM (infinite-loop risk).
- `LLMContext` uses `TypedDict(total=False)`, so adding fields is backward-compatible with zero caller changes for callers that don't set the new fields.
- Probe is awaited, and its latency is logged. If the actor is unavailable (e.g., crashed), the call falls through to the live LLM silently.
- Qdrant path defaults to `<data_dir>/qdrant/`, where `data_dir` is `EnvConfig.data_dir` (already in config at `configs/env.py:55`). Configurable via `env.qdrant_cache.path` override.

## Architecture & Integration Points

```
PromptManager.format_prompt_to_dialog(name, state_dict)
    → returns dialog, also computes:
        prompt_identity = (name, origin, version)
        prompt_inputs   = {field: value for text-type fields in state_dict}

Block calls:
    llm.atext_request(dialog, ..., context={
        "block_name": ..., "func_name": ..., "agent_id": ...,
        "prompt_identity": (name, origin, version),   ← new
        "prompt_inputs": {"intention": "...", "plan": "..."},  ← new
    })

LLM.atext_request():
    if tools != NOT_GIVEN → skip cache entirely
    if cache_actor and context has prompt_identity:
        t0 = time.perf_counter()
        result = await cache_actor.query_and_maybe_serve.remote(
            prompt_identity, prompt_inputs
        )
        log probe latency
        if result is not None:
            return result   ← cache hit, LLM call skipped

    → live LLM call (unchanged path)
    → cache_actor.record.remote(prompt_identity, prompt_inputs, llm_response)
         [fire-and-forget]
    return llm_response
```

Integration point citations:

- `agentsociety/llm/llm.py:33` — `LLMContext(TypedDict, total=False)` gains two fields: `prompt_identity: tuple[str, str, str]` and `prompt_inputs: dict[str, Any]`.
- `agentsociety/llm/llm.py:104` — `LLM.__init__` gains `cache_actor: Optional[Any] = None`, stored as `self._cache_actor`.
- `agentsociety/llm/llm.py:228` — `LLM.atext_request()` is the insertion point for both the probe (before `acquire_client`) and the record (fire-and-forget after `return result`).
- `agentsociety/prompts/prompt_manager.py:387` — `PromptManager.format_prompt()` and `format_prompt_to_dialog()` gain new methods `get_prompt_identity(name)` and `get_text_input_fields(name)` to expose what callers need.
- `agentsociety/simulation/infrastructuremanager.py:376` — `_init_dispatcher_cache_actor()` is the structural template for the new `_init_llm_cache_actor()`.
- `agentsociety/simulation/infrastructuremanager.py:427` — `initialize_all()` is where `_init_llm_cache_actor()` is called, before `_init_core_components()`, so the handle is available when `LLM` is constructed.
- `agentsociety/simulation/infrastructuremanager.py:389` — `_init_core_components()` constructs `LLM(...)`: gains `cache_actor=self._llm_cache_actor`.
- `agentsociety/simulation/infrastructuremanager.py:435` — `close()` gains `await self._llm_cache_actor.close.remote()`.
- `agentsociety/simulation/simulationengine.py:196` — `_finalize_initialization()` adds `llm_cache_tool` to `agent_toolbox` (same pattern as `dispatcher_cache_tool` at line 196).
- `agentsociety/configs/env.py:43` — `EnvConfig` gains `qdrant_cache: QdrantCacheConfig`.
- `agentsociety/performance/prometheusActor.py:15` — `PrometheusActor` gains a `record_cache_stats(prompt_name, hits, misses)` method.
- All 33 prompt TOML files in `agentsociety/prompts/` gain `[outputs.*]` sections.

## Similar Patterns & Reuse

- **What it is**: `agentsociety/agent/dispatcher_cache_actor.py:8 — GlobalDispatcherCacheActor`
  **What it does**: Stateful Ray actor with `check_cache()` / `update_cache()` / `close()` methods and in-memory stats. Wrapped in `CustomTool`, initialized in `InfrastructureManager`.
  **How this feature uses it**: Identical actor boilerplate. The new `QdrantCacheActor` follows the same `@ray.remote class`, same `CustomTool` wrapper, same init/close in `InfrastructureManager`.

- **What it is**: `docs/features/qdrant-llm-cache-code-snippets.md — MultiFeatureQdrantChampionCache`
  **What it does**: Maintains one Qdrant collection with named vectors per text feature. Uses KNN (k=50) with cosine distance on each feature separately, runs macro-F1 scoring per feature to select a champion, computes a distance-quantile threshold, and returns cache-hit when `top_proba >= 0.95 AND furthest_neighbor_distance <= threshold`. Rebuilds every 1000 records.
  **How this feature uses it**: The class is adapted for the Ray actor context: async-safe (actor serializes calls), one per-prompt-identity instance (not one global), uses `QdrantClient(path=...)` instead of `:memory:`.

- **What it is**: `agentsociety/simulation/infrastructuremanager.py:293 — _init_embedding()`
  **What it does**: Loads `fastembed.SparseTextEmbedding("Qdrant/bm25")` with a timeout and cache directory.
  **How this feature uses it**: The actor uses the same `cache_dir` convention (`home_dir/huggingface_cache`) and wraps model loading in a timeout guard.

- **What it is**: `agentsociety/llm/llm.py:104 — LLM.__init__` accepting optional actor handles
  **What it does**: Accepts `metrics_actor` and `db_actor` as optional params, stores them, uses them for fire-and-forget side effects in `atext_request`.
  **How this feature uses it**: `cache_actor` is added as a third optional param following this exact pattern.

- **What it is**: `agentsociety/prompts/prompt_manager.py:152 — PromptManager.get_required_fields()`
  **What it does**: Returns `prompt_data["inputs"]["required"]` for a given prompt name.
  **How this feature uses it**: Two new analogous methods are added: `get_prompt_identity(name)` returns `(name, origin, version)` and `get_text_input_fields(name)` returns the list of fields with `type = "text"` in `[inputs.*]`.

## Implementation Strategy

### Step 1 — Add `[outputs]` to all prompt TOML files

**Before**: No TOML file has an `[outputs]` section (confirmed by grep). The `PromptManager` does not read outputs.

**After**: 33 TOML files gain `[outputs]` sections. The cache uses `[outputs]` to decide eligibility: if all outputs are `categorical` or `float`/`integer`, the prompt is cache-eligible. If any output is `text`, the prompt is dataset-only (no response serving).

Classification of existing prompts (all files to update listed with their cache eligibility):

**Cache-eligible (all outputs categorical or numeric):**
- `mobility_place_analysis` — output: `place_type: categorical`
- `mobility_place_type_selection` — output: `place_type: categorical`
- `mobility_place_second_type_selection` — output: `place_type: categorical`
- `mobility_radius_selection` — output: `radius: integer`
- `mobility_transport_mode_selection` — output: `mode: categorical`
- `needs_evaluation` — outputs: `hunger_satisfaction: float`, `energy_satisfaction: float`, `safety_satisfaction: float`, `social_satisfaction: float`
- `needs_initialize` — same 4 float outputs
- `needs_reflection` — same 4 float outputs (or `do_something: categorical`)
- `needs_poi_observation` — outputs: `price: float`, `atmosphere: float`, `satisfaction: float`, `convenience: float`
- `worktime_estimate` — output: `time: integer`
- `other_time_estimate` — output: `time: integer`
- `other_sleep_time_estimate` — output: `time: integer`
- `social_time_estimate` — output: `time: integer`
- `month_plan_observation` — outputs: `work: float`, `consumption: float`
- `cognition_attitude_update` — output: `attitude: integer` (0-10)
- `cognition_initialize_big5` — outputs: `openness: integer`, `conscientiousness: integer`, `extraversion: integer`, `agreeableness: integer`, `neuroticism: integer`
- `societyagent_chat_response_decision` — output: `should_respond: categorical`
- `societyagent_chat_belief_update` — outputs: `affinity: float`, `trust: float`, `familiarity: float`

**Dataset-only (free-text output):**
- `societyagent_status_summary` — output is a free-text sentence
- `societyagent_environment_reflection` — output is free-text reflection
- `cognition_emotion_update` — output: `conclusion: text` (plus numeric intensities; mixed — exclude from serving)
- `cognition_thought_update` — output: `thought: text`
- `month_plan_mental_health_assessment` — 20 categorical responses but response is a complex questionnaire object: classify as `text` output (dataset-only)
- `month_plan_goal_creation` — output is a JSON array of goal strings: `text`
- `social_message_generation` — output is a free-text message
- `cognition_initialize_preferences` — output is a nested JSON with mixed types: treat as `text` (dataset-only for safety)
- `cognition_initialize_hobbies` — output is a list of strings: `text`
- `plan_guidance_selection` — output is `selected_option: text` with evaluation sub-dict
- `plan_detailed_generation` — output is a list of plan steps: `text`
- `daily_schedule_generation` — output is a list of blocks: `text`
- `empty_block_filling` — output includes `candidates` list: `text`
- `mobility_aoi_area_selection` — output includes reasoning string: treat as `text` (dataset-only)
- `mobility_neighborhood_selection` — same: `text`

Note: borderline cases (mixed categorical + text in one prompt) are conservatively classified as `text`/dataset-only.

### Step 2 — Add `QdrantCacheConfig` Pydantic model and wire into `EnvConfig`

**File**: `agentsociety/llm/qdrant_cache_config.py` (new) and `agentsociety/configs/env.py` (modified).

**Before**: `EnvConfig` at `configs/env.py:43` has no cache fields. `data_dir` at `env.py:55` is `"./agentsociety_data/data"`.

**After**: New standalone Pydantic model (kept in `agentsociety/llm/qdrant_cache_config.py` so the LLM layer can import it without circular deps):

```python
class QdrantCacheConfig(BaseModel):
    enabled: bool = Field(default=False)
    path: Optional[str] = Field(default=None)
    # If None, defaults to <data_dir>/qdrant/ at runtime
    probability_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    batch_size: int = Field(default=1000, ge=1)
    n_neighbors: int = Field(default=50, ge=1)
    distance_quantile: float = Field(default=0.95, ge=0.0, le=1.0)
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_cache_dir: Optional[str] = Field(default=None)
    # If None, defaults to <home_dir>/huggingface_cache at runtime
```

`EnvConfig` gains: `qdrant_cache: QdrantCacheConfig = Field(default_factory=QdrantCacheConfig)`.

The `enabled: false` default means zero config change is required for existing users.

### Step 3 — Implement `QdrantCacheActor` in `agentsociety/llm/qdrant_cache_actor.py`

**File**: New file.

The actor wraps one `MultiFeatureQdrantChampionCache` instance per `(prompt_name, origin, version)`. Each instance is created lazily on first access. The Qdrant client is shared: one `QdrantClient(path=qdrant_path)` for all instances, with collection names encoded as `f"{name}__{origin}__{version}"`.

Key public methods:

```python
@ray.remote
class QdrantCacheActor:
    def __init__(
        self,
        qdrant_path: str,
        embedding_model: str,
        embedding_cache_dir: str,
        probability_threshold: float,
        batch_size: int,
        n_neighbors: int,
        distance_quantile: float,
    ): ...

    def query_and_maybe_serve(
        self,
        prompt_identity: tuple[str, str, str],   # (name, origin, version)
        prompt_inputs: dict[str, Any],            # {field_name: value} for text fields only
        output_schema: dict[str, dict],           # {field_name: {type, categories?}} from [outputs]
    ) -> Optional[Any]:
        """
        Returns the cached label if cache hit, else None.
        Internally routes to the correct per-prompt cache instance.
        Records hit/miss counters.
        """

    def record(
        self,
        prompt_identity: tuple[str, str, str],
        prompt_inputs: dict[str, Any],
        llm_response: Any,
    ) -> None:
        """Record an LLM response (cache miss) for future training."""

    def get_stats(self) -> dict[str, dict]:
        """Returns {collection_name: {hits, misses, total, rebuild_count}} for all collections."""

    def close(self) -> None:
        """Write stats to JSON file. Flush Qdrant client."""
```

Internal design:
- One `fastembed.TextEmbedding(embedding_model, cache_dir=embedding_cache_dir)` is loaded once in `__init__`.
- `self._caches: dict[str, MultiFeatureQdrantChampionCache]` — keyed by `f"{name}__{origin}__{version}"`.
- `self._hit_counts: dict[str, int]` and `self._miss_counts: dict[str, int]` — per collection.
- Each `MultiFeatureQdrantChampionCache` is constructed with `feature_names` = list of text-type input field names for that prompt.
- Before `query_and_maybe_serve`, embed each text field separately using `TextEmbedding` → gives `{field_name: np.ndarray}` — this is the `feature_row` passed to the cache.
- Output schema determines how to extract the label from the LLM response JSON for `record()`.
- On `close()`, write `{collection: {hits, misses, ...}}` to `<qdrant_path>/stats.json`.

Adaptation of `MultiFeatureQdrantChampionCache` from the snippets file:
- Use `QdrantClient(path=qdrant_path)` instead of `QdrantClient(":memory:")`.
- Collection name is `f"{name}__{origin}__{version}"` (already set at construction).
- Payload key for labels is `"label"` generically (not `"place_type"`).
- Label serialization: for categorical output, label = `str(value)`; for float outputs, label = `json.dumps({k: v for k, v in outputs.items()})` (treating multi-float outputs as a single JSON-encoded label key).
- The `_flush_buffer` method is called inside `record()` when `len(self.buffer_rows) >= self.batch_size`.

### Step 4 — Extend `LLMContext` and `LLM.atext_request`

**File**: `agentsociety/llm/llm.py`.

**Before** (`llm.py:33`):
```python
class LLMContext(TypedDict, total=False):
    block_name: str
    func_name: str
    agent_id: str
```

**After**:
```python
class LLMContext(TypedDict, total=False):
    block_name: str
    func_name: str
    agent_id: str
    prompt_identity: tuple[str, str, str]   # (name, origin, version)
    prompt_inputs: dict[str, Any]           # text-type field values for embedding
    prompt_output_schema: dict[str, dict]   # [outputs] section from TOML
```

`total=False` means all fields remain optional — no existing callers break.

**Before** (`llm.py:104`): `LLM.__init__` accepts `metrics_actor` and `db_actor`.

**After**: Gains `cache_actor: Optional[Any] = None`, stored as `self._cache_actor`.

**Before** (`llm.py:228`): `atext_request` has no cache interaction.

**After**: Inside `atext_request`, just before the `while True:` loop:
```python
# --- Cache probe (only for non-tool calls with prompt_identity) ---
_probe_result = None
_collection_id = None
if (
    self._cache_actor is not None
    and context is not None
    and "prompt_identity" in context
    and isinstance(tools, NotGiven)   # skip tool-calling requests
):
    _collection_id = context["prompt_identity"]
    t_probe = time.perf_counter()
    try:
        _probe_result = await self._cache_actor.query_and_maybe_serve.remote(
            context["prompt_identity"],
            context.get("prompt_inputs", {}),
            context.get("prompt_output_schema", {}),
        )
    except Exception as e:
        get_logger().debug(f"Cache probe failed: {e}")
        _probe_result = None
    probe_latency = time.perf_counter() - t_probe
    get_logger().debug(
        f"Cache probe latency={probe_latency*1000:.1f}ms "
        f"hit={_probe_result is not None} "
        f"collection={_collection_id}"
    )
    if _probe_result is not None:
        # Cache hit — emit metrics and return without calling LLM
        if self._metrics_actor is not None and context:
            self._metrics_actor.record_cache_stats.remote(
                prompt_name=str(context["prompt_identity"][0]),
                hit=True,
            )
        return _probe_result
```

After `return result` (successful LLM response, `llm.py:343`), add fire-and-forget record:
```python
if self._cache_actor is not None and _collection_id is not None:
    self._cache_actor.record.remote(
        context["prompt_identity"],
        context.get("prompt_inputs", {}),
        result,
    )
    if self._metrics_actor is not None:
        self._metrics_actor.record_cache_stats.remote(
            prompt_name=str(context["prompt_identity"][0]),
            hit=False,
        )
```

### Step 5 — Extend `PromptManager` to expose identity and text inputs

**File**: `agentsociety/prompts/prompt_manager.py`.

Add three new methods to `PromptManager`:

```python
def get_prompt_identity(self, prompt_name: str) -> tuple[str, str, str]:
    """Returns (name, origin, version) from [metadata]."""
    meta = self._loaded_prompts[prompt_name]["metadata"]
    return (meta["name"], meta.get("origin", "unknown"), meta.get("version", "0.0.0"))

def get_text_input_fields(self, prompt_name: str) -> list[str]:
    """Returns names of input fields declared as type='text' in [inputs.*]."""
    prompt_data = self._loaded_prompts.get(prompt_name, {})
    inputs = {k: v for k, v in prompt_data.get("inputs", {}).items() if k != "required"}
    return [k for k, v in inputs.items() if isinstance(v, dict) and v.get("type") == "text"]

def get_output_schema(self, prompt_name: str) -> dict[str, dict]:
    """Returns the [outputs] section dict, or {} if absent."""
    return {
        k: v
        for k, v in self._loaded_prompts.get(prompt_name, {}).get("outputs", {}).items()
    }

def is_cache_eligible(self, prompt_name: str) -> bool:
    """Returns True if all outputs are categorical or numeric (no text outputs)."""
    schema = self.get_output_schema(prompt_name)
    if not schema:
        return False
    return all(
        v.get("type") in ("categorical", "float", "integer")
        for v in schema.values()
    )
```

### Step 6 — Update block call sites to pass `prompt_identity` and `prompt_inputs`

**Files**: All 8 block files plus `societyagent.py`. All calls to `self.llm.atext_request(dialog, ..., context={...})` where `dialog` was produced by `self.prompt_manager.format_prompt_to_dialog(prompt_name, state_dict)` need three additional context keys.

The pattern in each block is currently (example from `mobility_block.py:193`):
```python
dialog = self.prompt_manager.format_prompt_to_dialog(self.place_analysis_prompt_name, state_dict)
response = await self.llm.atext_request(
    dialog,
    response_format={"type": "json_object"},
    context={"block_name": self.name, "func_name": "Place Analysis", "agent_id": self.agent.id},
)
```

After the change, the context dict gains three keys extracted via new `PromptManager` methods:
```python
dialog = self.prompt_manager.format_prompt_to_dialog(self.place_analysis_prompt_name, state_dict)
_pm = self.prompt_manager
response = await self.llm.atext_request(
    dialog,
    response_format={"type": "json_object"},
    context={
        "block_name": self.name,
        "func_name": "Place Analysis",
        "agent_id": self.agent.id,
        "prompt_identity": _pm.get_prompt_identity(self.place_analysis_prompt_name),
        "prompt_inputs": {
            k: state_dict[k]
            for k in _pm.get_text_input_fields(self.place_analysis_prompt_name)
            if k in state_dict
        },
        "prompt_output_schema": _pm.get_output_schema(self.place_analysis_prompt_name),
    },
)
```

This pattern applies to every `atext_request` call site that goes through `PromptManager`. The full list of call sites (identified by grep at `agentsociety/cityagent/blocks/`):

| File | Call sites using PromptManager |
|---|---|
| `cityagent/blocks/mobility_block.py` | 8 call sites (AOI selection, neighborhood selection, type selection ×2, radius, place analysis, transport mode, + others) |
| `cityagent/blocks/needs_block.py` | 4 call sites (initialize, reflection, poi observation, evaluation) |
| `cityagent/blocks/economy_block.py` | varies — grep shows `atext_request` calls |
| `cityagent/blocks/cognition_block.py` | varies |
| `cityagent/blocks/daily_schedule_block.py` | varies |
| `cityagent/blocks/plan_block.py` | varies |
| `cityagent/blocks/social_block.py` | varies |
| `cityagent/blocks/other_block.py` | varies |
| `cityagent/societyagent.py` | 4 call sites (status summary, environment reflection, chat belief update, chat response decision) |

Call sites in `agent/dispatcher.py` (the block dispatcher) and `agent/agent.py` do NOT use `PromptManager` — they pass ad-hoc dialogs. Those call sites are left unchanged and will not have `prompt_identity` in context, so the cache silently skips them.

### Step 7 — Wire into `InfrastructureManager`

**File**: `agentsociety/simulation/infrastructuremanager.py`.

**Before** (`infrastructuremanager.py:54`): No `_llm_cache_actor` or `_llm_cache_tool` attributes.

**After**: Add to `__init__`:
```python
self._llm_cache_actor: Optional[Any] = None
self._llm_cache_tool: Optional[CustomTool] = None
```

Add property accessors following the existing pattern (see `dispatcher_cache_tool` at `infrastructuremanager.py:102`).

New method `_init_llm_cache_actor()`, modeled on `_init_dispatcher_cache_actor()` at `infrastructuremanager.py:376`:
```python
def _init_llm_cache_actor(self):
    cfg = self._config.env.qdrant_cache
    if not cfg.enabled:
        get_logger().info("Qdrant LLM cache disabled by config, skipping.")
        return
    qdrant_path = cfg.path or os.path.join(self._config.env.data_dir, "qdrant")
    embedding_cache_dir = cfg.embedding_cache_dir or os.path.join(
        self._config.env.home_dir, "huggingface_cache"
    )
    os.makedirs(qdrant_path, exist_ok=True)
    try:
        from ..llm.qdrant_cache_actor import QdrantCacheActor
        self._llm_cache_actor = QdrantCacheActor.remote(
            qdrant_path=qdrant_path,
            embedding_model=cfg.embedding_model,
            embedding_cache_dir=embedding_cache_dir,
            probability_threshold=cfg.probability_threshold,
            batch_size=cfg.batch_size,
            n_neighbors=cfg.n_neighbors,
            distance_quantile=cfg.distance_quantile,
        )
        self._llm_cache_tool = CustomTool(
            name="llm_cache_actor",
            tool=self._llm_cache_actor,
            description="Ray actor for Qdrant-backed LLM semantic cache",
        )
        get_logger().info(f"Qdrant LLM cache actor initialized at {qdrant_path}")
    except Exception as e:
        get_logger().warning(f"Failed to initialize LLM cache actor: {e}")
```

In `initialize_all()` at `infrastructuremanager.py:427`, add `self._init_llm_cache_actor()` before `await self._init_core_components()`.

In `_init_core_components()` at `infrastructuremanager.py:389`, the `LLM` constructor call gains `cache_actor=self._llm_cache_actor`.

In `close()` at `infrastructuremanager.py:435`:
```python
if self._llm_cache_actor is not None:
    try:
        await self._llm_cache_actor.close.remote()
    except Exception as e:
        get_logger().warning(f"Error closing LLM cache actor: {e}")
```

### Step 8 — Add `llm_cache_tool` to agent toolbox

**File**: `agentsociety/simulation/simulationengine.py`.

**Before** (`simulationengine.py:195`): `_finalize_initialization` adds `metrics_tool`, `db_tool`, and `dispatcher_cache_tool` to `agent_toolbox`.

**After**: Add after the dispatcher cache:
```python
llm_cache_tool = self._infrastructure_manager.llm_cache_tool  # new property
if llm_cache_tool is not None:
    agent_toolbox.add_tool(llm_cache_tool)
```

This is not strictly required for the cache to work (agents don't need to call `get_stats()` themselves) but matches the established convention and allows future agent-level introspection.

### Step 9 — Add cache metrics to `PrometheusActor`

**File**: `agentsociety/performance/prometheusActor.py`.

Add a new method that tracks cache hits and misses per prompt name using Prometheus counters:
```python
def record_cache_stats(self, prompt_name: str, hit: bool) -> None:
    """Record a cache hit or miss for a given prompt."""
    self.metricsTracker.record_cache_stats(prompt_name, hit)
```

The underlying `MetricsTracker` gains two `Counter` objects: `cache_hits_total` and `cache_misses_total`, labelled by `prompt_name`.

### Step 10 — Export updates

**File**: `agentsociety/llm/__init__.py`.

Export `QdrantCacheActor` and `QdrantCacheConfig` for callers that need direct access:
```python
from .qdrant_cache_actor import QdrantCacheActor
from .qdrant_cache_config import QdrantCacheConfig
```

## Trade-Offs

| Gain | Cost / Risk |
|---|---|
| High-frequency prompts with stable patterns (mobility destination, needs satisfaction) get LLM calls skipped after sufficient history — major latency and cost reduction | Championship model rebuild is CPU-intensive (KNN training + threshold computation); rebuild every 1000 records may pause the actor for seconds in Python-land |
| Per-prompt feature championship means the best signal (e.g., `intention` for mobility) is automatically selected | Dense embedding of multiple text fields per call adds ~2–5 ms per probe inside the actor; acceptable for the amortized savings when cache hits |
| Probe result is awaited, so the hot path always knows the cache decision before calling the LLM | One Ray IPC round-trip before every eligible LLM call; at 1000 agents this is 1000 concurrent probes per tick — actor concurrency must be configured appropriately |
| Stats written to JSON on close; Prometheus metrics track per-prompt hit rates in real time | In-memory counters lost on actor crash; JSON file is only written on clean shutdown |
| Feature is opt-in with `enabled: false` default | The `[outputs]` TOML additions are mechanical but large — 33 files to touch, risk of errors during classification |
| All text-output prompts are still recorded as dataset (but not served from cache) | Qdrant on-disk storage grows unboundedly; no eviction policy in this version |

## Rejected Approaches

- **In-process cache (not a Ray actor)**: Agents run as isolated Ray remote actors. They cannot share a Python dict or an in-process Qdrant client. A Ray actor is the only viable shared-state mechanism. Rejected immediately.

- **Fire-and-forget probe (non-blocking)**: Answered in Q3 — the probe is awaited and its latency is logged. This is necessary to actually short-circuit the LLM call on a cache hit. Fire-and-forget probing would reduce latency overhead but would not allow skipping the LLM call, which is the point of the feature.

- **Use `block_name`/`func_name` as collection key instead of prompt identity**: Answered in Q1 — prompt identity `(name, origin, version)` is used. `block_name`/`func_name` strings are set inconsistently across blocks (e.g., `mobility_block.py:197` uses `"AOI Area Selection"` but `needs_block.py:609` uses `"evaluate_and_adjust_needs"`), while prompt TOML `name` fields are stable canonical identifiers. Version and origin allow per-variant caches when prompts diverge between citysim and agentsociety origins.

- **Embed the full rendered dialog**: Answered in Q2 — embed each text-type `[inputs.*]` field separately from the raw `state_dict`, before template rendering. This is the `MultiFeatureQdrantChampionCache` design: separate named vectors per feature. Embedding the full rendered dialog conflates all features into one vector, making feature championship impossible.

- **Use BM25 sparse embeddings**: BM25 sparse vectors measure keyword overlap. A prompt for agent A (age 35) and agent B (age 36) differ only in a numeric substring — BM25 would score them very differently. Dense embeddings (`bge-small-en-v1.5`) capture semantic similarity more robustly. Also confirmed in Q8.

- **One `QdrantCacheActor` per agent**: Would multiply actor count by the number of agents (e.g., 1000 actors), each with too few training samples to build a reliable model. Cross-agent learning is the entire point — one global actor accumulates history across all agents for the same prompt. Rejected.

- **Extend `PromptManager.format_prompt_to_dialog()` to return cache context inline**: Would require changing the return type signature, breaking all 30+ call sites. Instead, three new methods on `PromptManager` give callers opt-in access. Backward-compatible. Rejected the signature change.

- **Record dataset in existing ClickHouse `prompt_responses` table**: That table is append-only with no vector index. It cannot do nearest-neighbor queries. The Qdrant collections serve a different purpose (similarity search + label voting). The two stores are complementary: ClickHouse for structured logs, Qdrant for the cache model. Rejected as a replacement.

- **Add `embed = true` marker to TOML input fields**: Answered in Q10 — all `type = "text"` fields are automatically embedded. No explicit `embed = true` marker needed. Simpler and consistent with the TOML type system.

## Assumptions & Open Questions

### Assumptions

- `fastembed.TextEmbedding("BAAI/bge-small-en-v1.5")` is available inside the `qdrant-client[fastembed]` package already declared at `pyproject.toml`. This is confirmed by the fastembed package documentation.
- All agent LLM calls go through `LLM.atext_request` — there is no secondary call path.
- The simulation runs on a single machine — the local Qdrant path is accessible to all Ray workers.
- The actor's Python GIL serializes `query_and_maybe_serve` and `record` calls, preventing concurrent Qdrant writes from different agents from corrupting state.
- `state_dict` fields passed to `format_prompt_to_dialog` are already resolved (not raw memory handles) and serializable to string for embedding.
- The existing `prompt_responses` ClickHouse table continues to operate unchanged in parallel.

### Open Questions

**Q1 (Qdrant persistence across runs):** The Qdrant on-disk path persists across simulation runs. Should the actor check if an existing collection from a previous run exists and continue accumulating, or always start fresh? Recommendation: continue accumulating (the model gets better with more data), but this means the champion model from a previous run is reused immediately, which could be confusing if the prompt changed. This should be revisited when versioning of prompt-identity tuples is tight.

USER'S ANSWERS: Keep the same Qdrant database across runs that is keep updating and using it. Make the collection totally coupled to the prompt-identity tuples, so if I change it, I don't reuse a stale cache, but can re-use it later.

**Q2 (Actor concurrency):** The default Ray actor processes one call at a time. With 1000+ agents probing and recording simultaneously, there will be queuing. Should the actor be decorated with `@ray.remote(max_concurrency=N)` to allow concurrent reads? Note: Qdrant itself is thread-safe for reads but not concurrent writes. Recommendation: use `max_concurrency=1` (default) initially and profile; the KNN training rebuild is the bigger concern.

**Q3 (Label extraction for multi-output prompts):** For prompts with multiple float outputs (e.g., `needs_evaluation` with `hunger_satisfaction`, `energy_satisfaction`, `safety_satisfaction`, `social_satisfaction`), how should the label be encoded for the `MultiFeatureQdrantChampionCache`? The snippets file uses a single string label. Options:
- Encode as JSON string: `'{"hunger_satisfaction": 0.8, "energy_satisfaction": 0.7, ...}'`
- Train one cache instance per output field (more accuracy, more actor state)
Recommendation: JSON-string encoding for now (simplest), but flagged as a known limitation.

USER'S ANSWERS:

Use this format:
[outputs.hunger_satisfaction]
type = "float"
description = "Updated hunger satisfaction level (0.0 to 1.0)."

[outputs.energy_satisfaction]
type = "float"
description = "Updated energy satisfaction level (0.0 to 1.0)."

[outputs.safety_satisfaction]
type = "float"
description = "Updated safety satisfaction level (0.0 to 1.0)."

[outputs.social_satisfaction]
type = "float"
description = "Updated social satisfaction level (0.0 to 1.0)."


**Q4 (Collision in collection names):** Collection name is `f"{name}__{origin}__{version}"`. Qdrant collection names must match `[a-zA-Z0-9_-]+`. If `name`, `origin`, or `version` contain characters outside this set, the name must be sanitized. The current TOML files use safe characters, but a sanitization step (`re.sub(r'[^a-zA-Z0-9_-]', '_', ...)`) should be applied defensively. USER's ANSWER: Use sanitization.

## Code That Could Be Refactored *(informational)*

- `agentsociety/simulation/infrastructuremanager.py:329-387` — `_init_metrics_actor()`, `_init_clickhouse_actor()`, `_init_dispatcher_cache_actor()` are structurally near-identical: create actor with `.remote()`, wrap in `CustomTool`, assign to `self._X_tool`. A generic `_init_actor(cls, name, description, enabled, *args, **kwargs)` helper would eliminate the repetition. Not a blocker for this feature.
- `agentsociety/llm/llm.py:280-354` — The `while True:` loop in `atext_request` has grown complex. Adding probe/record logic inline will increase its line count further. A future refactor could extract `_do_probe()` and `_do_record()` as private async helpers. Note for post-implementation cleanup.
- `agentsociety/cityagent/blocks/mobility_block.py` — The 8 `atext_request` call sites each repeat the same 3-line `context={}` dict construction. After Step 6, each will grow by 3 more lines. A helper method `self._make_llm_context(func_name, prompt_name, state_dict)` on the `Block` base class would centralize this. Not a blocker.
- `agentsociety/prompts/prompt_manager.py:410` — `get_prompt_template()` and `format_prompt()` both look up `self._loaded_prompts[prompt_name]` with no shared helper. The new `get_prompt_identity()` and `get_text_input_fields()` methods add to this pattern. A private `_get_prompt_data(name)` helper with a clear error would clean this up.

## Proposed Next Steps

1. **Add `[outputs]` sections to all 33 prompt TOML files** (Step 1) — purely mechanical, no code risk. Do this first so the TOML schema is complete before any code reads it. Classify each prompt carefully using the table above.

2. **Implement `QdrantCacheConfig`** in `agentsociety/llm/qdrant_cache_config.py` and add the field to `EnvConfig` at `agentsociety/configs/env.py:43` (Step 2). Minimal change.

3. **Add three new methods to `PromptManager`** (`get_prompt_identity`, `get_text_input_fields`, `get_output_schema`, `is_cache_eligible`) at `agentsociety/prompts/prompt_manager.py` (Step 5). No side effects; can be tested in isolation.

4. **Implement `QdrantCacheActor`** in `agentsociety/llm/qdrant_cache_actor.py` (Step 3). Adapt `MultiFeatureQdrantChampionCache` from the snippets file. Use `QdrantClient(path=...)`, per-prompt cache instances, dense embeddings.

5. **Extend `LLMContext` and `LLM.atext_request`** (Step 4). Add the probe/record logic inside `atext_request`. Verify the skip condition for tool-calling requests (`isinstance(tools, NotGiven)`).

6. **Update all block call sites** (Step 6) — 8 block files + `societyagent.py`. The change at each call site is mechanical: add three keys to the `context={}` dict.

7. **Wire into `InfrastructureManager`** (Step 7) — add `_init_llm_cache_actor()`, update `initialize_all()`, update `_init_core_components()`, update `close()`.

8. **Add `llm_cache_tool` to agent toolbox** in `simulationengine.py` (Step 8).

9. **Add cache metrics** to `PrometheusActor` and `MetricsTracker` (Step 9).

10. **Update `agentsociety/llm/__init__.py`** exports (Step 10).

11. **Validate end-to-end**: Run a short simulation with `env.qdrant_cache.enabled: true`. Inspect Qdrant collection sizes, call `get_stats()` via Ray, verify JSON stats file written on shutdown, verify Prometheus metrics visible in Grafana.
