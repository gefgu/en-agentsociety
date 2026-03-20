# Changes from Upstream AgentSociety

This document catalogs all meaningful divergences from the original [tsinghua-fib-lab/agentsociety](https://github.com/tsinghua-fib-lab/agentsociety) codebase.

---

## 1. Dual-Engine Architecture (`simulation/`)

### Original
The original project had a single `AgentSociety` class that was itself the simulation runtime. It could only run city-scale population simulations.

### This Fork
`AgentSociety` is now a **factory** that produces one of two engine implementations:

| Engine | Config | Use Case |
|---|---|---|
| `SimulationEngine` | `Config` | Traditional city-scale multi-agent population simulation |
| `IndividualEngine` | `IndividualConfig` | Single or multi-agent task-solving pipeline (no city environment required) |

The `AgentSociety.__init__` path is kept for backwards-compatibility and emits a `DeprecationWarning`.

```python
# New way
engine = AgentSociety.create(config)   # returns SimulationEngine or IndividualEngine

# Old way (still works, deprecated)
engine = AgentSociety(config)
```

**Files changed**: `simulation/agentsociety.py` (rewritten), `simulation/individualengine.py` (new), `configs/__init__.py` (`IndividualConfig` added).

---

## 2. IndividualEngine & IndividualAgentBase (`simulation/`, `agent/`)

A completely new execution path for running agents as **task solvers** rather than city-simulation participants.

- Uses `IndividualConfig` instead of `Config`
- Loads tasks via `TaskLoader` and assigns them to `IndividualAgentBase`-typed agents
- No Ray actor groups, no mobility or economic simulators required
- Agents share a `MessageInterceptor`, `DatabaseWriter`, and `LLM` instance
- Designed for evaluations, benchmarks, and agentic pipelines

**Files added**: `simulation/individualengine.py`, `agent/agent.py` (`IndividualAgentBase` class), `taskloader/` (entire module).

---

## 3. TaskLoader (`taskloader/`)

A PyTorch `DataLoader`–inspired task management system (entirely new module).

- Loads tasks from JSON / JSONL files
- Tracks task status (`PENDING`, `RUNNING`, `COMPLETED`)
- Supports round-robin or random assignment of tasks to agents
- `Task` is a dataclass with `ground_truth`, `task_id`, `status`, `result`, `assigned_agent_id`
- Subclassable `Task` for domain-specific task types

**Files added**: `taskloader/taskloader.py`, `taskloader/__init__.py`.

---

## 4. CatBoost Need-Adjustment Actor (`catboost/`)

The original used LLM prompts to adjust agent need-satisfaction scores after each action. This is expensive and slow.

This fork adds a **CatBoost regression backend** that replaces the LLM for need adjustment:

- Runs as a Ray remote actor (`CatBoostAdjustNeedsActor`) for parallel inference
- One CatBoost model per need type (`hungry`, `tired`, `safe`, `social`)
- Uses `fastembed.TextEmbedding` + a pre-fitted PCA to encode action text
- Dispatched through `CatBoostDispatcherActor` which routes to the correct actor based on configuration

**Files added**: `catboost/catboost_adjust_needs.py`, `catboost/dispatcher.py`.

---

## 5. ModernBERT Regression Actor (`modernbert/`)

An experimental alternative to LLM need-adjustment using a fine-tuned `ModernBERT` classification/regression model. Currently **commented out** pending integration.

- Planned Ray remote actor with `num_gpus=0.1`
- Per-token regression over 4 need dimensions

**Files added**: `modernbert/modernbert_regression_actor.py`.

---

## 6. AgentToolbox & CustomTool (`agent/toolbox.py`)

The original `AgentToolbox` was a simple container for `LLM`, `Environment`, `Messager`, and `DatabaseWriter`.

This fork adds **extensible custom tools**:

- `CustomTool`: A Pydantic model wrapping any callable with metadata (`name`, `description`)
- `AgentToolbox.add_tool(tool: CustomTool)` / `get_tool(name)` / `list_tools()`
- Tools can be retrieved inside any `Block` or `Agent` method via `self.toolbox.get_tool("name")`
- `CustomTool.create_mcp_tool(...)` factory for MCP-protocol tools

---

## 7. BlockDispatcher (`agent/dispatcher.py`)

New LLM-powered router that selects the appropriate `Block` for a given user intention.

- Generates an OpenAI function-calling schema from registered block names + descriptions
- Sends the agent's `current_intention` context field to the LLM
- Returns the selected `Block` name or `None` if no block matches
- Supports a configurable `selection_prompt` template

The dispatcher is automatically created for every `Agent` instance and populated when `blocks` are provided.

---

## 8. `register_get` and `param_docs` Decorators (`agent/decorator.py`)

New decorators for exposing structured agent information:

```python
@register_get("Returns the agent's current hunger level")
async def get_hunger(self) -> float:
    return await self.memory.status.get("hunger_satisfaction")

@param_docs(name="The full name of the person", age="Age in years")
def greet(name, age): ...
```

- `register_get`: Registers a method into `cls.get_functions` dict with name and description, supports both sync and async methods.
- `param_docs`: Attaches per-parameter docstrings to any function for use in `FormatPrompt` templates.

---

## 9. DotDict Context System (`agent/context.py`)

The original project used raw `dict` objects for passing state between blocks. This fork introduces:

- `DotDict`: A `dict` subclass allowing `d.some_key` attribute-style access, with recursive conversion of nested dicts.
- `AgentContext` / `BlockContext`: Pydantic base models converted to `DotDict` at runtime via `context_to_dot_dict()`.
- `auto_deepcopy_dotdict`: Decorator that deep-copies DotDict arguments before passing to a function.
- `merge()`: Combines two `DotDict` instances, keeping live references to both originals.

---

## 10. Performance Observability Stack (`performance/`)

Entirely new module providing production-grade monitoring:

| Component | Role |
|---|---|
| `PrometheusActor` | Ray actor that exposes custom metrics to Prometheus |
| `ClickHouseActor` | Ray actor that writes event data to ClickHouse |
| `MetricsTracker` | High-level wrapper to record agent metrics |
| `BlockPerformance` | Records per-block execution time and token usage |
| `RoutingTracker` | Tracks block dispatcher routing decisions |
| `monitoring.py` | Starts the full Docker Compose stack (Prometheus, Grafana, ClickHouse, Loki) |

Docker Compose file, Prometheus config, Grafana dashboards, Alloy log config, and ClickHouse schema are all included.

---

## 11. CognitionBlock Enhancements (`cityagent/blocks/cognition_block.py`)

The original cognition block stored a basic emotion model. This fork extends it significantly:

- **Big Five personality initialization**: LLM-generates `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism` (1–3 integer scale) from demographic profile at start of simulation.
- **Hobbies generation**: LLM derives a list of 2–5 hobbies consistent with personality and demographics.
- **Life stage** and **household type** classification.
- **Goals** generation based on personality and demographics.
- All of the above are stored in agent memory and used throughout prompts.

---

## 12. SocietyAgent Personality Model (`cityagent/societyagent.py`)

The citizen agent now carries a richer internal state:

```python
# New StatusAttributes
hunger_satisfaction, energy_satisfaction, safety_satisfaction, social_satisfaction
current_need, emotion (6-dim), thought
# New: personality
openness, conscientiousness, extraversion, agreeableness, neuroticism
hobbies, goals, life_stage, household
```

Prompts throughout the agent (e.g., `ENVIRONMENT_REFLECTION_PROMPT`) now incorporate personality traits for more realistic, differentiated behavior.

---

## 13. Hugging Face Mirror Auto-Fallback (`__init__.py`)

When the package is imported, it probes `https://huggingface.co`. If unreachable and no HF endpoint env-var is set, it automatically sets:

```
HF_ENDPOINT=https://hf-mirror.com
HF_HUB_ENDPOINT=https://hf-mirror.com
```

This enables out-of-the-box usage in environments without direct access to Hugging Face (e.g., mainland China servers).

---

## 14. Commercial Module (`commercial/`)

An optional SaaS integration layer (not part of the open-source upstream):

- `auth/`: Multi-tenant authentication and authorization
- `billing/`: Usage tracking and quota enforcement  
- `executor/`: Hosted/cloud executor for managed simulation runs

---

## 15. Minor API / Structural Changes

| Change | Detail |
|---|---|
| `fastembed.SparseTextEmbedding` | Used throughout `Memory`, `VectorStore`, and `Toolbox` instead of a dense embedding model |
| `AgentToolbox` constructor | Now accepts an optional `embedding` field of type `SparseTextEmbedding` |
| `Block.NeedAgent` flag | If `True`, the owning `Agent` instance is injected automatically at registration time |
| `WorkflowType.FUNCTION` | New workflow step type for arbitrary Python callables |
| `WorkflowType.NEXT_ROUND` | New workflow step that resets agents while preserving memory |
| `WorkflowType.DELETE_AGENT` | New workflow step to remove agents mid-simulation |
| `AgentType.Individual` | New enum member for individual (task-solver) agents |
| `GatherQuery` | Helper model for bulk memory reads across multiple agents |
| `StorageDialog` + `StorageDialogType` | Fine-grained dialog persistence types added to storage |
