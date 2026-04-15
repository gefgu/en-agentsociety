# LLM Routing + Online Fine-Tuning
> Route specific prompt-keyed LLM calls to a smaller specialized model, and continuously improve that model online by comparing its outputs against the large model.

---

## Purpose & Motivation

City-scale simulations with 1,000+ agents make LLM calls at every tick for every agent. Many of those calls are low-stakes, high-frequency, and structurally simple — the `societyagent_status_summary` prompt is a canonical example: it generates a 1–2 sentence free-text description that is stored in memory and surfaced in the UI, but does not affect downstream reasoning or simulation state in a safety-critical way.

Routing these calls to a small, locally-hosted model (e.g., Qwen 500M served via vLLM) would:
- Reduce token cost by eliminating API calls for ~N_agents × N_ticks occurrences
- Reduce latency on slow paths if the small model is colocated
- Provide a real-world reinforcement signal for online fine-tuning experiments

The online fine-tuning component is explicitly experimental: the small model should improve during simulation by learning from disagreements with the large model.

---

## Success Criteria

- Routing: calls for the configured prompt key(s) go to the small model instead of the large model, with zero change to callers (blocks, agents, dispatcher)
- Correctness: the large model is still used as ground truth when the small model's confidence or agreement rate falls below a threshold
- Observability: per-prompt routing decisions are logged and exposed to Prometheus
- Fine-tuning: the small model receives (prompt, big-model-response) training pairs online; checkpoints are saved to disk at configurable intervals
- All existing behavior is unchanged when the feature is disabled (opt-in via config)

---

## Scope

**In scope:**
- A `RoutingLLM` wrapper that sits in front of `LLM` and dispatches calls by `prompt_identity` key
- A `SmallModelConfig` Pydantic model added alongside `LLMConfig` in `configs/__init__.py`
- A `FineTuningActor` Ray actor that receives (prompt, response) pairs and runs async gradient updates on the small model
- Integration via `InfrastructureManager._init_core_components` — the `RoutingLLM` replaces or wraps `self._llm`
- Routing only for the `societyagent_status_summary` prompt as the first target; extensible to any prompt key via config

**Out of scope:**
- Changing the `PromptManager`, `Block`, `SocietyAgent`, or any caller of `self.llm.atext_request` — all routing is transparent
- Distributed multi-node fine-tuning
- Serving the fine-tuned model to other experiments automatically
- Production deployment of the fine-tuned checkpoint (out of simulation scope)

---

## Constraints

- All routing and fine-tuning must be non-blocking relative to the simulation tick loop; training is async and fire-and-forget from the simulation's perspective
- The `LLM` interface (`atext_request` signature) must not change — callers must require zero modification
- The system must be opt-in and gracefully degrade to the existing `LLM` when unconfigured
- The small model is assumed to be served locally via vLLM and accessed via the OpenAI-compatible API (already supported via `LLMProviderType.VLLM`)
- Tool-use calls (dispatcher) must never be routed to the small model; routing applies only to non-tool `atext_request` calls

---

## Architecture & Integration Points

The feature touches exactly three layers:

1. **LLM layer** — where routing logic lives
2. **Config layer** — where the small model and routing rules are declared
3. **Infrastructure layer** — where the `RoutingLLM` and `FineTuningActor` are initialized

### LLM Layer

- `agentsociety/llm/llm.py:101` — `LLM.__init__` and `LLM.atext_request` are the target for wrapping. The `atext_request` method at line 420 already receives an `Optional[LLMContext]` parameter that contains `prompt_identity: tuple[str, str, str]` (line 38). This tuple's first element is the prompt name (e.g., `"societyagent_status_summary"`). This is the routing key.

- `agentsociety/llm/llm.py:420` — `atext_request` is the single point where all LLM calls pass. A `RoutingLLM` subclass or wrapper at this method is the minimal-touch insertion point.

- `agentsociety/llm/llm_actor.py:62` — `LLMActor` is a Ray remote actor. Each `LLM` instance owns a pool of `LLMActor` instances. The `RoutingLLM` would own a second pool for the small model.

### Config Layer

- `agentsociety/configs/__init__.py:65` — `Config` has `llm: List[LLMConfig]`. A new optional field `routing_llm: Optional[RoutingLLMConfig]` would be added here. `RoutingLLMConfig` contains: the small model `LLMConfig`, the list of prompt keys to route, and fine-tuning parameters.

### Infrastructure Layer

- `agentsociety/simulation/infrastructuremanager.py:437` — `_init_core_components` creates `self._llm = LLM(self._config.llm, ...)`. This is where `RoutingLLM` would be constructed instead, wrapping the base `LLM` with the small model reference.

- `agentsociety/simulation/infrastructuremanager.py:477` — `initialize_all` is the ordered initialization sequence. A `_init_fine_tuning_actor` call would be added here, analogous to `_init_llm_cache_actor` at line 483.

### Call Chain for `status_summary`

```
SocietyAgent.status_summary()       societyagent.py:252
  → LLM.atext_request(dialog, context={"prompt_identity": ("societyagent_status_summary", ...)})
                                     llm.py:420
  → [RoutingLLM intercepts here]
  → SmallLLMActorPool or self._base_llm.atext_request(...)
  → memory.status.update("status_summary", summary_text)
                                     societyagent.py:291
  → DataRecorder.collect_agents()    datarecorder.py:156 reads "status_summary" for storage
```

`status_summary()` is called at the end of every agent tick via `agent_base.py:460`:
```
AgentBase._run()   agent_base.py:460  → await self.status_summary()
```

This means it runs once per agent per tick. At 1,000 agents this is 1,000 LLM calls per tick — the highest-frequency non-tool call in the simulation.

---

## Similar Patterns & Reuse

### Pattern 1: QdrantCacheActor as a Ray actor sidecar

- **What it is**: `agentsociety/llm/cache/ray_actor.py:22 — QdrantCacheActor`
- **What it does**: A Ray remote actor that intercepts LLM calls by `prompt_identity`, serves cached results, and records misses for future training
- **How this feature uses it**: The `FineTuningActor` follows the same pattern — a Ray remote actor that receives (prompt, result) pairs via `.remote()` calls from `RoutingLLM`, completely async

### Pattern 2: LLMContext.prompt_identity as a routing key

- **What it is**: `agentsociety/llm/llm.py:38 — LLMContext TypedDict with field prompt_identity: tuple[str, str, str]`
- **What it does**: Carries prompt metadata (name, origin, version) from the call site to the cache and metrics layer without changing callers
- **How this feature uses it**: `RoutingLLM.atext_request` checks `context["prompt_identity"][0]` against the configured route set; if it matches and tools are NOT_GIVEN, it delegates to the small model pool

### Pattern 3: InfrastructureManager actor initialization pattern

- **What it is**: `agentsociety/simulation/infrastructuremanager.py:401 — _init_llm_cache_actor()`
- **What it does**: Guard on config flag, construct Ray remote actor, wrap in `CustomTool`, assign to instance field
- **How this feature uses it**: `_init_fine_tuning_actor()` follows the identical pattern; `_init_routing_llm()` is called inside `_init_core_components()` after the base `LLM` is built

### Pattern 4: LLMLoadBalancer for concurrency management

- **What it is**: `agentsociety/llm/load_balancer.py:14 — LLMLoadBalancer`
- **What it does**: Manages per-provider in-flight slot counts, cooldown, and circuit breaking
- **How this feature uses it**: The small model pool reuses `LLMLoadBalancer` without modification; the small model's `LLMConfig` sets an independent `concurrency` value

---

## Implementation Strategy

### Step 1: Add `RoutingLLMConfig` to the config layer

**Before**: `agentsociety/configs/__init__.py:65` — `Config` has `llm: List[LLMConfig]` only.

**After**: Add:
```python
class RoutingLLMConfig(BaseModel):
    small_model: LLMConfig
    routed_prompt_keys: list[str]          # e.g. ["societyagent_status_summary"]
    fallback_on_error: bool = True         # if small model fails, fall back to big model
    fine_tuning: Optional[FineTuningConfig] = None

class FineTuningConfig(BaseModel):
    enabled: bool = False
    checkpoint_dir: str
    checkpoint_interval_steps: int = 100
    learning_rate: float = 1e-5
    max_buffer_size: int = 1000            # ring buffer of training pairs
```

`Config.routing_llm: Optional[RoutingLLMConfig] = None` is added to `agentsociety/configs/__init__.py:65`.

### Step 2: Implement `RoutingLLM` in the LLM layer

**Before**: `agentsociety/llm/llm.py:101` — `LLM` is a standalone class.

**After**: Create `agentsociety/llm/routing_llm.py` containing `RoutingLLM` which holds:
- `_base_llm: LLM` — the existing big-model LLM, used as fallback and ground truth
- `_small_llm: LLM` — a second `LLM` instance initialized from `RoutingLLMConfig.small_model`
- `_routed_keys: set[str]` — the set of `prompt_identity[0]` values that should go to the small model
- `_fine_tuning_actor: Optional[FineTuningActor]` — Ray actor ref; called fire-and-forget

`RoutingLLM.atext_request` logic:
1. If `context` is None or `tools` is not `NOT_GIVEN`: delegate to `_base_llm.atext_request`
2. If `context["prompt_identity"][0]` is not in `_routed_keys`: delegate to `_base_llm.atext_request`
3. Else: call `_small_llm.atext_request` with the same arguments
4. If `_fine_tuning_actor` is not None: fire-and-forget `_fine_tuning_actor.record.remote(context, small_result)` — the actor will later call the big model to get the ground truth and generate a training pair
5. Return the small model's result

`RoutingLLM` exposes the same public API as `LLM` (`atext_request`, `prompt_tokens_used`, `completion_tokens_used`) so callers need no changes.

The new file attaches to existing code via:
- `agentsociety/llm/__init__.py` — export `RoutingLLM`
- `agentsociety/simulation/infrastructuremanager.py:440` — conditional construction

### Step 3: Modify `InfrastructureManager._init_core_components`

**Before**: `infrastructuremanager.py:440` — unconditionally creates `LLM(self._config.llm, ...)`.

**After**: After the base `LLM` is created, check `self._config.routing_llm`. If set, construct `RoutingLLM(base_llm=self._llm, routing_config=..., fine_tuning_actor=self._fine_tuning_actor)` and reassign `self._llm`. All downstream consumers receive the `RoutingLLM` transparently because `AgentToolbox.llm` is typed as `LLM` and `RoutingLLM` satisfies that interface.

### Step 4: Implement `FineTuningActor` (online fine-tuning)

**Before**: No fine-tuning component exists.

**After**: Create `agentsociety/llm/finetuning_actor.py` containing:

```python
@ray.remote
class FineTuningActor:
    def __init__(self, config: FineTuningConfig, big_llm_configs: List[LLMConfig]):
        # loads model via transformers
        # maintains a ring buffer of (prompt_text, target_response) pairs
        # spawns a background asyncio.Task for gradient updates

    async def record(self, context: LLMContext, small_model_result: str):
        # 1. Gets the big-model response for the same prompt (or retrieves from buffer)
        # 2. Adds (prompt_text, big_model_response) to ring buffer
        # 3. Triggers a gradient step if buffer is full enough

    async def checkpoint(self, step: int):
        # saves model weights to checkpoint_dir/step_{step}/
```

The actor's `record` method calls the big model to get the ground-truth label. This doubles the token cost for routed calls when fine-tuning is enabled — this is the core trade-off.

**Note**: This step has significant open questions (see below). It is intentionally left at interface level here.

---

## Trade-Offs

### Routing (Part 1)

| Gain | Cost |
|---|---|
| Eliminates API cost for ~N_agents × N_ticks calls | Small model quality for free-text generation is uncertain |
| Reduces latency if small model is colocated on same machine | Two LLM pools → double the Ray actor overhead |
| Zero change to callers | Config becomes more complex (new `routing_llm` section) |
| Graceful fallback on error | Adds a code layer that could mask routing bugs |

The biggest risk: `societyagent_status_summary` outputs `type = "text"` (free-text), not `categorical/integer/float`. This means the existing `QdrantCacheActor` already skips it (it only caches structured outputs). A small 500M model generating free text will produce noticeably different output from a large model. Whether that matters depends on the use case — if the status summary is only for the UI (which the code confirms: it goes to `DataRecorder → StorageStatus.status`), degraded quality is acceptable.

### Online Fine-Tuning (Part 2)

| Gain | Cost |
|---|---|
| Model improves without a separate offline training pipeline | During fine-tuning, the big model is called for every routed prompt — effectively 2× the token cost until the model converges |
| Training signal is real simulation data | Fine-tuning a 500M model mid-simulation requires GPU memory; vLLM and training cannot share the same process naively |
| Checkpoint artifacts are available for reuse | PyTorch gradient descent in a Ray actor blocks that actor for the duration of the backward pass — buffer size and training cadence must be tuned |
| | Catastrophic forgetting: online fine-tuning on one task can degrade other tasks |
| | Defining "agreement" for free-text generation is non-trivial: exact string match is too strict; embedding similarity or LLM-as-judge adds complexity |

---

## Rejected Approaches

### Approach: Add routing inside `LLMActor`

**Why rejected**: `LLMActor` at `agentsociety/llm/llm_actor.py:62` is a Ray remote actor. It already receives a `config: LLMConfig` per call. Adding routing there would mean passing config for both models on every call and branching inside the remote actor. This spreads routing logic across a Ray message boundary, making it harder to test and reason about. `RoutingLLM` as a local wrapper is cleaner.

### Approach: Add a `routed_llm` field to `AgentToolbox`

**Why rejected**: `AgentToolbox` at `agentsociety/agent/toolbox.py:154` is shared across all agents. Adding a second `LLM` field would require every block and agent to be aware of routing. The point of this feature is that routing is transparent to callers.

### Approach: Modify `Block.build_llm_prompt_context` to select the LLM

**Why rejected**: `Block.build_llm_prompt_context` at `agentsociety/agent/block.py:156` only builds the context dict; it does not make LLM calls. Routing at the block level would require every block to know about routing rules. Routing at the `LLM`/`RoutingLLM` layer keeps the policy centralized and decoupled.

### Approach: Use the existing `QdrantCacheActor` skip mode as a proxy for routing

**Why rejected**: `QdrantCacheActor` only handles structured outputs (`categorical`, `float`, `integer`). The `status_summary` prompt outputs `type = "text"`, which is explicitly excluded from cache eligibility at `agentsociety/llm/llm.py:206`. This approach would require changing the cache system's eligibility rules, with unintended side effects.

### Approach: Run fine-tuning in-process inside `RoutingLLM`

**Why rejected**: Gradient updates on a PyTorch model inside an async event loop would block the entire agent simulation during each backward pass. A dedicated Ray actor receives training pairs via non-blocking `.remote()` calls and runs training on its own thread.

### Approach: Use RLHF / reward model for fine-tuning signal

**Why rejected**: This requires a separately trained reward model, which is outside the scope of this simulation framework. Simple imitation learning (small model imitates large model) is the correct first step.

---

## Assumptions & Open Questions

### Assumptions

1. The small model (Qwen 500M) is already fine-tuned for instruction following and accessible via a running vLLM instance at a known URL. The feature does not handle model download or vLLM startup.
2. `societyagent_status_summary` is purely presentational — its output affects no downstream LLM calls, no need updates, no plan generation, no block dispatch. This must be confirmed before routing is enabled.
3. The small model is on the same machine as the simulation (low-latency assumption). If it's remote, latency savings may not materialize.

### Open Questions (require answers before finalizing Part 2)

**Q1: Is the fine-tuning compute co-located with vLLM inference?**
If the small model is served via vLLM for inference AND needs gradient updates, these cannot share the same process. The plan assumes a separate `transformers` model instance in the `FineTuningActor` that periodically reloads into vLLM. This is the standard "shadow model" pattern but adds operational complexity. Alternatively, fine-tuning happens purely offline after the simulation; the "online" label is then misleading.

**Q2: What is the agreement metric for free-text outputs?**
The existing cache system uses exact match after normalization (`llm.py:556 _normalize_for_compare`). For `status_summary`, which is free text ("I am working at the office..."), exact match is 0% even for semantically identical outputs. The plan needs a clear definition:
- Option A: Cosine similarity of sentence embeddings (requires embedding model in `FineTuningActor`)
- Option B: Keyword overlap (simple but brittle)
- Option C: LLM-as-judge (expensive — calls the big model twice)
- Option D: No agreement check; always train on big-model output as label (pure imitation learning)

**Q3: Should the small model also handle OTHER prompt keys, or only `societyagent_status_summary`?**
The architecture supports any prompt key via config. But each additional routed prompt is a new risk of quality degradation. The plan currently targets `status_summary` only as the first target.

**Q4: What happens to fine-tuning when the simulation resumes from a checkpoint?**
The existing checkpoint system at `agentsociety/simulation/checkpointmanager.py` saves agent memory state. It does not save optimizer state for fine-tuning. The plan would need to decide: does the `FineTuningActor` checkpoint the optimizer to `FineTuningConfig.checkpoint_dir`, and does resume load from it?

**Q5: Is the goal of fine-tuning to produce a permanent artifact, or to improve simulation quality during a single run?**
This determines whether checkpointing, experiment-to-experiment model loading, and training stability matter. If it's per-run only, many complexities disappear.

---

## Code That Could Be Refactored *(informational)*

- `agentsociety/llm/llm.py:101` — `LLM.__init__` constructs both the load balancer and the actor pool inline. If `RoutingLLM` needs to create a second pool, extracting `_build_actor_pool(configs) -> List[LLMActor]` would be cleaner and avoid duplicating the loop.
- `agentsociety/llm/llm.py:38` — `LLMContext` is a `TypedDict`. It could become a Pydantic model to get validation and easier extension. Not a blocker.
- `agentsociety/cityagent/societyagent.py:252` — `status_summary()` calls `self.llm.atext_request` with no `response_format` and no `max_tokens`. For a small model, setting `max_tokens=100` would prevent runaway generation. This should be added in `societyagent.py` regardless of routing.
- `agentsociety/prompts/societyagent/societyagent_status_summary_citysim_v1_0.toml:158` — The output type is `text`, which makes this prompt ineligible for `QdrantCacheActor`. If the output were constrained to a fixed schema (e.g., a `summary` field with `type = "text"` and a bounded token count), the downstream behavior would be identical and a routing confidence threshold would be easier to define.

---

## Proposed Next Steps

1. **Answer Open Questions Q1–Q5** before any implementation begins. Q2 (agreement metric) and Q1 (compute co-location) are the decisions that most change the design.

2. **Implement Part 1 (Routing) independently** — it delivers real cost savings and has no dependency on the fine-tuning design. Steps: add `RoutingLLMConfig` to `configs/__init__.py`, implement `RoutingLLM` in `agentsociety/llm/routing_llm.py`, modify `infrastructuremanager.py:_init_core_components`.

3. **Validate Part 1** by running a simulation with routing enabled and confirming: (a) the big model receives zero calls for `societyagent_status_summary`, (b) the simulation output is visually acceptable, (c) token counts drop by the expected amount.

4. **Design Part 2 (Fine-Tuning) as a separate feature** once the agreement metric and compute topology are decided. The `FineTuningActor` interface described here is a placeholder; the internals depend heavily on Q1 and Q2 answers.
