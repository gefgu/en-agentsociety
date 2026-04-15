# LLM Routing — Run Tracking

Plan: `/mnt/raid5/gustavo/citysim/packages/agentsociety/docs/features/llm-routing.md`
Test command: `cd /mnt/raid5/gustavo/citysim/packages/agentsociety && python -c "import agentsociety"`

## Steps

- [x] Step 1: Define `RoutedLLMEntry` in `agentsociety/llm/llm.py` alongside `LLMConfig` and export from `agentsociety/llm/__init__.py`
- [ ] Step 2: Add `routing: list[RoutedLLMEntry] = []` to `Config` in `agentsociety/configs/__init__.py`
- [ ] Step 3: Create `agentsociety/llm/routing_llm.py` implementing `RoutingLLM`. In `atext_request`, set `context["model_role"] = "routed"` on copied context before delegating.
- [ ] Step 4: Add `model_role: str` to `LLMContext` at `agentsociety/llm/llm.py` (the TypedDict near line 34)
- [ ] Step 5: Add `llm_tokens_by_prompt_total` Counter to `MetricsTracker` at `agentsociety/performance/MetricsTracker.py` and expose `record_llm_tokens_by_prompt` on `PrometheusActor` at `agentsociety/performance/prometheusActor.py`
- [ ] Step 6: Add `model_role` label to `performance_tokens_total` and `performance_block_calls_total` in `agentsociety/performance/BlockPerformance.py`. Update `record_performance` signature and `.labels(...)` calls.
- [ ] Step 7: Thread `model_role` through `LLM._record_success_metrics_and_db` at `agentsociety/llm/llm.py`: read from context, pass to `record_block_performance.remote(...)` and `record_llm_tokens_by_prompt.remote(...)`
- [ ] Step 8: Modify `agentsociety/simulation/infrastructuremanager.py` `_init_core_components` to wrap `self._llm` when `self._config.routing` is non-empty
- [x] Step 9: SKIPPED — Grafana dashboards (no dashboard files in repo)
- [ ] Step 10: Validation — confirm import check passes
