# Adaptive LLM Routing — Run Tracking

Plan: `docs/features/adaptive-llm-routing.md`
Test command: `sh tests/run_e2e_tests`

## Progress

- [ ] Step 1: TOML schema extension + PromptManager methods
  - Add `[inputs.X]` typed declarations and `[outputs]` section to all existing TOML files
  - Add `get_input_schema()` and `get_output_schema()` to `agentsociety/prompts/prompt_manager.py`

- [ ] Step 2: `LLMContext.template_name` + call site updates
  - Add `template_name: str` to `LLMContext` at `agentsociety/llm/llm.py:36`
  - Update every `atext_request()` context dict in `agentsociety/cityagent/blocks/` and `agentsociety/cityagent/societyagent.py`
  - Add `template_name` to `insert_prompt_response_record()` signature in clickhouse.py, duckdb.py, database_actor.py, and llm.py
  - Write migration `0016_alter_prompt_responses_add_template_name.sql`

- [ ] Step 3: `RoutingConfig` model + `template_statistics` and `router_decisions` tables
  - Define `RoutingConfig` in `agentsociety/configs/`
  - Add `TemplateStatisticsRecord` and `RouterDecisionRecord` to `agentsociety/database/schema.py`
  - Implement insert methods in both ClickHouse and DuckDB backends
  - Write migrations 0014 and 0015
  - Expose through `DatabaseActor`

- [ ] Step 4: `ResponseStatisticsCollector`
  - Implement `agentsociety/routing/statistics.py`
  - Wire into `LLM.atext_request()` on the Big LLM success path

- [ ] Step 5: `LLMRouter` (rule table only, Big LLM passthrough)
  - Implement `agentsociety/routing/router.py` with full decision procedure
  - Initially all templates route to Big LLM (no CatBoost or SLM yet)
  - Validates the routing gate with zero functional change
