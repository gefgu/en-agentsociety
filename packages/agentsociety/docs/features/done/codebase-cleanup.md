# Codebase Cleanup
> A catalogued, actionable inventory of dead code, duplicated logic, deprecated patterns, and structural tech debt across the agentsociety package, ordered by impact.

## Purpose & Motivation
The agentsociety package has accumulated technical debt from rapid feature development, a CitySim fork divergence, an in-progress migration from `FormatPrompt` to `PromptManager`, and several exploratory features (Qdrant cache, block_memory, AgentSociety backward-compat shim) that were partially implemented. The goal is to remove confusion for future contributors, reduce the surface area of the codebase that must be maintained, and surface a small number of latent bugs.

## Success Criteria
- Every item below is either resolved, explicitly deferred with a reason, or re-classified after further discussion.
- No behavioral regressions in end-to-end examples under `examples/`.
- `agentsociety check --config` continues to pass on all reference configs.

## Scope
**In scope:**
- Dead code removal (unused imports, no-op classes, unreachable logic)
- Consolidation of duplicated utility functions
- Removal or completion of stub/TODO code
- Fixing misuse patterns (`print` instead of logger, inline `import traceback`, unguarded `_db_actor` access)
- Addressing deprecated patterns (`from __future__ import annotations` on Python 3.11+, `ToolCategory`-less `CustomTool` factory methods)

**Out of scope:**
- Architectural rewrites (e.g. replacing Ray with asyncio)
- New features
- Documentation rewrite
- WebAPI (`webapi/`) — separate product surface, deferred

---

## Constraints
- No test suite; validation must be done through example scripts in `examples/`.
- Ray remote actors complicate dead-code analysis — methods called via `.remote()` appear unused to static tools.
- `commercial/` sub-package is a deployment-only module; lower priority.

---

## Catalog

Tasks are grouped by category and annotated with:
- **Impact**: High / Medium / Low
- **Effort**: Easy (< 30 min) / Medium (30 min – 2 h) / Hard (> 2 h)
- **Risk**: Low / Medium / High (chance of regression)

---

### Category 1: Stub / Incomplete Code (TODOs and commented-out calls)

#### C1-1 — `BlockParams.block_memory` is unused and self-annotated as such
- **Location**: `agentsociety/agent/block.py:24-25`
- **Description**: `block_memory: Optional[dict[str, Any]] = None` is declared inside `BlockParams` with the comment `# TODO: unused`. The corresponding `Block.block_memory` property (`block.py:145-150`) raises `RuntimeError` if accessed (nothing in the codebase calls `.block_memory`). The entire `block_memory` branch in `Block.__init__` (`block.py:75-82`) instantiates a `KVMemory` but it is never read.
- **Action**: Delete `BlockParams.block_memory`, the `if key == "block_memory"` branch in `Block.__init__` (`block.py:70-82`), and the `block_memory` property (`block.py:145-150`). Also delete the `self._block_memory = None` assignment, and the `_block_memory` attribute entirely.
- **Impact**: Medium — reduces confusion about whether blocks have their own memory stores
- **Effort**: Easy
- **Risk**: Low

IGNORE THE COMMENTED ONES.
<!-- #### C1-2 — `_get_number_of_contacts_in_last_7_days` is a stub returning 0
- **Location**: `agentsociety/cityagent/blocks/economy_block.py:429-431`
- **Description**: The method is declared but returns a hard-coded `0` with `# TODO: IMPLEMENT`. It is called nowhere in the file.
- **Action**: Either implement it (requires social graph query) or delete both the method and the `# TODO: IMPLEMENT` comment. A grep shows no callers; deletion is safe.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low
- **User's input**: Keep this. It should be implemented later.

#### C1-3 — Transport mode selection result is never applied (commented-out call)
- **Location**: `agentsociety/cityagent/blocks/mobility_block.py:1101-1104`
- **Description**: `set_person_vehicle_attribute` is commented out with `# TODO`. The `TransportModeSelectionBlock.forward` computes `selected_mode_str` but never passes it to the simulator. The return value `{"transport_mode": selected_mode_str}` is informational only; the physical simulation never receives this choice.
- **Action**: Either implement and uncomment the call, or document that transport mode selection is advisory only and remove the dead comment.
- **Impact**: High — potential simulation correctness issue
- **Effort**: Medium
- **Risk**: Medium (touching gRPC environment calls) -->

#### C1-4 — `month = "Current Month"` placeholder in mobility block
- **Location**: `agentsociety/cityagent/blocks/mobility_block.py:1044`
- **Description**: The prompt context key `month` is always set to the string literal `"Current Month"` instead of deriving it from the simulation time. The environment object has `get_datetime()` which returns actual time components.
- **Action**: Replace with `self.environment.get_datetime(True)` (already used one line above for `sim_time`) and extract the month.
- **Impact**: Medium — prompts receive incorrect seasonal context
- **Effort**: Easy
- **Risk**: Low

#### C1-5 — `TODO: remove random position assignment` in `CitizenAgentBase._bind_to_economy`
- **Location**: `agentsociety/agent/agent.py:696`
- **Description**: Economy agents are assigned a random map position on bind (`agent.py:697-715`) because the economy simulator requires an `xy_position` but the agent may not have one yet. The TODO indicates this should be replaced with a real position lookup.
- **Action**: If the agent always has a `home` position by the time `_bind_to_economy` runs (it does — `_bind_to_simulator` runs first), use the home position instead of `random.randrange`. The home AOI center is available through `environment.map`.
- **Impact**: Medium — simulator receives inaccurate initial agent locations
- **Effort**: Medium
- **Risk**: Medium

#### C1-6 — `# TODO: remove the design` on `EconomyClient._get_request_type`
- **Location**: `agentsociety/environment/economy/econ_client.py:131`
- **Description**: `_get_request_type` performs linear scans over citizen/bank/nbs/government/firm ID sets to classify an entity. The TODO notes this design should be changed; the method is called internally several times within `econ_client.py`. A dict-based lookup would be O(1) instead of O(n).
- **Action**: Replace the four `all(i in self._xxx_ids for i in id)` chains with a single reverse-lookup dict built at init time: `{id: entity_type for ...}`.
- **Impact**: Low (performance, not correctness)
- **Effort**: Easy
- **Risk**: Low

#### C1-7 — Commented-out debug `print` statements
- **Locations**:
  - `agentsociety/agent/agent.py:340, 350` — `# print(f"dialog: ...")`, `# print(f"response: ...")`
  - `agentsociety/performance/RoutingTracker.py:34` — `# print("Recording block performance:", ...)`
  - `agentsociety/performance/BlockPerformance.py:48` — `# print("Recording block performance:", ...)`
- **Action**: Delete all four commented-out print lines.
- **Impact**: Low (noise)
- **Effort**: Easy
- **Risk**: Low

#### C1-8 — `# UNCOMMENT TO ALLOW INITIAL SOCIAL NETWORK` dead comment
- **Location**: `agentsociety/cityagent/__init__.py:226`
- **Description**: `# initialize_social_network_by_similarity,` is commented out in the default init_funcs list. The function is imported at line 4 but the import AST analysis shows it is unused. This creates confusion about whether social network initialization is supported.
- **Action**: Either make this a config flag (e.g., `SocietyAgentConfig.initialize_social_network: bool = False`) or remove the commented import and its associated import line.
- **Impact**: Low (clarity)
- **Effort**: Easy
- **Risk**: Low
- Make it a config flag, with the default value of false.

---

### Category 2: Duplicated Logic

#### C2-1 — `extract_json` is defined twice
- **Locations**:
  - `agentsociety/agent/agent_base.py:62` — defines `extract_json(output_str)`
  - `agentsociety/cityagent/blocks/cognition_block.py:12` — defines an identical `extract_json(output_str)`
- **Description**: Both functions find the first `{` and last `}` in a string. `agent_base.py` version is the authoritative one (exported in `__all__`). `cognition_block.py` defines its own copy locally.
- **Action**: Delete the copy in `cognition_block.py:12-37` and add `from ...agent.agent_base import extract_json` (or from `...agent import extract_json`).
- **Impact**: Low (correctness risk if the two diverge)
- **Effort**: Easy
- **Risk**: Low

#### C2-2 — `SocietyAgent` owns a second `PromptManager` that duplicates `Block._shared_prompt_manager`
- **Locations**:
  - `agentsociety/agent/block.py:188-208` — `Block._get_or_create_prompt_manager()` creates a singleton `PromptManager` pointing at `agentsociety/prompts/`
  - `agentsociety/cityagent/societyagent.py:220-223` — `SocietyAgent.__init__` creates *another* `PromptManager` pointing at the same `prompts/` directory
- **Description**: Both point at `str(Path(__file__).resolve().parents[1] / "prompts")`. Two identical `PromptManager` instances are created for every `SocietyAgent`, loading and parsing all TOML files twice. The `SocietyAgent`-owned `prompt_manager` is used for `societyagent_*` prompts; the `Block._shared_prompt_manager` is used by all `Block` subclasses.
- **Action**: Use `Block._shared_prompt_manager` (or `Block._get_or_create_prompt_manager(None)`) inside `SocietyAgent.__init__` instead of creating a second instance. The `societyagent_*` prompt TOMLs live in the same directory and will be found by the shared instance.
- **Impact**: Medium (memory + startup overhead proportional to agent count)
- **Effort**: Easy
- **Risk**: Low

#### C2-3 — `_build_prompt_context` / `build_llm_prompt_context` are equivalent across `SocietyAgent` and `Block`
- **Locations**:
  - `agentsociety/agent/block.py:156-185` — `Block.build_llm_prompt_context()`
  - `agentsociety/cityagent/societyagent.py:235-253` — `SocietyAgent._build_prompt_context()`
- **Description**: The two methods build the same `LLMContext` dictionary (block name, func name, agent id, prompt identity, prompt inputs, prompt input/output schema). `SocietyAgent._build_prompt_context` uses `self.prompt_manager` and `self.id`; `Block.build_llm_prompt_context` uses `self.prompt_manager` and `self._agent.id`. They are structurally identical.
- **Action**: After resolving C2-2 (shared `PromptManager`), delete `SocietyAgent._build_prompt_context` and replace all its call sites (`societyagent.py:246, 249, 252, 253`) with `self.build_llm_prompt_context(...)` (inheriting from `Block` or calling as a mixin). Requires `SocietyAgent` to have access to `build_llm_prompt_context`, which it does not currently since it is not a `Block`.
- **Coordination**: This may require making `_build_prompt_context` a standalone helper function instead.
- **Impact**: Low (code deduplication)
- **Effort**: Medium
- **Risk**: Low

#### C2-4 — `add_tool` and `add_custom_tool` in `AgentToolbox` are identical
- **Location**: `agentsociety/agent/toolbox.py:184-213`
- **Description**: `add_custom_tool(self, tool: CustomTool)` at line 203 simply calls `self.add_tool(tool)`. These two methods are identical in behavior.
- **Action**: Delete `add_custom_tool`; it is not called anywhere in production code (only in `CHANGES.md` documentation).
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C2-5 — `CustomTool.create_mcp_tool` and `create_normal_tool` produce identical objects
- **Location**: `agentsociety/agent/toolbox.py:95-151`
- **Description**: Both class methods create `cls(name=name, tool=tool, description=description)`. The original design referenced a `ToolCategory` enum (MCP vs NORMAL) that no longer exists in the code. Neither method is called anywhere in the production codebase.
- **Action**: Delete both factory class methods. Users calling `CustomTool(name=..., tool=..., description=...)` directly get the same result.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C2-6 — Inline `import traceback` inside exception handler duplicates top-level import
- **Location**: `agentsociety/simulation/simulationengine.py:676`
- **Description**: `import traceback` appears at the top of the file at line 8 and again inline inside the `_message_dispatch` exception handler at line 676. The inline import is redundant.
- **Action**: Delete line 676.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

---

### Category 3: Unused Imports in Production Modules

These are not `__init__.py` re-export files (those "unused" imports are intentional public API re-exports). The following are in implementation files.

#### C3-1 — `person_pb2` imported but never used in two files
- **Locations**:
  - `agentsociety/agent/agent.py:10` — `from pycityproto.city.person.v2 import person_pb2 as person_pb2`
  - `agentsociety/agent/agent_base.py:7` — `from pycityproto.city.person.v2 import person_pb2 as person_pb2`
- **Description**: Neither file references `person_pb2` by name in any function body. The protobuf type is used in `PersonService` (in `environment/sim/person_service.py`) but not in these agent files.
- **Action**: Remove both import lines.
- **Impact**: Low (startup time, clarity)
- **Effort**: Easy
- **Risk**: Low

#### C3-2 — `map_pb2` imported but never used in `environment.py`
- **Location**: `agentsociety/environment/environment.py:11`
- **Description**: `from pycityproto.city.map.v2 import map_pb2 as map_pb2` appears at the top. A grep for `map_pb2` shows only the import line itself in that file.
- **Action**: Remove the import line.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C3-3 — `json` imported but not used in `economy_block.py`
- **Location**: `agentsociety/cityagent/blocks/economy_block.py:1`
- **Description**: `import json` is present; `json_repair` is used throughout but standard `json` is not called directly.
- **Action**: Remove `import json`.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C3-4 — `Optional` imported but not used in `needs_block.py`
- **Location**: `agentsociety/cityagent/blocks/needs_block.py:1`
- **Description**: `from typing import Any, Optional` — `Optional` is not used directly (the file uses `X | None` union syntax or does not annotate optional parameters).
- **Action**: Remove `Optional` from the import.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C3-5 — `time` imported but never called in three block files
- **Locations**:
  - `agentsociety/cityagent/blocks/plan_block.py:1`
  - `agentsociety/cityagent/blocks/other_block.py:2`
  - `agentsociety/cityagent/blocks/social_block.py:3`
- **Description**: `import time` appears at the top of all three files but no `time.*` call exists in any of them (verified by grep).
- **Action**: Remove `import time` from all three files.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C3-6 — `from __future__ import annotations` on Python 3.11+ codebase
- **Locations** (10 files):
  - `agentsociety/agent/agent.py:1`
  - `agentsociety/agent/dispatcher_cache_actor.py:1`
  - `agentsociety/database/duckdb.py:1`
  - `agentsociety/database/base_database.py:3`
  - `agentsociety/database/clickhouse.py:1`
  - `agentsociety/database/database_actor.py:1`
  - `agentsociety/configs/exp.py:1`
  - `agentsociety/memory/spatial_memory.py:1`
  - `agentsociety/memory/kv_memory.py:1`
  - `agentsociety/memory/stream_memory.py:1`
- **Description**: `requires-python = ">=3.11"` in `pyproject.toml`. PEP 563 (`from __future__ import annotations`) defers annotation evaluation and is the default behavior in Python 3.10+ in most contexts. On 3.11 this import is harmless but unnecessary, and it can mask real bugs (e.g. when annotations are introspected at runtime via Pydantic). **Note**: Pydantic v2 and Ray both introspect annotations; removing this future import could cause Pydantic models to parse type annotations differently if forward references are involved. Verify before mass removal.
- **Action**: Audit each file for forward-reference annotations (e.g. `"SomeClass"` string annotations or self-referential types). Remove the future import only where no forward references exist.
- **Impact**: Low (clarity, avoids subtle Pydantic introspection issues)
- **Effort**: Medium (requires per-file audit)
- **Risk**: Medium (Pydantic/Ray interaction)

---

### Category 4: Deprecated or Inconsistent Patterns

#### C4-1 — `FormatPrompt` (legacy) and `PromptManager` (new) coexist; `BlockDispatcher` still uses the old system
- **Locations**:
  - `agentsociety/agent/prompt.py` — entire `FormatPrompt` class
  - `agentsociety/agent/dispatcher.py:11, 47, 56` — `BlockDispatcher` imports and uses `FormatPrompt`
  - `agentsociety/agent/__init__.py:18, 45` — `FormatPrompt` re-exported
- **Description**: All `Block` subclasses in `cityagent/blocks/` have been migrated to `PromptManager` (confirmed by reading cognition, economy, mobility, daily_schedule, plan, social, other blocks). The dispatcher prompt is the only remaining consumer of `FormatPrompt`, using its `${context.current_intention}` interpolation syntax. `FormatPrompt` is a 242-line class with its own async template engine (using `eval`). `PromptManager` provides `format_prompt_to_dialog()` as a replacement.
- **Action**: Migrate `BlockDispatcher.dispatcher_prompt` to use a `PromptManager`-managed TOML prompt file (or a simple f-string since the dispatcher prompt only substitutes `context.current_intention`). Remove `agent/prompt.py` and its re-export once `dispatcher.py` is migrated.
- **Impact**: High — reduces the dual-system maintenance burden; `FormatPrompt._eval_expr` uses `eval()` which is a security smell
- **Effort**: Medium
- **Risk**: Medium (dispatcher is in the hot path for every agent step)

#### C4-2 — `AgentSociety.__init__` deprecated constructor copies attributes with `dir()` loop
- **Location**: `agentsociety/simulation/agentsociety.py:62-114`
- **Description**: The deprecated `AgentSociety()` constructor (kept for backward compat) calls `self.create()` then iterates `dir(engine)` to copy non-private, non-callable attributes, then stores `self._engine` for method delegation via `__getattr__`. This approach is fragile: it copies the state snapshot at construction time, so any attribute changes on the engine after construction are not reflected on the `AgentSociety` wrapper.
- **Action**: Remove the `__init__` and `__getattr__` fallback entirely. Any code that calls `AgentSociety(config)` should already be producing a `DeprecationWarning`. Assess via git log and examples whether any caller still uses the constructor form.
- **Impact**: Medium — eliminates a fragile shim
- **Effort**: Easy (delete the method body, keep only the `create` classmethod)
- **Risk**: Low (already emits DeprecationWarning)

#### C4-3 — `LLMConfig.validate_configuration` incorrectly blocks `base_url` for all non-VLLM providers
- **Location**: `agentsociety/llm/llm.py:93-97`
- **Description**: The validator raises `ValueError("base_url is not supported for this provider")` if `base_url is not None` and `provider != VLLM`. However, `LLM.__init__` immediately overwrites `config.base_url` for DeepSeek, Qwen, SiliconFlow, etc. (lines 150-162). The validator fires *before* `__init__` sets `base_url`, meaning a user who pre-sets `base_url` on a non-VLLM provider will get an error even though `LLM.__init__` would have overridden it anyway. This creates a confusing API.
- **Action**: Either remove the validator (since `LLM.__init__` sets all base URLs anyway) or loosen it to only block when the user explicitly provides a `base_url` for providers that have a well-known fixed URL, e.g. DeepSeek.
- **Impact**: Medium (user-facing error)
- **Effort**: Easy
- **Risk**: Low

#### C4-4 — `_db_actor.insert_prompt_response_record.remote(...)` called without None-check
- **Location**: `agentsociety/llm/llm.py:377-384`
- **Description**: Inside the `if self._metrics_actor is not None:` guard, `self._db_actor.insert_prompt_response_record.remote(...)` is called at line 377 without first checking `self._db_actor is not None`. `_db_actor` is optional (see `LLM.__init__:139`) and may be `None` if the DatabaseActor is not enabled.
- **Action**: Add `if self._db_actor is not None:` before line 377.
- **Impact**: High — will crash at runtime when `metrics_actor` is set but `db_actor` is not
- **Effort**: Easy
- **Risk**: Low

#### C4-5 — `print()` used instead of logger in production code paths
- **Locations** (production-relevant only, excluding webapi which is separate):
  - `agentsociety/agent/prompt.py:126, 199` — error evaluation fallback uses `print()`
  - `agentsociety/agent/prompt.py:237-241` — `FormatPrompt.log()` uses `print()`
  - `agentsociety/agent/decorator.py:84` — `print()` in decorator
  - `agentsociety/cityagent/blocks/utils.py:30` — `print()` in `extract_dict_from_string` parse error
- **Action**: Replace each `print(...)` with `get_logger().warning(...)` or `get_logger().error(...)` as appropriate. The `FormatPrompt.log()` method is a debugging helper; if `FormatPrompt` is removed (see C4-1), this is moot.
- **Impact**: Medium — log output is invisible when Ray stdout is suppressed
- **Effort**: Easy
- **Risk**: Low

#### C4-6 — `WorkflowType.INTERVENE` duplicates `MESSAGE_INTERVENE` behavior with a misleading warning
- **Location**: `agentsociety/simulation/simulationengine.py:1064-1075`
- **Description**: The `INTERVENE = "other"` workflow type at `configs/exp.py:60` is handled at `simulationengine.py:1064-1075` and emits `"MESSAGE_INTERVENE is not fully implemented yet"` — but then calls `send_intervention_message()` identically to `MESSAGE_INTERVENE`. The two branches are functionally identical. The warning message even incorrectly names the other type.
- **Action**: Either delete the `INTERVENE` type (deprecate to `MESSAGE_INTERVENE`), or document what it was originally intended to do differently. At minimum, fix the warning message to say `INTERVENE` instead of `MESSAGE_INTERVENE`.
- **Impact**: Low (clarity)
- **Effort**: Easy
- **Risk**: Low

---

### Category 5: Structural / Design Tech Debt

#### C5-1 — `BlockParams.block_memory` and `Block.agent_memory` property are both present and redundant
> Note: C1-1 covers removing `block_memory`; this item covers the dual `memory` / `agent_memory` property.
- **Location**: `agentsociety/agent/block.py:128-142`
- **Description**: `Block` exposes both `memory` (line 129, returns `self._agent_memory`) and `agent_memory` (line 137, also returns `self._agent_memory`). They are identical. `memory` is the common name used throughout block implementations; `agent_memory` is used in no production call site (confirmed by grep).
- **Action**: Delete the `agent_memory` property. Keep `memory`.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C5-2 — Empty stub agent base classes with only docstrings
- **Location**: `agentsociety/agent/agent.py:782-809` — `FirmAgentBase`, `BankAgentBase`, `NBSAgentBase`, `GovernmentAgentBase`
- **Description**: All four classes have an empty body (just a docstring or `...`). They inherit `InstitutionAgentBase` without adding anything. They exist only to give subclasses a type name, which is valid, but the docstrings are imprecise (they say "Represents a X agent" without any additional contract).
- **Action**: No deletion needed. Add a brief note that these exist for type discrimination and forward-compatible extension. This is a documentation-only fix.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: None

#### C5-3 — `AgentSociety.__init__` `dir()` loop can cause `RecursionError` or incorrect copies
- **Location**: `agentsociety/simulation/agentsociety.py:88-96`
- **Description**: `for attr_name in dir(engine)` iterates all attributes including dunder methods and descriptor objects. `setattr(self, attr_name, attr_value)` then shallow-copies them, which can produce surprising behavior for properties, cached objects, or Ray handles. Since this constructor is already deprecated (C4-2), this is a secondary concern — it reinforces the argument for removal.
- **Action**: Resolved by C4-2.
- **Impact**: Medium
- **Effort**: Easy (covered by C4-2)
- **Risk**: Low

#### C5-4 — `extract_dict_from_string` in `cityagent/blocks/utils.py` uses `ast.literal_eval` instead of `json_repair`
- **Location**: `agentsociety/cityagent/blocks/utils.py:11-32`
- **Description**: `extract_dict_from_string` uses `re.findall` + `ast.literal_eval` to parse dicts from LLM output. This approach is brittle (fails on JSON-style `true`/`false`/`null`, Python's `ast.literal_eval` requires Python syntax). The same `economy_block.py` that calls this function also imports `json_repair`. Callers at `economy_block.py:525, 594` could use `json_repair.loads(clean_json_response(...))` which is already the pattern in every other block.
- **Action**: Replace calls in `economy_block.py:525, 594` with `json_repair.loads(clean_json_response(...))` and delete `extract_dict_from_string` from `utils.py`. Also remove the `import ast` from `utils.py:1`.
- **Impact**: Medium (correctness — LLM outputs `true` not `True`)
- **Effort**: Easy
- **Risk**: Low

#### C5-5 — `AgentToolbox` has unused introspection methods
- **Location**: `agentsociety/agent/toolbox.py:276-318` — `get_tool_info`, `get_all_tools_info`, `has_tool`, `__contains__`, `__len__`
- **Description**: None of these methods are called anywhere in the codebase (confirmed by grep). `has_tool` and `__contains__` duplicate each other. The toolbox API surface was over-built relative to actual usage.
- **Action**: Delete `get_tool_info`, `get_all_tools_info`, `has_tool`, `__contains__`, `__len__`. Keep `add_tool`, `get_tool`, `get_tool_object`, `list_tools`, `remove_tool`.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: Low

#### C5-6 — `SimulationEngine._config.env.env_config` vs `_fill_in_agent_class_and_memory_config` takes `env_config: Config` (not `EnvConfig`)
- **Location**: `agentsociety/cityagent/__init__.py:59-60`
- **Description**: `_fill_in_agent_class_and_memory_config(self: AgentConfig, env_config: Config)` receives a full `Config` but uses only `env_config.env` and `env_config.agents`. The parameter is named `env_config` but it is actually a `Config`. This naming confusion affects readability.
- **Action**: Rename parameter from `env_config` to `config` (and update `_fill_in_agent_class_and_memory_config(agent_config, env_config=config.env)` call sites in the `default()` function — but note the call passes `config.env` not `config`, meaning the function receives an `EnvConfig` but is typed as `Config`). This is actually a type annotation bug — the parameter should be typed `EnvConfig`.
- **Action (corrected)**: Change the type annotation from `env_config: Config` to `env_config: EnvConfig` and update the body to not access `.env.` prefix (since `env_config` already is the `EnvConfig`). Check that `env_config` is used in the function body — it is not, confirming the entire parameter is unused in practice.
- **Impact**: Low (clarity / type safety)
- **Effort**: Easy
- **Risk**: Low

---

### Category 6: Latent Bugs

#### C6-1 — `_db_actor` used without None-check in `llm.py`
> See C4-4. This is the highest-risk latent bug.

#### C6-2 — `WorkflowType.INTERVENE` branch misspells "congnition" in its warning
- **Location**: `agentsociety/simulation/simulationengine.py:1066`
- **Description**: `"MESSAGE_INTERVENE is not fully implemented yet, it can only influence the congnition of target agents"` — "congnition" should be "cognition", and the message incorrectly names `MESSAGE_INTERVENE` instead of `INTERVENE`.
- **Action**: Fix the string.
- **Impact**: Low
- **Effort**: Easy
- **Risk**: None

#### C6-3 — `_save_global_prompt` has a dual-path that can write directly to `database_writer` bypassing `DataRecorder`
- **Location**: `agentsociety/simulation/simulationengine.py:573-588`
- **Description**: If `self._data_recorder is None`, `_save_global_prompt` writes directly via `self._database_writer.write_global_prompt()`. But `DataRecorder` is always started before `run()` is called (in `init()`). The `data_recorder is None` fallback path is only reachable if `_start_data_recorder()` failed silently. This bypasses the async write queue and could interleave writes with the recorder's async writes.
- **Action**: Either remove the fallback direct-write path (make it log a warning and return) or assert that `_data_recorder` is always set.
- **Impact**: Medium
- **Effort**: Easy
- **Risk**: Low

---

## Trade-Offs

| Trade-off | Decision |
|---|---|
| Removing `FormatPrompt` (C4-1) is the highest-value cleanup but touches the dispatch hot path | Treat as a separate mini-feature after the easy removals are done |
| `from __future__ import annotations` removal (C3-6) can break Pydantic introspection | Audit per-file before touching; do not batch-remove |
| Deprecated `AgentSociety()` constructor removal (C4-2) — could break external callers | Acceptable since it already emits `DeprecationWarning`; check git log for usages first |

## Rejected Approaches
- **Automated linting via `flake8 --extend-ignore` or `ruff`**: Would catch unused imports but not semantic issues (wrong parameter type, duplicate functions, TODO stubs). Manual catalog is more valuable here.

## Assumptions & Open Questions
- The `commercial/` sub-package is not audited here; it has its own team and deployment concerns.
- `webapi/` is excluded from scope; it has many `print()` calls and its own issues.
- The `database/` sub-package (`ClickHouseDatabase`, `DuckDBDatabase`, `DatabaseActor`) appears complete and correct; the README.MD in `agentsociety/database/` is a local developer reference, not dead code.
- Whether `SupervisorBase` and `SupervisorAgent` are actively used by any simulation scenario needs to be confirmed before touching `_create_default_supervisor_attributes` (C1-2 adjacent).

## Proposed Next Steps (ordered by impact and safety)

| # | Task | Category | Effort | Risk |
|---|---|---|---|---|
| 1 | Fix latent `_db_actor` None-check bug | C4-4 / C6-1 | Easy | Low |
| 2 | Remove `import time` from `plan_block.py`, `other_block.py`, `social_block.py` | C3-5 | Easy | Low |
| 3 | Remove `person_pb2` imports from `agent.py` and `agent_base.py` | C3-1 | Easy | Low |
| 4 | Remove `map_pb2` import from `environment.py` | C3-2 | Easy | Low |
| 5 | Remove `json` import from `economy_block.py` | C3-3 | Easy | Low |
| 6 | Remove `Optional` from `needs_block.py` imports | C3-4 | Easy | Low |
| 7 | Delete commented-out `print` lines and debug comments | C1-7, C1-8 | Easy | None |
| 8 | Delete `extract_json` copy in `cognition_block.py` | C2-1 | Easy | Low |
| 9 | Delete `add_custom_tool`, `create_mcp_tool`, `create_normal_tool` from `toolbox.py` | C2-4, C2-5 | Easy | Low |
| 10 | Delete unused introspection methods from `AgentToolbox` | C5-5 | Easy | Low |
| 11 | Delete `BlockParams.block_memory` / `Block.block_memory` / `Block.agent_memory` | C1-1, C5-1 | Easy | Low |
| 12 | Delete inline `import traceback` in `simulationengine.py:676` | C2-6 | Easy | None |
| 13 | Fix typo + wrong name in `INTERVENE` warning message | C6-2 | Easy | None |
| 14 | Replace `extract_dict_from_string` with `json_repair` in `economy_block.py` | C5-4 | Easy | Low |
| 15 | Remove deprecated `AgentSociety.__init__` constructor body | C4-2 | Easy | Low |
| 16 | Fix `LLMConfig.validate_configuration` to not block `base_url` on managed providers | C4-3 | Easy | Low |
| 17 | Replace `month = "Current Month"` with real month extraction | C1-4 | Easy | Low |
| 18 | Fix `EconomyClient._get_request_type` to use dict lookup | C1-6 | Easy | Low |
| 19 | Fix `_save_global_prompt` fallback path | C6-3 | Easy | Low |
| 20 | Clarify / deduplicate `WorkflowType.INTERVENE` vs `MESSAGE_INTERVENE` | C4-6 | Easy | Low |
| 21 | Delete unused `_get_number_of_contacts_in_last_7_days` stub | C1-2 | Easy | Low |
| 22 | Audit and remove `from __future__ import annotations` per-file | C3-6 | Medium | Medium |
| 23 | Use `Block._shared_prompt_manager` inside `SocietyAgent` (eliminate duplicate PM) | C2-2 | Easy | Low |
| 24 | Consolidate `_build_prompt_context` / `build_llm_prompt_context` | C2-3 | Medium | Low |
| 25 | Replace `CitizenAgentBase._bind_to_economy` random position with home position | C1-5 | Medium | Medium |
| 26 | Implement or document transport mode selection result propagation | C1-3 | Medium | Medium |
| 27 | Replace `print()` with `get_logger()` in production files | C4-5 | Easy | Low |
| 28 | Migrate `BlockDispatcher` dispatcher prompt from `FormatPrompt` to inline string or PromptManager | C4-1 | Medium | Medium |
| 29 | Remove `FormatPrompt` class and `agent/prompt.py` after step 28 | C4-1 | Easy | Low |

## Code That Could Be Refactored (informational)

- `agentsociety/simulation/simulationengine.py:1007-1081` — The `run()` workflow dispatch is a long `elif` chain over `WorkflowType` values. A dispatch table (`handlers: dict[WorkflowType, Callable]`) would be cleaner.
- `agentsociety/agent/agent.py:236-620` — `CitizenAgentBase` is 384 lines and handles simulation binding, economy binding, survey, interview, and motion update. Consider splitting into focused mixins.
- `agentsociety/llm/llm.py:279-420` — `atext_request` is a 140-line method mixing cache probe, server selection, retry loop, metric recording, and cache update. Extracting helper methods would improve readability.
- `agentsociety/cityagent/blocks/mobility_block.py` — The file is the largest in the codebase (1200+ lines, 9+ nested Block classes). Consider splitting into `place_selection_block.py`, `move_block.py`, `transport_mode_block.py`.
