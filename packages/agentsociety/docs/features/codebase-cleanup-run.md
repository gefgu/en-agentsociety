# Codebase Cleanup — Run Tracking

Based on plan: `docs/features/codebase-cleanup.md`

Progress is tracked here. Original plan file is not modified.

## Steps

- [ ] Step 1: Fix latent `_db_actor` None-check bug (C4-4 / C6-1) — MEDIUM risk, ASK USER
- [ ] Step 2: Remove `import time` from `plan_block.py`, `other_block.py`, `social_block.py` (C3-5) — Low risk
- [ ] Step 3: Remove `person_pb2` imports from `agent.py` and `agent_base.py` (C3-1) — Low risk
- [ ] Step 4: Remove `map_pb2` import from `environment.py` (C3-2) — Low risk
- [ ] Step 5: Remove `json` import from `economy_block.py` (C3-3) — Low risk
- [ ] Step 6: Remove `Optional` from `needs_block.py` imports (C3-4) — Low risk
- [ ] Step 7: Delete commented-out `print` lines (C1-7) — None risk
- [ ] Step 8: Make `initialize_social_network` a config flag (C1-8) — Low risk
- [ ] Step 9: Delete `extract_json` copy in `cognition_block.py` (C2-1) — Low risk
- [ ] Step 10: Delete `add_custom_tool`, `create_mcp_tool`, `create_normal_tool` from `toolbox.py` (C2-4, C2-5) — Low risk
- [ ] Step 11: Delete unused introspection methods from `AgentToolbox` (C5-5) — Low risk
- [ ] Step 12: Delete `BlockParams.block_memory` / `Block.block_memory` / `Block.agent_memory` (C1-1, C5-1) — Low risk
- [ ] Step 13: Delete inline `import traceback` in `simulationengine.py:676` (C2-6) — None risk
- [ ] Step 14: Fix typo + wrong name in `INTERVENE` warning message (C6-2) — None risk
- [ ] Step 15: Replace `extract_dict_from_string` with `json_repair` in `economy_block.py` (C5-4) — Low risk
- [ ] Step 16: Remove deprecated `AgentSociety.__init__` constructor body (C4-2) — MEDIUM risk, ASK USER
- [ ] Step 17: Fix `LLMConfig.validate_configuration` to not block `base_url` on managed providers (C4-3) — Low risk
- [ ] Step 18: Replace `month = "Current Month"` with real month extraction (C1-4) — Low risk
- [ ] Step 19: Fix `EconomyClient._get_request_type` to use dict lookup (C1-6) — Low risk
- [ ] Step 20: Fix `_save_global_prompt` fallback path (C6-3) — Low risk
- [ ] Step 21: Clarify / deduplicate `WorkflowType.INTERVENE` vs `MESSAGE_INTERVENE` (C4-6) — Low risk
- [ ] Step 22: Audit and remove `from __future__ import annotations` per-file (C3-6) — MEDIUM risk, ASK USER
- [ ] Step 23: Use `Block._shared_prompt_manager` inside `SocietyAgent` (C2-2) — MEDIUM risk, ASK USER
- [ ] Step 24: Consolidate `_build_prompt_context` / `build_llm_prompt_context` (C2-3) — Low risk
- [ ] Step 25: Replace `CitizenAgentBase._bind_to_economy` random position with home position (C1-5) — MEDIUM risk, ASK USER
- [ ] Step 26: Replace `print()` with `get_logger()` in production files (C4-5) — Low risk (deferred until FormatPrompt decision)
