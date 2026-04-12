# Adaptive LLM Routing
> Replace the uniform Big LLM call path with a three-tier routing system — CatBoost for structured prediction, SLM+LoRA for text generation, Big LLM as fallback — to reduce total Big LLM token consumption by 10x while preserving population-level statistical indistinguishability.

---

## Purpose & Motivation

Every LLM call in the simulation goes through `LLM.atext_request()` in
`agentsociety/llm/llm.py:609`. With populations of hundreds to thousands of agents
running for multiple simulated days, the Big LLM becomes the sole bottleneck: the
C++ city simulator completes a tick in milliseconds while a single simulation day
takes hours because of wall-clock LLM latency and API cost.

The goal is to make the simulator runnable on consumer hardware with affordable API
bills, enabling community adoption. The mechanism: for any given prompt template,
after collecting enough responses from the Big LLM, learn whether the output is
predictable enough that a cheaper model can substitute without degrading
population-level statistics.

Why now: the recent addition of `PromptManager` (
`agentsociety/prompts/prompt_manager.py`) and the `PromptResponseRecord` telemetry
pipeline (`agentsociety/database/schema.py:22`) give us structured, named, and
archived prompt data for the first time. This feature builds on both.

---

## Success Criteria

1. Total Big LLM input+output token count decreases by 10x or more across a
   representative multi-day simulation run.
2. Population-level output statistics (need satisfaction distributions, mobility
   destination category distributions, daily schedule patterns, Big Five
   initialization distributions) are statistically indistinguishable from a
   baseline run that used only the Big LLM, measured across N agents over a
   multi-day run.
3. The routing system is transparent: every call that was served by CatBoost or
   SLM is recorded so it can be audited.
4. When confidence thresholds are not met, the system falls back to the Big LLM
   silently, never producing degraded output.

---

## Scope

**In scope:**
- Enhanced TOML schema: `[inputs.X]` tables with `type`/`description`/`categories`,
  and `[outputs]` section with field schemas
- `ResponseStatisticsCollector`: collects and persists per-template response
  statistics into two new database tables
- `LLMRouter`: rule-table-based routing class, called internally from
  `LLM.atext_request()`
- `CatBoostPredictor`: one `CatBoostClassifier`/`CatBoostRegressor` per output field
  per template, with confidence gating
- `SLMPredictor`: vLLM multi-LoRA inference wrapper with context-window overflow
  fallback to Big LLM
- `OnlineFineTuner`: dedicated class triggered during simulation for CatBoost
  re-training and LoRA adapter fine-tuning on new data from the telemetry tables
- `template_name` field added to `LLMContext` TypedDict
- All `atext_request()` call sites in `cityagent/blocks/` updated to pass
  `template_name` in the context dict

**Out of scope:**
- Shadow mode (user explicitly rejected)
- Logprob-based entropy gating (user explicitly rejected)
- Joint multi-output CatBoost models (per-field independent models chosen instead)
- Dispatcher block routing (tools/function-calling path in `LLM.atext_request()` —
  see Rejected Approaches)
- Any UI or API exposure of routing decisions
- Distributed fine-tuning across multiple GPUs (single-machine only in v1)

---

## Constraints

- No changes to the public API of `LLM.atext_request()` — routing is internal
- Must not break ClickHouse-absent (DuckDB fallback) configurations
- Fine-tuning compute is environment-dependent; all hardware parameters are
  configurable, never hardcoded
- Sample thresholds, variance thresholds, and confidence gates are configurable
  parameters, not magic constants
- CatBoost and vLLM are optional dependencies; the system must degrade gracefully
  (fall back to Big LLM) if they are not installed

---

## Architecture and Integration Points

The feature spans five new modules and touches four existing ones.

### New modules

| Module | Location |
|--------|----------|
| `ResponseStatisticsCollector` | `agentsociety/routing/statistics.py` |
| `LLMRouter` | `agentsociety/routing/router.py` |
| `CatBoostPredictor` | `agentsociety/routing/catboost_predictor.py` |
| `SLMPredictor` | `agentsociety/routing/slm_predictor.py` |
| `OnlineFineTuner` | `agentsociety/routing/fine_tuner.py` |
| Package init | `agentsociety/routing/__init__.py` |

### Existing files touched

- `agentsociety/llm/llm.py:36` — `LLMContext` TypedDict: add `template_name: str`
  field
- `agentsociety/llm/llm.py:609` — `LLM.atext_request()`: delegate to
  `LLMRouter.route()` before dispatching to `LLMActor`
- `agentsociety/prompts/prompt_manager.py:32` — `PromptManager`: add methods to
  read `[inputs.X]` tables and `[outputs]` section from TOML data
- `agentsociety/database/schema.py` — two new `TypedDict`s:
  `TemplateStatisticsRecord` and `RouterDecisionRecord`
- `agentsociety/database/clickhouse.py` and `duckdb.py` — new `insert_*` methods
  and table registrations for the two new records
- `agentsociety/database/database_actor.py` — expose the two new insert methods as
  Ray remote methods
- `agentsociety/database/migrations/` — two new SQL migration files
- `agentsociety/cityagent/blocks/` (all block files listed below) — add
  `template_name` to every `context={}` dict passed to `atext_request()`

### Call chain (current)

```
Block.forward() in any cityagent/blocks/*.py
  → self.llm.atext_request(dialog, context={block_name, func_name, agent_id})
      in agentsociety/llm/llm.py:609
    → server selection loop  (llm.py:658)
    → self._actors[actor_i].call.remote(...)  (llm.py:728)
    → self._db_actor.insert_prompt_response_record.remote(...)  (llm.py:807)
```

### Call chain (after this feature)

```
Block.forward() in any cityagent/blocks/*.py
  → self.llm.atext_request(dialog, context={block_name, func_name, agent_id,
                                             template_name})
      in agentsociety/llm/llm.py:609
    → LLMRouter.route(template_name, dialog, context, **kwargs)
        in agentsociety/routing/router.py
      ├── [if template_name is known and profiled]
      │   ├── [output_type == regression or classification AND confident]
      │   │   → CatBoostPredictor.predict(template_name, features)
      │   │       in agentsociety/routing/catboost_predictor.py
      │   │   → record RouterDecisionRecord(tier="catboost") → DatabaseActor
      │   │   → return prediction  ← (Big LLM never called)
      │   │
      │   └── [output_type == text]
      │       → SLMPredictor.generate(template_name, dialog, max_tokens)
      │           in agentsociety/routing/slm_predictor.py
      │       ├── [context window fits] → vLLM LoRA inference → return
      │       └── [context overflow]   → fall through to Big LLM
      │
      └── [fallback: template unknown, not profiled, or not confident]
          → existing server selection loop  (llm.py:658)
          → self._actors[actor_i].call.remote(...)
          → ResponseStatisticsCollector.record(template_name, inputs, response)
              in agentsociety/routing/statistics.py
          → return result
    → self._db_actor.insert_prompt_response_record.remote(...)  (llm.py:807)
      [unchanged — records all responses regardless of tier]
```

---

## Enhanced TOML Schema

### Current schema

The current TOML files (`agentsociety/prompts/blocks/mobilityblock/
mobility_place_type_selection_agentsociety_v1_0.toml:1`) have:

```toml
[metadata]
name = "mobility_place_type_selection"
version = "1.0.0"
origin = "agentsociety"
description = "..."

[inputs]
required = ["plan", "intention", "poi_category", ...]

[prompt]
input = "..."
```

The `[inputs]` section is a flat list of names. There is no type information and
no `[outputs]` section.

### New schema (additive, fully backward-compatible)

The existing `required` list is preserved unchanged so that
`PromptManager.get_required_fields()` (`prompt_manager.py:152`) continues to work
without modification.

New sections are added:

```toml
[metadata]
name = "mobility_place_type_selection"
version = "1.1.0"
origin = "citysim"
description = "..."

[inputs]
required = ["plan", "intention", "poi_category", "household", "openness", ...]

# New: typed input declarations (optional; used by statistics collector)
[inputs.plan]
type = "text"
description = "The agent's daily plan."

[inputs.household]
type = "categorical"
categories = ["single", "couple", "family", "roommates"]

[inputs.openness]
type = "ordinal"
categories = [1, 2, 3]   # 1=Low, 2=Medium, 3=High

# New: output schema (used by statistics collector and CatBoost predictor)
[outputs.place_type]
type = "categorical"
categories = ["shopping", "dining", "recreation", "work", "home", "other"]
description = "The selected primary POI category."
```

**Type vocabulary for both inputs and outputs:**

| type | Description |
|------|-------------|
| `text` | Free-form string |
| `categorical` | Unordered discrete set; `categories` list required |
| `ordinal` | Ordered discrete set; `categories` list required |
| `continuous` | Real-valued scalar |
| `json` | Structured JSON object (text generation tier) |

**Tier derivation rule (read from `[outputs]`):**
- Any template whose `[outputs]` section contains only `categorical`, `ordinal`,
  or `continuous` fields → **CatBoost tier** (once profiled and confident)
- Any template whose `[outputs]` section contains at least one `text` or `json`
  field → **SLM tier**
- Any template with no `[outputs]` section → **Big LLM only** (never routed)

### PromptManager changes

`PromptManager` in `agentsociety/prompts/prompt_manager.py:32` gains two new
methods:

```python
def get_input_schema(self, prompt_name: str) -> dict[str, dict]:
    """Return the [inputs.X] table for each declared input field.
    Returns {} if no typed declarations exist (backward-compatible)."""

def get_output_schema(self, prompt_name: str) -> dict[str, dict]:
    """Return the [outputs] section.
    Returns {} if not present (backward-compatible)."""
```

These methods read from `self._loaded_prompts[prompt_name]` which already holds
the full parsed TOML dict (`prompt_manager.py:38`).

---

## Response Statistics System

### Purpose

Before routing can be activated for a template, the system must establish that:
1. Enough responses have been collected (minimum sample size met)
2. The responses show enough regularity (low variance) that a cheaper model can
   substitute reliably

Statistics are collected passively on every Big LLM call that falls through to the
existing `LLMActor` path.

### What is collected

After every successful Big LLM response where `template_name` is known and an
output schema exists, `ResponseStatisticsCollector.record()` is called. It
maintains an **in-memory rolling window** per template (to avoid per-call database
writes) and periodically flushes aggregated statistics.

For each template, the collector tracks per-output-field statistics:

| Output field type | Statistic collected |
|-------------------|-------------------|
| `categorical` / `ordinal` | Response frequency distribution (counts per category), entropy of the distribution |
| `continuous` | Mean, variance, coefficient of variation |
| `text` / `json` | Mean pairwise BM25 cosine similarity across a sample of responses |

Additionally, for all types, the collector performs **input-feature differentiation
analysis**: it clusters collected responses into groups based on subsets of input
features (using categorical binning for `categorical`/`ordinal` inputs and
quartile binning for `continuous` inputs). For each cluster, it computes the same
per-field statistics. This reveals whether separate LoRA adapters per feature
cluster are needed.

### Storage: two new database tables

#### `template_statistics` table

Stores the latest aggregate statistics per template and per output field.

New TypedDict in `agentsociety/database/schema.py`:

```python
class TemplateStatisticsRecord(TypedDict):
    exp_id: str
    template_name: str           # metadata.name from TOML
    output_field: str            # key from [outputs] section
    output_type: str             # categorical / ordinal / continuous / text / json
    sample_count: int            # total responses collected
    last_updated: datetime
    # Structured statistics (JSON-encoded)
    distribution_json: str       # for categorical/ordinal: {category: count, ...}
    entropy: float               # for categorical/ordinal
    mean: float                  # for continuous (NaN if not applicable)
    variance: float              # for continuous (NaN if not applicable)
    similarity_mean: float       # for text/json: mean pairwise BM25 similarity
    # Input differentiation analysis (JSON-encoded)
    cluster_analysis_json: str   # {feature_key: {cluster_label: {stats}}}
    is_profiled: bool            # True once sample_count >= min_sample_count
    routing_tier: str            # "catboost" / "slm" / "big_llm" / "pending"
```

#### `router_decisions` table

Records every routing decision for auditability.

```python
class RouterDecisionRecord(TypedDict):
    exp_id: str
    simulation_step: int
    timestamp: datetime
    agent_id: int
    template_name: str
    tier_used: str              # "catboost" / "slm" / "big_llm"
    reason: str                 # "not_profiled" / "low_confidence" /
                                #  "context_overflow" / "catboost_confident" /
                                #  "slm_text" / etc.
    input_tokens_saved: int     # estimated tokens saved vs Big LLM (0 for big_llm)
```

### Migration files

`agentsociety/database/migrations/0014_create_template_statistics.sql` and
`agentsociety/database/migrations/0015_create_router_decisions.sql`.

Both backends (ClickHouse and DuckDB) must implement the corresponding create
statements and insert methods. The `ClickHouseDatabase` and `DuckDBDatabase`
classes in `agentsociety/database/clickhouse.py:56` and
`agentsociety/database/duckdb.py` follow identical patterns: add table schema to
`self.table_schemas`, implement `insert_template_statistics_record()` and
`insert_router_decision_record()`, then expose both through `DatabaseActor`
(`agentsociety/database/database_actor.py:22`) as Ray remote methods.

### Configurable parameters

All thresholds live in a new `RoutingConfig` Pydantic model (added to
`agentsociety/configs/__init__.py` and made an optional field on the top-level
`Config` model at `agentsociety/configs/__init__.py:65`):

```python
class RoutingConfig(BaseModel):
    enabled: bool = False                          # Off by default
    min_sample_count: int = 1000                   # Min responses before profiling
    categorical_entropy_threshold: float = 1.5     # Max entropy to allow CatBoost
    continuous_cv_threshold: float = 0.3           # Max CV to allow CatBoost
    text_similarity_threshold: float = 0.7         # Min BM25 similarity for SLM
    catboost_confidence_threshold: float = 0.85    # Min CatBoost predict_proba
    cluster_min_size: int = 100                    # Min cluster size for analysis
    statistics_flush_interval: int = 500           # Flush stats every N records
    slm_max_context_tokens: int = 4096             # Overflow boundary for SLM
    slm_base_url: Optional[str] = None             # vLLM endpoint for SLM
    slm_model: Optional[str] = None                # Base SLM model name
    fine_tuning_interval_steps: int = 5000         # Fine-tune every N sim steps
    fine_tuning_min_new_records: int = 500         # Min new records to trigger FT
    catboost_models_dir: str = "routing/catboost"  # Relative to home_dir
    lora_adapters_dir: str = "routing/lora"        # Relative to home_dir
```

---

## Routing Rule Table

`LLMRouter` (`agentsociety/routing/router.py`) implements a deterministic rule
table. No machine learning is used for the routing decision itself — the rules are
derived directly from statistics and schema type.

### Decision procedure (evaluated in order)

```
Given: template_name, dialog, context kwargs

1. If template_name is None or not in PromptManager → Big LLM (reason: "no_template")
2. If output_schema is empty (no [outputs] section) → Big LLM (reason: "no_output_schema")
3. If statistics.is_profiled(template_name) is False → Big LLM (reason: "not_profiled")
4. If routing_tier == "catboost":
     a. Extract input features from dialog using input_schema
     b. For each output field: call CatBoostPredictor.predict(template_name, field, features)
     c. If all fields return confidence >= catboost_confidence_threshold → return predictions
        (reason: "catboost_confident")
     d. Else → Big LLM (reason: "low_confidence")
5. If routing_tier == "slm":
     a. Estimate prompt token count
     b. If token_count > slm_max_context_tokens → Big LLM (reason: "context_overflow")
     c. If SLMPredictor not available (not installed) → Big LLM (reason: "slm_unavailable")
     d. Else → SLMPredictor.generate(template_name, dialog)
        (reason: "slm_text")
6. Default → Big LLM (reason: "fallback")
```

The routing tier for a template is stored in `template_statistics.routing_tier`
and is set by `ResponseStatisticsCollector` once profiling is complete. The
`LLMRouter` reads this value at route time; it does not re-derive it on every call.

### Feature extraction for CatBoost

When routing to CatBoost, the router must reconstruct the input feature vector from
the rendered dialog string. The input schema in the TOML `[inputs.X]` tables
provides the feature names and types. The router uses a lightweight regex-based
parser to extract values from the rendered prompt text (since the prompt is already
formatted by `PromptManager.format_prompt()` before `atext_request()` is called).

The feature vector is a flat dict: `{field_name: value}` where value is the
category label (for categorical/ordinal) or a float (for continuous). Fields
declared as `text` in the input schema are excluded from the CatBoost feature
vector (CatBoost handles categorical features natively via its
`cat_features` parameter; text features are too high-dimensional for this tier).

---

## CatBoost Integration

### One model per output field per template

For a template with output schema:
```toml
[outputs.place_type]
type = "categorical"
```

The system trains one `CatBoostClassifier` model, keyed by
`(template_name, output_field)` = `("mobility_place_type_selection", "place_type")`.

For a continuous output field, a `CatBoostRegressor` is trained instead.

Model files are stored at:
`{home_dir}/{catboost_models_dir}/{template_name}__{output_field}.cbm`

### Training data

Training data is read from the `prompt_responses` table (ClickHouse or DuckDB) by
joining `template_name` (from `func_name` or the new `template_name` column — see
below) with `static_agent_attributes` on `agent_id` to obtain demographic features.
The response column is parsed to extract the output field value.

### Confidence gating

`CatBoostPredictor.predict()` returns `(value, confidence)`. For classifiers,
confidence is `predict_proba().max()`. For regressors, confidence is derived from
the prediction interval width relative to the training distribution variance; if
the interval is narrow enough (configurable), confidence is set to 1.0, otherwise
to a scaled value.

If confidence < `catboost_confidence_threshold` for any field in the template,
the router falls back to the Big LLM for the entire call. There is no partial
substitution within a single call.

### Storage

Trained CatBoost models are persisted to disk in `.cbm` format using
`model.save_model(path)`. They are loaded at simulation startup if they exist, and
updated by `OnlineFineTuner` during the simulation.

---

## SLM / LoRA Integration

### Architecture

`SLMPredictor` wraps a vLLM `AsyncLLMEngine` (or a vLLM OpenAI-compatible
endpoint via `AsyncOpenAI` with `base_url=slm_base_url`). The latter is preferred
because it decouples the fine-tuning process from the inference process and avoids
in-process GPU contention.

vLLM's multi-LoRA support allows a single vLLM server to host the base SLM and
switch LoRA adapters per request using the `model` parameter in the completion
request. Each adapter is keyed by `template_name` (from `metadata.name` in the
TOML). The adapter path is:
`{home_dir}/{lora_adapters_dir}/{template_name}/`

### Context window overflow handling

Before sending to SLM, `SLMPredictor.generate()` calls a lightweight token counter
(using the base SLM tokenizer, loaded once at startup). If the estimated token
count of the dialog exceeds `slm_max_context_tokens`, the method returns `None`
and the router falls back to the Big LLM. This is recorded as
`reason: "context_overflow"` in the `router_decisions` table.

### VRAM configuration

`SLMPredictor` is initialized with `slm_base_url` and `slm_model` from
`RoutingConfig`. The vLLM server itself is launched and managed externally (not
by the simulator). VRAM allocation is entirely the operator's responsibility.
The `SLMPredictor` is effectively stateless from the simulator's perspective — it
is a thin async HTTP client.

---

## Online Fine-Tuner

### Design

`OnlineFineTuner` (`agentsociety/routing/fine_tuner.py`) is a standalone class (not
a Ray actor) that is owned by `SimulationEngine`. It is called periodically during
the simulation via a hook in the main simulation step loop.

### Trigger conditions

Fine-tuning is triggered when both of the following are true:
1. `current_sim_step % fine_tuning_interval_steps == 0`
2. New records since last fine-tuning run >=
   `fine_tuning_min_new_records` for at least one template

### CatBoost re-training

For each profiled template with `routing_tier == "catboost"`:
1. Query `prompt_responses` for all records where `func_name` matches the
   `template_name` (or the new `template_name` column once it exists), joined
   with `static_agent_attributes` on `agent_id`
2. Parse response JSON to extract output field values
3. Re-train the CatBoost model from scratch using all available data
4. If new model's cross-validation accuracy on a held-out 20% split is equal to
   or better than the previous model, replace the model file on disk and update
   `CatBoostPredictor`'s in-memory model
5. Otherwise, keep the old model and log a warning

Re-training is done synchronously in the `OnlineFineTuner` call (blocking the
calling coroutine). The CatBoost training call is wrapped in
`asyncio.get_event_loop().run_in_executor(None, ...)` to avoid blocking the event
loop.

### LoRA fine-tuning

For each profiled template with `routing_tier == "slm"`:
1. Query `prompt_responses` for records matching the template
2. Format into instruction-tuning pairs: `(prompt_text, response_text)`
3. Run a PEFT/LoRA fine-tuning step using `transformers` + `peft` libraries on
   the base SLM model checkpoint
4. Save the updated adapter to
   `{home_dir}/{lora_adapters_dir}/{template_name}/`
5. If a vLLM endpoint is configured, call the vLLM management API to hot-reload
   the updated adapter

LoRA fine-tuning is also run in an executor to avoid blocking the event loop.

### SimulationEngine integration point

In `agentsociety/simulation/simulationengine.py`, the existing step loop (wherever
`AgentManager` ticks agents forward) gains a post-step hook:

```python
# After each simulation step:
if self._routing_config.enabled:
    await self._fine_tuner.maybe_fine_tune(current_step)
```

`OnlineFineTuner` is instantiated in `SimulationEngine.__init__()` alongside the
existing `LLM`, `AgentManager`, and `DatabaseActor` objects.

---

## LLM Integration Point

### `LLMContext` extension

`agentsociety/llm/llm.py:36` currently:

```python
class LLMContext(TypedDict, total=False):
    block_name: str
    func_name: str
    agent_id: str
```

After this feature, one field is added:

```python
class LLMContext(TypedDict, total=False):
    block_name: str
    func_name: str
    agent_id: str
    template_name: str    # NEW: value of metadata.name from the TOML file
```

This is `total=False` so all existing call sites that do not pass `template_name`
continue to compile and run without modification. Missing `template_name` means
`routing_tier` will be `"big_llm"` with reason `"no_template"`.

### `LLM.atext_request()` modification

At `agentsociety/llm/llm.py:609`, immediately after the function signature, before
the `while True:` server selection loop, the routing delegation is inserted:

```python
# Early in atext_request(), before server selection loop:
template_name = (context or {}).get("template_name")
if self._router is not None and template_name:
    result = await self._router.route(
        template_name=template_name,
        dialog=dialog,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
        context=context,
    )
    if result is not None:
        # Record the routing decision; do NOT call Big LLM
        return result
# Fall through to existing server selection loop
```

`self._router` is an optional `LLMRouter` instance, set to `None` by default and
injected at `LLM.__init__()` when `RoutingConfig.enabled` is `True`. This means
the feature is entirely off unless explicitly enabled.

### `LLM.__init__()` change

`agentsociety/llm/llm.py:433` gains an optional `routing_config` parameter:

```python
def __init__(
    self,
    configs: List[LLMConfig],
    num_actors: int = max(cpu_count() * 2, 32),
    metrics_actor: Optional[PrometheusActor] = None,
    db_actor: Optional[DatabaseActor] = None,
    routing_config: Optional[RoutingConfig] = None,   # NEW
):
```

If `routing_config` is provided and `routing_config.enabled` is `True`, `LLM`
constructs `LLMRouter`, `CatBoostPredictor`, `SLMPredictor`, and
`ResponseStatisticsCollector` and wires them together.

### Call site updates in blocks

Every `atext_request()` call in `agentsociety/cityagent/blocks/` must add
`template_name` to the context dict. The following files contain calls that need
updating (identified from grep results):

| File | Number of call sites |
|------|---------------------|
| `agentsociety/cityagent/blocks/mobility_block.py` | 6 |
| `agentsociety/cityagent/blocks/needs_block.py` | 4 |
| `agentsociety/cityagent/blocks/cognition_block.py` | 6 |
| `agentsociety/cityagent/blocks/economy_block.py` | 4 |
| `agentsociety/cityagent/blocks/plan_block.py` | 2 |
| `agentsociety/cityagent/blocks/social_block.py` | 2 |
| `agentsociety/cityagent/blocks/daily_schedule_block.py` | 2 |
| `agentsociety/cityagent/blocks/other_block.py` | 2 |
| `agentsociety/cityagent/societyagent.py` | 3 (status_summary, etc.) |

In each case, the context dict already contains `block_name` and `func_name`. The
`template_name` is already stored as a string attribute of the block (e.g.,
`self.type_selection_prompt_name = "mobility_place_type_selection"` at
`mobility_block.py:67`). So the change at each call site is minimal:

```python
# Before:
context={"block_name": "PlaceSelectionBlock", "func_name": "select_type",
         "agent_id": self.id}

# After:
context={"block_name": "PlaceSelectionBlock", "func_name": "select_type",
         "agent_id": self.id,
         "template_name": self.type_selection_prompt_name}
```

The dispatcher path (tool-calling calls in `agentsociety/agent/dispatcher.py`)
does NOT get `template_name` — dispatcher prompts are not in the TOML prompt
system and do not have output schemas, so they will never be routed away from the
Big LLM.

---

## `template_name` column in `prompt_responses`

The `PromptResponseRecord` in `agentsociety/database/schema.py:22` currently has
no `template_name` field. Fine-tuning queries (and statistics collection) join on
`func_name` as a proxy, but `func_name` is not identical to `template_name` in all
cases.

A migration `0016_alter_prompt_responses_add_template_name.sql` adds a nullable
`template_name` column to `prompt_responses`. The
`ClickHouseDatabase.insert_prompt_response_record()` at `clickhouse.py:361` and
its DuckDB counterpart gain an optional `template_name: Optional[str]` parameter.
`DatabaseActor.insert_prompt_response_record()` at `database_actor.py:85` is
updated to accept and pass through this parameter. `LLM.atext_request()` at
`llm.py:807` already passes `func_name` from context; it now also passes
`template_name` when present.

---

## Trade-Offs

| Gain | Cost / Risk |
|------|-------------|
| 10x token reduction on profiled templates | Cold-start period: first N=`min_sample_count` calls per template still go to Big LLM |
| CatBoost inference is microseconds vs seconds for LLM | Additional complexity in `LLM.atext_request()` — the routing gate adds a conditional branch |
| SLM inference is local and cheap | Requires a vLLM server running externally; complexity of LoRA adapter management |
| Feature is off by default (`enabled: False`) | Engineers must explicitly configure it; no automatic benefit without configuration |
| Routing decisions are auditable via `router_decisions` table | Additional database writes per call (mitigated by batching in existing `_queue_record` mechanism) |
| Modular: CatBoost and SLM are optional imports | Dependency management: catboost, vllm, peft, transformers are not currently in pyproject.toml |
| Online fine-tuning adapts to population shifts | Fine-tuning uses CPU/GPU time during simulation; if `fine_tuning_interval_steps` is too low, it will compete with agent ticks |
| Per-field independent CatBoost models are more accurate | More model files to manage; disk space scales with (templates × output fields) |

---

## Rejected Approaches

**Logprob-based entropy gating**
Route based on model-reported token probability distributions. Rejected because the
user has empirically tried this and found it unreliable. The model's reported
confidence does not correlate well with actual output regularity across population.

**Joint multi-output CatBoost model**
Train one model that predicts all output fields simultaneously. Rejected because
output fields within a single template may not co-vary (e.g., `place_type` and
`transport_mode` are independent given the same inputs). Independent models per
field are more accurate and compositionally clearer.

**Routing the dispatcher / tool-calling path**
The `BlockDispatcher` in `agentsociety/agent/dispatcher.py` also uses
`atext_request()` with tools and `tool_choice`. This path cannot be routed to
CatBoost or SLM because it relies on structured JSON function-call syntax that only
the Big LLM reliably produces. Routing the dispatcher would require a completely
different approach (fine-tuning for function-calling) and is out of scope.

**Shadow mode (run both tiers and compare per-call)**
Proposed to validate routing quality. Rejected by the user. Validation is done
post-hoc at the population level (Q2: statistical indistinguishability), not
per-call.

**Single monolithic `RouterActor` as a Ray actor**
Considered making the entire router a Ray remote actor so it could be shared across
all agent Ray actors. Rejected because CatBoost inference is CPU-local and
sub-millisecond — the Ray overhead of a remote call would dwarf the inference time.
Instead, `LLMRouter` is a plain Python object owned by `LLM`, which is already
shared across agents via `AgentToolbox`. `ResponseStatisticsCollector` uses the
existing `DatabaseActor` for persistence to avoid adding another Ray actor.

**Logistic regression / random forest instead of CatBoost**
CatBoost is chosen because: (1) it handles mixed categorical+continuous features
natively without one-hot encoding overhead, (2) it provides well-calibrated
`predict_proba`, (3) it trains fast on small datasets (hundreds to thousands of
samples), and (4) it requires minimal hyperparameter tuning.

**Hardcoded thresholds**
All statistics thresholds (entropy, CV, similarity, confidence) were considered as
constants. Rejected in favor of `RoutingConfig` because the optimal values are
empirically unknown and will differ across simulation setups, cities, and
population sizes.

---

## Assumptions and Open Questions

**Assumptions:**

1. The rendered prompt text (after `PromptManager.format_prompt()`) reliably
   contains the input field values in a form that the regex-based feature extractor
   can recover. This is true for the current templates but may not hold for future
   templates with heavily transformed inputs.

2. `func_name` in existing `prompt_responses` records is a reliable proxy for
   `template_name` for the purpose of bootstrapping training data before the new
   `template_name` column is fully populated. This needs to be verified per block.

3. The `PromptResponseRecord.response` column stores the raw LLM output string,
   which is parseable as JSON for templates that return JSON. This is true today
   but is not enforced by a schema.

4. Running `OnlineFineTuner` synchronously (in executor) every
   `fine_tuning_interval_steps` will not cause agent tick timeouts. If fine-tuning
   takes longer than a simulation step, it will delay ticks. This needs measurement
   before setting a default interval.

**Open questions requiring empirical tuning:**

1. What is the right `min_sample_count`? 1000 is the default but may be too low
   (noisy statistics) or too high (slow cold-start). Needs measurement against
   actual Big LLM response distributions.

2. What `categorical_entropy_threshold` correctly separates "predictable" from
   "genuinely variable" templates? Template `mobility_place_type_selection` likely
   has moderate entropy (depends heavily on `intention`); `cognition_initialize_big5`
   likely has low entropy (demographics → personality is deterministic). Needs
   empirical measurement.

3. Which templates will actually reach the CatBoost tier vs. remaining in the
   SLM or Big LLM tier? The answer depends on population demographics and which
   input features dominate. Unknown without running the profiling phase.

4. Is BM25 cosine similarity a reliable proxy for semantic equivalence in
   `text`-type outputs (e.g., `social_message_generation`)? If messages are
   topically similar but syntactically varied, BM25 will underestimate similarity.
   Dense embedding similarity (already supported via `fastembed` in the codebase)
   could be a fallback, but adds cost.

5. What base SLM model should be used? The plan does not prescribe a specific
   model family. This is environment-dependent and must be specified in
   `RoutingConfig.slm_model`.

6. Will CatBoost confidence degrade over time as the simulated population evolves
   (e.g., income changes, personality drift)? If so, the re-training interval may
   need to be adaptive rather than fixed.

---

## Code That Could Be Refactored (informational)

- `agentsociety/llm/llm.py:807` — The `insert_prompt_response_record.remote()` call
  is inside `atext_request()` but only fires when `self._metrics_actor is not None`.
  This makes it easy to miss when `metrics_actor` is not configured. Consider
  making the DB write unconditional (guarded only on `self._db_actor is not None`).
  This is directly relevant because the statistics collector depends on
  `prompt_responses` being populated.

- `agentsociety/prompts/prompt_manager.py:159` — `build_agent_state()` is a 200-line
  method with a large explicit `elif` chain for known field names. As typed input
  schemas are added to TOMLs, this method's explicit field list will grow stale.
  A longer-term refactor would make field resolution data-driven (driven by the
  TOML input schema itself), but this is not required for this feature.

- `agentsociety/database/schema.py` — All `TypedDict` classes are in one flat file.
  As two more are added, grouping by subsystem (agent data, routing data) would
  improve navigability. No action required now.

---

## Proposed Next Steps

Steps are ordered by dependency. Each step can be reviewed and merged independently.

**Step 1: TOML schema extension + PromptManager methods**
- Add `[inputs.X]` typed declarations and `[outputs]` section to all existing TOML
  files in `agentsociety/prompts/blocks/` and `agentsociety/prompts/societyagent/`
- Add `get_input_schema()` and `get_output_schema()` to
  `agentsociety/prompts/prompt_manager.py`
- No routing logic yet. Purely additive.

**Step 2: `LLMContext.template_name` + call site updates**
- Add `template_name: str` to `LLMContext` at `agentsociety/llm/llm.py:36`
- Update every `atext_request()` context dict in `agentsociety/cityagent/blocks/`
  and `agentsociety/cityagent/societyagent.py` (28 call sites across 9 files)
- Add `template_name` to `insert_prompt_response_record()` signature in
  `agentsociety/database/clickhouse.py:361`, `duckdb.py`, `database_actor.py:85`,
  and `llm.py:807`
- Write migration `0016_alter_prompt_responses_add_template_name.sql`

**Step 3: `RoutingConfig` model + `template_statistics` and `router_decisions` tables**
- Define `RoutingConfig` in `agentsociety/configs/`
- Add `TemplateStatisticsRecord` and `RouterDecisionRecord` to
  `agentsociety/database/schema.py`
- Implement insert methods in both ClickHouse and DuckDB backends
- Write migrations 0014 and 0015
- Expose through `DatabaseActor`

**Step 4: `ResponseStatisticsCollector`**
- Implement `agentsociety/routing/statistics.py`
- Wire into `LLM.atext_request()` on the Big LLM success path
- Validate statistics are written to the database correctly

**Step 5: `LLMRouter` (rule table only, Big LLM passthrough)**
- Implement `agentsociety/routing/router.py` with the full decision procedure
- Initially, all templates route to Big LLM (no CatBoost or SLM yet)
- This validates the routing gate with zero functional change

**Step 6: `CatBoostPredictor`**
- Implement `agentsociety/routing/catboost_predictor.py`
- Wire into `LLMRouter`
- Validate on a single template first (e.g., `mobility_place_type_selection`)

**Step 7: `OnlineFineTuner` (CatBoost only)**
- Implement the CatBoost re-training path in `agentsociety/routing/fine_tuner.py`
- Wire into `SimulationEngine` step loop
- Validate that models improve over simulation time

**Step 8: `SLMPredictor` + LoRA fine-tuning**
- Implement `agentsociety/routing/slm_predictor.py` against a vLLM endpoint
- Add LoRA fine-tuning to `OnlineFineTuner`
- This step requires a running vLLM server; validate on text-output templates
  (e.g., `social_message_generation`)

**Step 9: End-to-end validation**
- Run a full N-agent multi-day simulation with `routing.enabled: true`
- Measure token reduction against baseline
- Run statistical tests on population-level output distributions
- Tune thresholds in `RoutingConfig` based on empirical results
