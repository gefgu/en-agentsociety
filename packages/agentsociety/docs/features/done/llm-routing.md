# LLM Routing
> Route specific LLM calls to a designated model based on prompt identity, configured entirely in YAML without changing any agent or block code.

---

## Purpose & Motivation

City-scale simulations with 1,000+ agents make LLM calls at every tick for every agent. Many of these calls are high-frequency and structurally simple. The `societyagent_status_summary` prompt is the canonical example: it generates a 1–2 sentence free-text description stored in memory and surfaced in the UI, but it does not affect downstream reasoning, need updates, or block dispatch.

Routing these calls to a small, locally-hosted model (e.g., a Qwen 500M served via vLLM) eliminates API cost for the highest-frequency non-tool call in the simulation — approximately N_agents × N_ticks calls — with zero change to any block, agent, or prompt code.

---

## Success Criteria

- Calls for configured `prompt_identity` keys go to the designated model instead of the round-robin pool, with zero change to callers.
- When the feature is disabled (no routing config), behavior is byte-for-byte identical to today.
- The `societyagent_status_summary` prompt, which runs once per agent per tick, is demonstrably served by the small model (verifiable via token counts or logging).
- No change is required to any `Block`, `Agent`, `PromptManager`, or caller of `self.llm.atext_request`.

---

## Scope

**In scope:**
- A `RoutedLLMEntry` Pydantic model that extends `LLMConfig` with a `prompt_identities: list[str]` field.
- An optional `routing: list[RoutedLLMEntry]` field on `Config` (and optionally `IndividualConfig`).
- A `RoutingLLM` wrapper class in `agentsociety/llm/routing_llm.py` that intercepts `atext_request` and dispatches by `prompt_identity[0]`.
- Construction of `RoutingLLM` inside `InfrastructureManager._init_core_components` when routing config is present.
- Routing for any prompt identity string declared in config; `societyagent_status_summary` is the first target use case.

**Out of scope:**
- Online fine-tuning (deferred — see section below).
- Shadow mode or agreement-based fallback to the big model.
- Fallback to the big model on small-model error (replacement mode only: if configured, it is used).
- Changing `PromptManager`, any `Block`, `SocietyAgent`, or any other caller.
- Serving or deploying the routed model — it must already be running as a vLLM-compatible OpenAI endpoint.

---

## Constraints

- The `LLM.atext_request` signature at `agentsociety/llm/llm.py:420` must not change — `RoutingLLM` must present the identical interface.
- `LLMConfig.validate_configuration` at `agentsociety/llm/llm.py:94` currently enforces that `base_url` is only accepted when `provider == VLLM`. The routed model is always a vLLM server, so this constraint is already satisfied; no validator changes are needed.
- The feature must be opt-in: `Config.routing` defaults to `[]` or `None`, and the existing `LLM` path is untouched when it is absent.
- Tool-use calls (block dispatcher) must never be routed. Routing applies only when `tools is NOT_GIVEN`.

---

## Architecture & Integration Points

The feature touches exactly three layers.

### 1. Config layer

- `agentsociety/configs/__init__.py:68` — `Config.llm: List[LLMConfig]` is the existing pool. A new optional field `routing: list[RoutedLLMEntry] = []` is added on the same model. Each `RoutedLLMEntry` is an `LLMConfig` subclass with one additional field.

### 2. LLM layer

- `agentsociety/llm/llm.py:34` — `LLMContext` TypedDict. The field `prompt_identity: tuple[str, str, str]` at line 38 is the routing key source. `prompt_identity[0]` is the prompt name string (e.g., `"societyagent_status_summary"`).
- `agentsociety/llm/llm.py:420` — `LLM.atext_request` is the single dispatch point. `RoutingLLM` wraps this class and overrides only this method.
- `agentsociety/llm/llm.py:101` — `LLM.__init__` constructs `self._actors` (the Ray actor pool) and `self._load_balancer`. `RoutingLLM` will instantiate a second `LLM` for each configured routed entry using the same constructor, so no pool construction logic needs to be duplicated.
- `agentsociety/llm/__init__.py:3` — exports `LLM`, `LLMConfig`. `RoutingLLM` and `RoutedLLMEntry` are added to this export list.

### 3. Infrastructure layer

- `agentsociety/simulation/infrastructuremanager.py:437` — `_init_core_components` constructs `self._llm = LLM(...)` at line 440. After this line, if `self._config.routing` is non-empty, `self._llm` is replaced with a `RoutingLLM` instance that wraps the just-created base `LLM`.
- `agentsociety/simulation/infrastructuremanager.py:47` — `self._llm: Optional[LLM]` is the field read by all downstream consumers. Because `RoutingLLM` satisfies the `LLM` interface, no consumer changes are needed.

### Call chain for `societyagent_status_summary`

```
AgentBase._run()                          agent_base.py:460
  -> SocietyAgent.status_summary()        societyagent.py:252
  -> self.llm.atext_request(dialog, context={"prompt_identity": ("societyagent_status_summary", ...)})
                                          llm.py:420
  -> [RoutingLLM intercepts here]
  -> small_llm.atext_request(same args)   routing_llm.py (new)
  -> memory.status.update("status_summary", result)
                                          societyagent.py:291
  -> DataRecorder.collect_agents()        datarecorder.py (reads "status_summary" for storage)
```

This call runs once per agent per tick. It is the highest-frequency non-tool call in the simulation.

---

## Similar Patterns & Reuse

### Pattern 1: `LLMContext.prompt_identity` as a routing key

- **What it is**: `agentsociety/llm/llm.py:38 — prompt_identity: tuple[str, str, str]` inside `LLMContext`
- **What it does**: Carries prompt metadata (name, origin, version) from the call site to the cache and metrics layer without changing callers
- **How this feature uses it**: `RoutingLLM.atext_request` reads `context["prompt_identity"][0]` and checks it against the configured route set

### Pattern 2: `LLM` instantiated a second time for a different config

- **What it is**: `agentsociety/simulation/infrastructuremanager.py:468` — `MessageInterceptor(self._config.llm)` creates a second LLM-consuming object from a different config list
- **What it does**: Shows the pattern of holding a second LLM-configured object alongside the main one
- **How this feature uses it**: `RoutingLLM.__init__` creates one `LLM` instance per `RoutedLLMEntry` using the same `LLM.__init__` constructor, reusing all actor pool and load balancer logic

### Pattern 3: `_init_llm_cache_actor` guard pattern

- **What it is**: `agentsociety/simulation/infrastructuremanager.py:401 — _init_llm_cache_actor()`
- **What it does**: Guards on a config flag, constructs a Ray actor, and assigns to an instance field; gracefully skips if disabled
- **How this feature uses it**: The routing LLM construction in `_init_core_components` follows the same guard idiom: check `self._config.routing`, skip if empty, otherwise wrap

---

## Implementation Strategy

### Step 1: Add `RoutedLLMEntry` to the config layer

**File**: `agentsociety/configs/__init__.py`

**Before**: `Config` has `llm: List[LLMConfig]` at line 68 only.

**After**: Add before `Config`:

```python
from ..llm import LLMConfig, RoutedLLMEntry   # RoutedLLMEntry added to llm exports

class Config(BaseModel):
    llm: List[LLMConfig] = Field(..., min_length=1)
    routing: list[RoutedLLMEntry] = Field(default=[])
    ...
```

`RoutedLLMEntry` is a subclass of `LLMConfig` with one additional field:

```python
class RoutedLLMEntry(LLMConfig):
    prompt_identities: list[str] = Field(..., min_length=1)
    """Prompt identity names (prompt_identity[0]) that this LLM handles."""
```

Because `RoutedLLMEntry` subclasses `LLMConfig`, it inherits `provider`, `base_url`, `api_key`, `model`, `concurrency`, `timeout`, and the `validate_configuration` validator. A vLLM routed entry sets `provider = "vllm"` and provides `base_url` — exactly as any existing vLLM entry does today.

A YAML config entry looks like:

```yaml
routing:
  - provider: vllm
    base_url: "http://localhost:8001/v1"
    api_key: "unused"
    model: "Qwen/Qwen2.5-0.5B-Instruct"
    concurrency: 50
    prompt_identities:
      - "societyagent_status_summary"
```

### Step 2: Implement `RoutingLLM` in the LLM layer

**File**: `agentsociety/llm/routing_llm.py` (new file)

`RoutingLLM` wraps a base `LLM` instance and holds a dict mapping prompt identity strings to dedicated `LLM` instances.

```python
class RoutingLLM(LLM):
    def __init__(
        self,
        base_llm: LLM,
        routing_entries: list[RoutedLLMEntry],
        # forward remaining kwargs for interface compatibility
        metrics_actor=None,
        db_actor=None,
        cache_actor=None,
        cache_skip_mode=False,
    ):
        # Do NOT call super().__init__() — we hold a pre-built base_llm
        self._base_llm = base_llm
        self._routes: dict[str, LLM] = {}
        for entry in routing_entries:
            small_llm = LLM(
                [entry],  # LLMConfig list with one entry
                metrics_actor=metrics_actor,
                db_actor=db_actor,
                cache_actor=cache_actor,
                cache_skip_mode=cache_skip_mode,
            )
            for key in entry.prompt_identities:
                self._routes[key] = small_llm

    async def atext_request(self, dialog, ..., context=None):
        if (
            context is not None
            and "prompt_identity" in context
            and isinstance(tools, NotGiven)
        ):
            key = context["prompt_identity"][0]
            if key in self._routes:
                return await self._routes[key].atext_request(dialog, ..., context=context)
        return await self._base_llm.atext_request(dialog, ..., context=context)

    # Proxy all other LLM public attributes to base_llm
    @property
    def prompt_tokens_used(self):
        return self._base_llm.prompt_tokens_used + sum(
            llm.prompt_tokens_used for llm in self._routes.values()
        )

    @property
    def completion_tokens_used(self):
        return self._base_llm.completion_tokens_used + sum(
            llm.completion_tokens_used for llm in self._routes.values()
        )
```

Notes on the implementation:
- `RoutedLLMEntry` subclasses `LLMConfig`, so it can be passed directly as `[entry]` to `LLM.__init__` at `llm.py:101`. No constructor changes required.
- Multiple entries that share the same `prompt_identity` key: last entry wins (dict assignment). This is consistent with Python dict semantics and should be documented.
- If `tools` is not `NOT_GIVEN` (i.e., it is a list), the call is always delegated to `_base_llm` regardless of `prompt_identity`. This ensures block dispatch is never routed.
- `RoutedLLMEntry` is defined in `llm.py` alongside `LLMConfig` (same file) rather than in a new file, to avoid a circular import between `configs/__init__.py` and `llm/`. It is added to `llm/__init__.py` exports.

### Step 3: Update `LLM` exports

**File**: `agentsociety/llm/llm.py:25` — add `RoutedLLMEntry` to `__all__`.

**File**: `agentsociety/llm/__init__.py:3` — add `RoutedLLMEntry` to the import and `__all__`.

### Step 4: Modify `InfrastructureManager._init_core_components`

**File**: `agentsociety/simulation/infrastructuremanager.py:437`

**Before** (line 440):
```python
self._llm = LLM(
    self._config.llm,
    metrics_actor=self._metrics_actor,
    db_actor=self._db_actor,
    cache_actor=self._llm_cache_actor,
    cache_skip_mode=self._config.env.qdrant_cache.skip_mode,
)
```

**After**: Append immediately after the `LLM` construction block:
```python
if self._config.routing:
    get_logger().info(
        f"LLM routing enabled for {sum(len(e.prompt_identities) for e in self._config.routing)} prompt key(s)"
    )
    self._llm = RoutingLLM(
        base_llm=self._llm,
        routing_entries=self._config.routing,
        metrics_actor=self._metrics_actor,
        db_actor=self._db_actor,
        cache_actor=self._llm_cache_actor,
        cache_skip_mode=self._config.env.qdrant_cache.skip_mode,
    )
```

`RoutingLLM` is added to the import at `infrastructuremanager.py:20`:
```python
from ..llm import LLM, QdrantCacheActor, RoutingLLM
```

The `self._llm: Optional[LLM]` field declaration at line 47 requires no change because `RoutingLLM` is a subclass of `LLM`.

---

## Metrics

### How token tracking works today

Token tracking in the existing stack has two independent paths:

**Path 1 — instance counters (in-process).**
`LLM._record_request_log` at `agentsociety/llm/llm.py:269` increments `self.prompt_tokens_used` and `self.completion_tokens_used` (plain `int` fields on the `LLM` instance, set in `__init__` at `llm.py:137-138`). These are read at the end of a simulation run (e.g., for logging final totals). They are not Prometheus metrics.

**Path 2 — Prometheus (fire-and-forget remote call).**
`LLM._record_success_metrics_and_db` at `agentsociety/llm/llm.py:289` calls `self._metrics_actor.record_block_performance.remote(token_input=..., token_output=...)`. This goes to `PrometheusActor.record_block_performance` at `agentsociety/performance/prometheusActor.py:26`, which delegates to `BlockPerformance.record_performance` at `agentsociety/performance/BlockPerformance.py:29`. `BlockPerformance` maintains the `performance_tokens_total` Counter at `BlockPerformance.py:23` with labels `[exp_id, direction, actor, block_name, func_name, agent_id]`.

There is no `model` or `prompt_identity` label on `performance_tokens_total` today. The `actor` label is hardcoded to `"llm"` for all LLM calls (`_record_success_metrics_and_db` at `llm.py:306`).

A separate `RoutingTrackerActor` exists at `agentsociety/performance/RoutingTracker.py:9` and is called via `PrometheusActor.record_routing` at `prometheusActor.py:46`. It tracks routing call counts (`routing_llm_calls_total`) by `block_name/func_name/routed` but does not carry token counts.

### What `RoutingLLM` changes about this picture

When `RoutingLLM` dispatches a call to `_routes[key].atext_request(...)`, the inner `LLM` instance (the "small" model) calls `_record_success_metrics_and_db` with the same `metrics_actor`. That means Prometheus already receives token counts for routed calls — but they are indistinguishable from base-model calls. Both are emitted as `actor="llm"` with no label indicating which physical model handled the request.

The `prompt_identity[0]` string is available in `context` at the time `_record_success_metrics_and_db` is called (it is part of `LLMContext`), but it is not currently forwarded to the counter.

### Required changes

#### 1. Add a `model_role` field to `LLMContext`

**File**: `agentsociety/llm/llm.py:34`

Add one optional field to the `LLMContext` TypedDict:

```python
class LLMContext(TypedDict, total=False):
    ...
    model_role: str   # "base" or "routed"; absent means "base"
```

This field is set by `RoutingLLM.atext_request` before delegating to the inner `LLM`:

```python
# In RoutingLLM.atext_request, on the routed branch:
context = dict(context) if context else {}
context["model_role"] = "routed"
return await self._routes[key].atext_request(dialog, ..., context=context)
```

No caller outside `RoutingLLM` sets this field. When routing is disabled (plain `LLM` is used directly), `model_role` is absent, and the metrics layer treats it as `"base"`.

#### 2. Add a `model_role` label to `performance_tokens_total` and `performance_block_calls_total`

**File**: `agentsociety/performance/BlockPerformance.py:23`

Extend both Counters with a `model_role` label:

```python
self.calls = Counter(
    "performance_block_calls_total",
    "Number of calls to blocks",
    ["exp_id", "block_name", "func_name", "agent_id", "actor", "model_role"],
)
self.token_counter = Counter(
    "performance_tokens_total",
    "Number of tokens processed by LLMs",
    ["exp_id", "direction", "actor", "block_name", "func_name", "agent_id", "model_role"],
)
```

`record_performance` receives `model_role: str = "base"` as a new parameter and passes it through to `.labels(...)`.

#### 3. Thread `model_role` through `_record_success_metrics_and_db`

**File**: `agentsociety/llm/llm.py:289`

`_record_success_metrics_and_db` already reads `context` to extract `block_name`, `func_name`, and `agent_id`. Add:

```python
model_role = metric_context.get("model_role", "base")
```

Pass `model_role` into `record_block_performance.remote(...)`:

```python
self._metrics_actor.record_block_performance.remote(
    duration=end_time - start_time,
    actor="llm",
    model_role=model_role,
    token_input=log["input_tokens"],
    token_output=log["output_tokens"],
    block_name=metric_context.get("block_name", "unknown"),
    func_name=metric_context.get("func_name", "unknown"),
    agent_id=metric_context.get("agent_id", "unknown"),
)
```

#### 4. Update `PrometheusActor.record_block_performance`

**File**: `agentsociety/performance/prometheusActor.py:26`

Add `model_role: str = "base"` to the signature and forward it to `BlockPerformance.record_performance`:

```python
def record_block_performance(
    self,
    block_name: str,
    func_name: str,
    duration: float,
    actor: Literal["llm", "modernbert", "catboost"],
    agent_id: str,
    token_input: int,
    token_output: int,
    model_role: str = "base",
) -> None:
    self.blockPerformance.record_performance(
        block_name, func_name, duration, actor, agent_id,
        token_input, token_output, model_role=model_role,
    )
```

The default `"base"` ensures backward compatibility: all existing callers (e.g., any non-LLM actor that calls `record_block_performance`) continue to work without change.

#### 5. Add a `prompt_identity` label to a dedicated token counter

The `performance_tokens_total` counter already has `block_name` and `func_name`, which together identify the call site. Adding `prompt_identity` as a sixth label would create high cardinality (one series per unique prompt name × block × func × agent × direction × model_role). A safer approach is a separate, lighter counter:

**File**: `agentsociety/performance/MetricsTracker.py`

Add a new counter to `MetricsTracker.__init__`:

```python
self.llm_tokens_by_prompt = Counter(
    "llm_tokens_by_prompt_total",
    "Token usage broken down by prompt identity and model role",
    ["exp_id", "prompt_name", "direction", "model_role"],
)
```

Add a corresponding method:

```python
def record_llm_tokens_by_prompt(
    self,
    prompt_name: str,
    token_input: int,
    token_output: int,
    model_role: str = "base",
) -> None:
    self.llm_tokens_by_prompt.labels(
        exp_id=self.exp_id,
        prompt_name=prompt_name,
        direction="input",
        model_role=model_role,
    ).inc(token_input)
    self.llm_tokens_by_prompt.labels(
        exp_id=self.exp_id,
        prompt_name=prompt_name,
        direction="output",
        model_role=model_role,
    ).inc(token_output)
```

Expose it on `PrometheusActor` at `prometheusActor.py`:

```python
def record_llm_tokens_by_prompt(
    self,
    prompt_name: str,
    token_input: int,
    token_output: int,
    model_role: str = "base",
) -> None:
    self.metricsTracker.record_llm_tokens_by_prompt(
        prompt_name, token_input, token_output, model_role
    )
```

#### 6. Call the new counter from `_record_success_metrics_and_db`

**File**: `agentsociety/llm/llm.py:289`

After the existing `record_block_performance.remote(...)` call, add:

```python
prompt_name = str(context["prompt_identity"][0]) if (
    context is not None and "prompt_identity" in context
) else "unknown"
self._metrics_actor.record_llm_tokens_by_prompt.remote(
    prompt_name=prompt_name,
    token_input=log["input_tokens"],
    token_output=log["output_tokens"],
    model_role=model_role,
)
```

This fires for every successful LLM call (routed or not). When routing is disabled, `model_role` is `"base"` and `prompt_name` comes from the existing `prompt_identity` in context — which is always set for block-originated calls.

### Resulting Prometheus surface

After these changes, the following time series are available:

| Metric | Labels | Purpose |
|---|---|---|
| `performance_tokens_total` | `exp_id, direction, actor, block_name, func_name, agent_id, model_role` | Per-block token counts, split by which model pool handled it |
| `performance_block_calls_total` | `exp_id, block_name, func_name, agent_id, actor, model_role` | Per-block call counts, split by model pool |
| `llm_tokens_by_prompt_total` | `exp_id, prompt_name, direction, model_role` | Aggregate token counts by prompt identity and model pool (the primary cost-tracking metric) |
| `routing_llm_calls_total` | `exp_id, block_name, func_name, routed, agent_id` | Routing decision counts (already exists, unchanged) |

### Backward compatibility

- The `model_role` parameter defaults to `"base"` everywhere. Existing call sites (non-LLM actors, any direct `record_block_performance` calls outside this feature) pass no `model_role` and get label value `"base"` automatically.
- Adding a new label to an existing Counter is a breaking change in Prometheus (existing recorded series will not have the new label and will stop matching queries). The `performance_tokens_total` and `performance_block_calls_total` counters were introduced in this codebase fork and are not published externally, so this is acceptable. Any existing Grafana dashboards targeting these counters will need to add `model_role=~".*"` to their label matchers.
- `llm_tokens_by_prompt_total` is a new counter and has no backward-compatibility burden.

### Why not intercept at `RoutingLLM` level instead

`RoutingLLM` could record its own token metrics by inspecting the result before returning it. This was rejected because:

- Token counts are only available inside `LLM._record_request_log` after the raw API response is parsed. `RoutingLLM` delegates the full call to the inner `LLM`, so it never sees `log["input_tokens"]`.
- Duplicating token extraction in `RoutingLLM` would require parsing the OpenAI response object, which is already done inside `LLMActor` and surfaced via the `log` dict — only visible inside `LLM.atext_request`.
- The `context` mutation approach (setting `model_role` before delegation) is a one-line change that threads through the existing metrics path cleanly without any duplication.

---

## Trade-Offs

| Gain | Cost |
|---|---|
| Eliminates API cost for the highest-frequency non-tool call | Small model output quality is uncertain; status summary is purely presentational, so this is acceptable |
| Zero change to any caller, block, or prompt | Two separate LLM pools (base + one per routed entry) → slightly more Ray actor overhead |
| Graceful no-op when routing is not configured | `RoutingLLM` adds a thin dispatch layer on every `atext_request`; overhead is negligible (one dict lookup) |
| Extensible to any prompt identity via config | Config becomes slightly more complex; a `routing` section is a new concept |
| Replacement mode keeps logic simple | No fallback: if the routed model is down or misconfigured, those prompts fail rather than silently falling back |
| Token metrics split by model_role and prompt_identity | Adding `model_role` label to existing counters breaks existing Prometheus queries; dashboards need label-matcher updates |

The replacement-mode-only decision (no fallback to big model on error) is intentional: it keeps the routing logic trivially simple. The downside is that a misconfigured or unavailable small model will cause agent failures for the affected prompt. This is acceptable for an opt-in feature used in controlled simulation environments.

---

## Rejected Approaches

### Approach: Add `prompt_identities` field directly to `LLMConfig`

**Why rejected**: `LLMConfig` is a general-purpose config used for every provider entry in the pool. Adding an optional `prompt_identities` field to it would mix routing concerns into the base config, making it possible to accidentally configure routing on a main-pool entry. A separate `RoutedLLMEntry` subclass makes the distinction explicit and allows Pydantic validation to require the field.

### Approach: Separate top-level `routing_llm` config key with a nested `LLMConfig`

**Why rejected**: This was the approach in the previous plan draft. Using a list of `RoutedLLMEntry` (each extending `LLMConfig`) is cleaner because it allows multiple models to be routed simultaneously without nesting and matches the existing `llm: list[LLMConfig]` pattern already on `Config`.

### Approach: Add routing inside `LLMActor`

**Why rejected**: `LLMActor` at `agentsociety/llm/llm_actor.py` is a Ray remote actor. Routing inside it would spread the decision across a Ray message boundary, require passing configs for both models on every call, and make the logic harder to test. A local Python wrapper is the correct location.

### Approach: Add a second `llm_routed` field to `AgentToolbox`

**Why rejected**: `AgentToolbox` at `agentsociety/agent/toolbox.py` is shared across all agents. Exposing a second LLM there would require all blocks and agents to be aware of routing. Routing must be transparent to callers.

### Approach: Modify `Block.build_llm_prompt_context` to select the model

**Why rejected**: `Block.build_llm_prompt_context` at `agentsociety/agent/block.py` builds the context dict but does not make LLM calls. Routing at the block level would scatter routing policy across every block file. Centralizing it in `RoutingLLM` keeps the policy in one place.

### Approach: Shadow mode (call both models, compare, use big model result)

**Why rejected**: Shadow mode was part of the original fine-tuning-inclusive plan. With fine-tuning out of scope, shadow mode provides no value — its only purpose was to generate training pairs. Replacement mode is simpler and sufficient.

### Approach: Record token metrics inside `RoutingLLM.atext_request` directly

**Why rejected**: `RoutingLLM` delegates to an inner `LLM` and never sees the raw `log` dict that contains parsed token counts. Token extraction happens inside `LLMActor` (the Ray actor) and surfaces only via `log["input_tokens"]` / `log["output_tokens"]` inside `LLM.atext_request`. Duplicating that extraction in `RoutingLLM` would require re-parsing the OpenAI response object, which is coupling to internal `LLMActor` behavior. The context mutation approach is cleaner.

---

## Assumptions & Open Questions

### Assumptions

1. The routed model is already running as a vLLM-compatible OpenAI endpoint at a known URL before the simulation starts. This feature does not handle model download or vLLM process startup.
2. `societyagent_status_summary` output is purely presentational: it goes to `memory.status["status_summary"]` and then to `DataRecorder` for UI display. It does not influence any downstream LLM call, need calculation, or plan generation. This was confirmed during the original plan's codebase exploration.
3. A `RoutedLLMEntry` is always `provider = VLLM`. The existing `LLMConfig.validate_configuration` at `llm.py:94` already enforces that `base_url` requires `provider == VLLM`, so this is enforced by the inherited validator with no extra code.

### Open Questions

**Q1: Should `IndividualConfig` (the task-solving engine) also get a `routing` field?**
`IndividualConfig` at `configs/__init__.py:100` mirrors `Config` but uses `IndividualEngine`. The same routing mechanism would apply there. It is out of scope for this plan but the implementation is trivially identical — add `routing: list[RoutedLLMEntry] = []` to `IndividualConfig` and apply the same `_init_core_components` logic in `IndividualEngine`. Defer until needed.

**Q2: Token accounting across base and routed pools.**
`LLM.prompt_tokens_used` and `completion_tokens_used` are plain integer counters on the instance (`llm.py:137-138`). `RoutingLLM` must aggregate these across all constituent `LLM` instances. The proposed implementation does this with `@property` aggregators. Verify that callers (e.g., `simulationengine.py`) read these fields rather than accumulating them themselves. Note that the Prometheus path (`performance_tokens_total`) is separate from these instance counters and is not affected by the aggregation — each inner `LLM` emits its own metrics independently.

**Q3: Prometheus label cardinality for `agent_id`.**
The existing `performance_tokens_total` counter already includes `agent_id`, which in a 1,000-agent simulation produces 1,000 × N_prompts × 2 (directions) × 2 (model_roles) time series. Adding `model_role` doubles the existing cardinality. This is unlikely to be a practical problem for the Prometheus instance in the Docker Compose stack, but should be noted for large-scale deployments. The new `llm_tokens_by_prompt_total` counter deliberately omits `agent_id` to stay low-cardinality.

---

## Code That Could Be Refactored *(informational)*

- `agentsociety/llm/llm.py:101` — `LLM.__init__` builds the actor pool and load balancer inline. If a future feature needs to create a pool without a full `LLM`, extracting a `_build_actor_pool(configs) -> list[LLMActor]` helper would be useful. Not a blocker here because `RoutingLLM` instantiates full `LLM` objects.
- `agentsociety/cityagent/societyagent.py:252` — `status_summary()` calls `self.llm.atext_request` with no `max_tokens`. For a small routed model, adding `max_tokens=100` would prevent runaway generation on unconstrained text output. This improvement is independent of routing and should be made regardless.
- `agentsociety/llm/llm.py:38` — `LLMContext` is a `TypedDict`. The `prompt_identity` field is a plain 3-tuple with no named accessors. A small named tuple or dataclass would make `[0]` accesses self-documenting. Not a blocker.
- `agentsociety/performance/RoutingTracker.py:9` — `RoutingTrackerActor` tracks routing call counts but not token counts. Now that `llm_tokens_by_prompt_total` covers per-prompt token breakdowns, `RoutingTrackerActor` is partially redundant. It could be merged into `MetricsTracker` in a future cleanup, but is not a blocker.

---

## Deferred: Online Fine-Tuning

The original version of this plan included a `FineTuningActor` Ray actor for online gradient updates during simulation. This was removed from scope because:

- Fine-tuning during simulation requires a GPU process running alongside vLLM inference; these cannot share the same vLLM process without custom tooling.
- The agreement metric for free-text outputs (status summary is `type = "text"`) is non-trivial: exact match is 0% for semantically equivalent outputs; embedding similarity or LLM-as-judge adds significant complexity.
- The cost during fine-tuning is 2× the tokens (small model call + big model call for ground truth), which defeats the cost-saving purpose until convergence.

Fine-tuning is a valid future feature. When it is revisited, the `RoutingLLM` wrapper is the natural insertion point: a `FineTuningActor` ref can be added to `RoutingLLM.__init__` and called fire-and-forget after each routed response, without changing any other code. The interface described in the previous plan draft is a reasonable starting point.

---

## Proposed Next Steps

1. Define `RoutedLLMEntry` in `agentsociety/llm/llm.py` alongside `LLMConfig` and export it from `agentsociety/llm/__init__.py`.
2. Add `routing: list[RoutedLLMEntry] = []` to `Config` in `agentsociety/configs/__init__.py`.
3. Create `agentsociety/llm/routing_llm.py` implementing `RoutingLLM` as described above. In `RoutingLLM.atext_request`, set `context["model_role"] = "routed"` on the copied context before delegating to the inner `LLM`.
4. Add `model_role: str` to `LLMContext` at `agentsociety/llm/llm.py:34`.
5. Add `llm_tokens_by_prompt_total` Counter to `MetricsTracker` at `agentsociety/performance/MetricsTracker.py` and expose `record_llm_tokens_by_prompt` on `PrometheusActor` at `agentsociety/performance/prometheusActor.py`.
6. Add `model_role` label to `performance_tokens_total` and `performance_block_calls_total` in `agentsociety/performance/BlockPerformance.py`. Update `record_performance` signature and all `.labels(...)` calls.
7. Thread `model_role` through `LLM._record_success_metrics_and_db` at `agentsociety/llm/llm.py:289`: read from `context`, pass to `record_block_performance.remote(...)` and `record_llm_tokens_by_prompt.remote(...)`.
8. Modify `agentsociety/simulation/infrastructuremanager.py:_init_core_components` to wrap `self._llm` when `self._config.routing` is non-empty.
9. Update any Grafana dashboards that query `performance_tokens_total` or `performance_block_calls_total` to add `model_role=~".*"` to their label matchers (or split by `model_role` to see base vs. routed breakdown).
10. Validate by running a simulation with `societyagent_status_summary` routed to a local vLLM instance and confirming: (a) zero calls go to the big model for that prompt, (b) `llm_tokens_by_prompt_total{prompt_name="societyagent_status_summary", model_role="routed"}` accumulates tokens in Prometheus, (c) `llm_tokens_by_prompt_total{model_role="base"}` shows reduced counts for that prompt name, (d) status summaries appear in the UI.
