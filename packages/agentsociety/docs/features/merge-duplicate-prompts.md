# Merge Duplicate Prompt Templates
> Consolidate near-identical TOML prompt files into canonical shared templates so that each logical prompt has one definition that all callers reference.

## Purpose & Motivation

The prompt library has grown through organic addition: each block author created a new `.toml` file when they needed a prompt, often copy-pasting an existing one and making minor edits. The result is several clusters of nearly-identical templates:

- **Four time-estimate prompts** share the same preamble, the same Big Five block, and the same JSON output. Only their activity-domain examples differ.
- **Three mobility place-selection prompts** (`place_type`, `place_second_type`, `place_analysis`) are structurally the same prompt with a single sentence changed.
- **Two cognition update prompts** (`thought_update`, `emotion_update`) share a verbatim 9-line persona header.

When a shared concept changes (e.g., the Big Five scale description, the chronotype explanation text, or the JSON output instruction), it must currently be updated in every duplicate independently. Missing one creates silent prompt divergence.

## Success Criteria

- Every duplicate group identified below is collapsed to a single canonical TOML file (or a minimal parametric variant set).
- All callers (`prompt_name` strings in Python blocks) resolve to the canonical file without behavior change.
- No block Python code changes beyond updating `self.prompt_name` string values.
- The `PromptManager` version-resolution mechanism continues to work unchanged — no changes to `prompt_manager.py` or `prompt_memory_handler.py` are required.

## Scope

**In scope:**
- Identifying and merging the four time-estimate prompt TOMLs.
- Identifying and merging the three mobility place-selection prompt TOMLs.
- Extracting the shared cognition persona header pattern (informational — see Open Questions).
- Creating new versioned canonical TOMLs (`origin = "citysim"`, bumped versions) to replace duplicates.
- Updating `self.prompt_name` strings in the four Python block files that reference the replaced prompts.

**Out of scope:**
- Changes to `PromptManager`, `PromptMemoryHandler`, or `Block` base classes.
- Merging prompts that are merely thematically related but structurally different (e.g., `needs_evaluation` and `needs_reflection`).
- TOML file deletion of the originals — keep them as tombstones until at least one simulation run confirms correctness.
- Prompt content quality improvements (rewording, better instructions).

## Constraints

- The `PromptManager` loads prompts by `metadata.name` and resolves the highest version when no `active_config` is specified (`prompt_manager.py:68-88`). Renaming a prompt's `metadata.name` means all callers must also update their `self.prompt_name` string.
- Fields resolved automatically by `PromptMemoryHandler` (`prompt_memory_handler.py:148-199`) must remain the same field names in any unified prompt — the handler has no awareness of prompt identity.
- The `worktime_estimate` prompt uses `current_intention` as its field name while the other time-estimate prompts use `intention` (`worktime_estimate_citysim_v1_1.toml:14` vs `other_time_estimate_agentsociety_v1_0.toml:14`). Both map to the same memory source via the handler (`prompt_memory_handler.py:154`), but the TOML field name and the prompt text placeholder must match. A unified template must pick one.

## Architecture & Integration Points

### PromptManager load path

- `agentsociety/prompts/prompt_manager.py:43-88` — `_resolve_and_load_prompts()` walks every `.toml` under `prompts_dir`, groups by `metadata.name`, picks the highest version.
- `agentsociety/prompts/prompt_manager.py:154-160` — `get_required_fields()` returns input field names from the TOML `[inputs]` section.
- `agentsociety/prompts/prompt_manager.py:227-271` — `build_agent_state()` resolves each required field either from the caller-supplied `context` dict or by delegating to `PromptMemoryHandler.resolve_field()`.
- `agentsociety/prompts/prompt_manager.py:326-327` — `format_prompt_to_dialog()` wraps the formatted string into a single-turn dialog list.

### Block prompt lookup pattern (same in every block)

```python
# Example from WorkBlock (economy_block.py:84-98)
required_fields = self.prompt_manager.get_required_fields(self.prompt_name)
state_dict = await self.prompt_manager.build_agent_state(required_fields, context, self.memory)
final_prompt = self.prompt_manager.format_prompt_to_dialog(self.prompt_name, state_dict)
result = await self.llm.atext_request(final_prompt, ...)
```

The `self.prompt_name` string is set once in `__init__` and is the only coupling between Python code and a TOML file.

### Files touched by each duplicate group

| Group | TOML files | Python files |
|---|---|---|
| Time estimate | `other_time_estimate_agentsociety_v1_0.toml`, `other_sleep_time_estimate_citysim_v1_0.toml`, `social_time_estimate_agentsociety_v1_0.toml`, `worktime_estimate_citysim_v1_1.toml` | `other_block.py`, `social_block.py`, `economy_block.py` |
| Mobility place selection | `mobility_place_type_selection_agentsociety_v1_0.toml`, `mobility_place_second_type_selection_agentsociety_v1_0.toml`, `mobility_place_analysis_agentsociety_v1_0.toml` | `place_selection_block.py` |
| Cognition persona header | `cognition_thought_update_agentsociety_v1_0.toml`, `cognition_emotion_update_agentsociety_v1_0.toml`, `cognition_attitude_update_agentsociety_v1_0.toml` | `cognition_block.py` (informational — see Open Questions) |

## Duplicate Groups Found

### Group 1 — Time Estimate (HIGH priority — 4 near-identical files)

All four prompts share:
- Identical preamble: `"As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention."` (`other_time_estimate_agentsociety_v1_0.toml:70`, `other_sleep_time_estimate_citysim_v1_0.toml:66`, `social_time_estimate_agentsociety_v1_0.toml:70`, `worktime_estimate_citysim_v1_1.toml:62`).
- Identical `[inputs]` sections for: `plan`, `emotion_types`, `household`, `life_stage`, `hobbies`, `goals`, all five Big Five traits.
- Identical JSON output format and `output_guidance`.
- Identical body template text through the Big Five block.

**Differences only:**
- `worktime_estimate` uses `current_intention` instead of `intention` as the field name (`worktime_estimate_citysim_v1_1.toml:13`).
- `other_sleep_time_estimate` omits `work_ethic` and uses a sleep-specific chronotype explanation (`other_sleep_time_estimate_citysim_v1_0.toml:86-90`).
- `other_time_estimate` and `social_time_estimate` have `work_ethic`; `other_sleep_time_estimate` does not.
- Examples list differs by domain: work examples vs social examples vs generic examples.
- `output_description` differs: "sleep action", "social action", "generic action", "work action".

**Full diff between `other_time_estimate` and `social_time_estimate`:**
The entire `[inputs]` block is word-for-word identical. The prompt body is identical through the Big Five block. The only change: the examples list (`other_time_estimate_agentsociety_v1_0.toml:97-101` uses generic examples; `social_time_estimate_agentsociety_v1_0.toml:97-100` uses social examples).

**Full diff between `other_time_estimate` and `other_sleep_time_estimate`:**
`other_sleep_time_estimate` omits the `work_ethic` input (`other_time_estimate_agentsociety_v1_0.toml:61-63` vs absent), changes chronotype description slightly (`other_sleep_time_estimate_citysim_v1_0.toml:88`), and changes examples to generic ones.

**Full diff between `other_time_estimate` and `worktime_estimate`:**
`worktime_estimate` uses `current_intention` (not `intention`), omits `chronotype` and `leisure_preference`, and has work-focused examples. The preamble and Big Five block are identical.

**Proposed canonical template:** A single `activity_time_estimate` prompt with:
- A required `activity_domain` input (categorical: `work | social | sleep | other`) used only to select the `examples` sub-block.
- `intention` as the canonical field name (the `PromptMemoryHandler` maps both `intention` and `current_intention` to the same source — `prompt_memory_handler.py:154`).
- Optional inputs `work_ethic`, `chronotype`, `leisure_preference` — the prompt body renders them if present; the handler resolves them automatically since they are registered (`prompt_memory_handler.py:181-189`).

**Alternative:** Keep two files instead of one — `activity_time_estimate` (for other/social/work, which share `work_ethic`) and `sleep_time_estimate` (which omits it). This is simpler because it avoids optional-field rendering logic in the TOML. See Trade-Offs.

---

### Group 2 — Mobility Place Selection (HIGH priority — 3 near-identical files)

Files:
- `agentsociety/prompts/blocks/mobilityblock/mobility_place_type_selection_agentsociety_v1_0.toml`
- `agentsociety/prompts/blocks/mobilityblock/mobility_place_second_type_selection_agentsociety_v1_0.toml`
- `agentsociety/prompts/blocks/mobilityblock/mobility_place_analysis_agentsociety_v1_0.toml`

All three share:
- Identical `[inputs]` blocks for: `plan`, `intention`, `other_info`, `household`, `life_stage`, `hobbies`, `goals`, all five Big Five traits, `leisure_preference`, `risk_tolerance`.
- Near-identical prompt body: same preamble opener with only "intelligent decision system" vs "intelligent analysis system", same agent-state block, same behavioral preferences block, same JSON output format.

**Differences only:**
- `mobility_place_analysis` changes "decision system" to "analysis system" in the preamble (line 70).
- `mobility_place_analysis` uses `{place_list}` as the options variable name; the other two use `{poi_category}` (`mobility_place_analysis_agentsociety_v1_0.toml:87` vs `mobility_place_type_selection_agentsociety_v1_0.toml:86`).
- `mobility_place_analysis` has `categories = ["home", "workplace", "other"]` in `[outputs.place_type]`; the other two do not restrict categories.
- The example JSON value differs: `"home"` vs `"shopping"`.

**Proposed canonical template:** A single `mobility_place_selection` prompt with:
- `options` as the unified field name (replacing both `poi_category` and `place_list`).
- `selection_role` as an optional text input to vary the system role description.
- The `[outputs.place_type]` section without hardcoded categories (callers validate downstream).

This requires updating the caller in `place_selection_block.py` to pass the options field under the unified name.

---

### Group 3 — Cognition Persona Header (MEDIUM priority — shared boilerplate across 3 files)

Files:
- `agentsociety/prompts/blocks/cognitionblock/cognition_thought_update_agentsociety_v1_0.toml`
- `agentsociety/prompts/blocks/cognitionblock/cognition_emotion_update_agentsociety_v1_0.toml`
- `agentsociety/prompts/blocks/cognitionblock/cognition_attitude_update_agentsociety_v1_0.toml`

All three share an identical 9-line persona header:

```
You are a {gender}, aged {age}, belonging to the {race} race and identifying as {religion}.
Your marital status is {marriage_status}, and you currently reside in a {residence} area.
Your occupation is {occupation}, and your education level is {education}.
You are {personality}, with a consumption level of {consumption} and a family consumption level of {family_consumption}.
Your income is {income}, and you are skilled in {skill}.

My current emotion intensities are (0 meaning not at all, 10 meaning very much):
sadness: {sadness}, joy: {joy}, fear: {fear}, disgust: {disgust}, anger: {anger}, surprise: {surprise}.

Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {openness}, conscientiousness: {conscientiousness}, extraversion: {extraversion}, agreeableness: {agreeableness}, neuroticism: {neuroticism}.
```

(`cognition_thought_update_agentsociety_v1_0.toml:118-128`, `cognition_emotion_update_agentsociety_v1_0.toml:114-124`, `cognition_attitude_update_agentsociety_v1_0.toml:126-136` — identical text.)

**Important difference:** TOML does not support template inheritance or includes. There is no mechanism in `PromptManager` to compose prompts from partials. Therefore, eliminating this header duplication would require either:
1. Extending `PromptManager` with an `[includes]` or shared-snippet mechanism (significant scope).
2. Accepting the duplication but noting it as a known maintenance burden.

This group is classified as informational — a blocker for true deduplication unless the `PromptManager` is extended. The refactor plan below does not address this group in the initial pass.

---

### Group 4 — Big Five Input Block (LOW priority — boilerplate across 15+ files)

All prompts that accept personality inputs repeat the identical five-field `[inputs]` block:

```toml
[inputs.openness]
type = "integer"
description = "Big Five trait: Openness (1=Low, 2=Medium, 3=High)."
... (repeated for conscientiousness, extraversion, agreeableness, neuroticism)
```

This appears in every TOML file except `month_plan_goal_creation` and a few others. TOML has no include/anchor mechanism. This is structural duplication in the TOML schema layer, not in the prompt text. It cannot be eliminated without extending the loader. Informational only.

## Implementation Strategy

### Step 1 — Merge the four time-estimate prompts into two canonical files

**Decision:** Use two files (not one) to avoid optional-field complexity:
- `activity_time_estimate` — covers `other`, `social`, and `work` domains (all include `work_ethic`).
- `sleep_time_estimate` — covers the `sleep` domain only (omits `work_ethic`; uses sleep-specific chronotype description).

This is the minimal change that eliminates duplication while keeping each TOML self-contained and readable.

**Before:**
- `agentsociety/prompts/blocks/otherblock/other_time_estimate_agentsociety_v1_0.toml` — used by `OtherNoneBlock` (`other_block.py:112`, `self.prompt_name = "other_time_estimate"`)
- `agentsociety/prompts/blocks/otherblock/other_sleep_time_estimate_citysim_v1_0.toml` — used by `SleepBlock` (`other_block.py:41`, `self.prompt_name = "other_sleep_time_estimate"`)
- `agentsociety/prompts/blocks/socialblock/social_time_estimate_agentsociety_v1_0.toml` — used by `SocialNoneBlock` (`social_block.py:32`, `self.time_estimate_prompt_name = "social_time_estimate"`)
- `agentsociety/prompts/blocks/economyblock/worktime_estimate_citysim_v1_1.toml` — used by `WorkBlock` (`economy_block.py:67`, `self.prompt_name = "worktime_estimate"`)

**After (new files to create):**

`agentsociety/prompts/blocks/shared/activity_time_estimate_citysim_v1_0.toml`:
- `metadata.name = "activity_time_estimate"`
- Inputs: all shared inputs (`plan`, `intention`, `emotion_types`, `household`, `life_stage`, `hobbies`, `goals`, all Big Five, `chronotype`, `work_ethic`, `leisure_preference`).
- Field name: `intention` (not `current_intention`). The `PromptMemoryHandler` resolves both aliases to the same memory source (`prompt_memory_handler.py:154`); `WorkBlock.forward()` passes context that already has `current_step.intention` accessible via the handler.
- Examples section: generic examples (the activity-specific examples are not semantically meaningful — the LLM's reasoning comes from the persona context, not from the few-shot examples).

`agentsociety/prompts/blocks/shared/sleep_time_estimate_citysim_v1_0.toml`:
- `metadata.name = "sleep_time_estimate"` (same name as existing `other_sleep_time_estimate` — bump version to 2.0.0 if reusing name, or use new name and update Python string).
- Inputs: shared inputs minus `work_ethic`.
- Chronotype description: sleep-specific wording.

**Python changes:**
- `other_block.py:112` — `OtherNoneBlock.__init__`: change `self.prompt_name = "other_time_estimate"` to `self.prompt_name = "activity_time_estimate"`.
- `social_block.py:32` — `SocialNoneBlock.__init__`: change `self.time_estimate_prompt_name = "social_time_estimate"` to `self.time_estimate_prompt_name = "activity_time_estimate"`.
- `economy_block.py:67` — `WorkBlock.__init__`: change `self.prompt_name = "worktime_estimate"` to `self.prompt_name = "activity_time_estimate"`.
- `other_block.py:41` — `SleepBlock.__init__`: change `self.prompt_name = "other_sleep_time_estimate"` to `self.prompt_name = "sleep_time_estimate"`.

No other Python code changes needed. All four blocks use the identical `get_required_fields` / `build_agent_state` / `format_prompt_to_dialog` pattern.

---

### Step 2 — Merge the three mobility place-selection prompts into one

**Before:**
- `mobility_place_type_selection_agentsociety_v1_0.toml` — `metadata.name = "mobility_place_type_selection"`
- `mobility_place_second_type_selection_agentsociety_v1_0.toml` — `metadata.name = "mobility_place_second_type_selection"`
- `mobility_place_analysis_agentsociety_v1_0.toml` — `metadata.name = "mobility_place_analysis"`

All three are called from `place_selection_block.py` (to be confirmed below — see Open Questions about which prompt names are used).

**After (new file to create):**

`agentsociety/prompts/blocks/mobilityblock/mobility_place_selection_citysim_v1_0.toml`:
- `metadata.name = "mobility_place_selection"`
- Unified input field: `options` (replaces both `poi_category` and `place_list`).
- Prompt body: identical to the three existing prompts, using `{options}` as the variable.
- No hardcoded `categories` in `[outputs.place_type]` — validation is the caller's responsibility.

**Python changes in `place_selection_block.py`:**
- Every call site that uses `"mobility_place_type_selection"`, `"mobility_place_second_type_selection"`, or `"mobility_place_analysis"` must:
  1. Change `self.prompt_name` to `"mobility_place_selection"`.
  2. Change the context key for the options variable from `poi_category` or `place_list` to `options`.

---

### Step 3 — Preserve originals as tombstones

Leave all original TOML files in place but lower their versions by adding a `deprecated = true` metadata key (for documentation). The `PromptManager` will continue to load them alongside the new files; since the new files have higher versions, they win automatically (`prompt_manager.py:81-88`). The old names (`other_time_estimate`, `worktime_estimate`, etc.) are simply no longer referenced by Python code, so they become dead weight but cause no harm.

## Trade-Offs

| What is gained | What is sacrificed |
|---|---|
| Single source of truth for time-estimate prompt wording | Each block can no longer independently diverge its examples list without forking |
| Big Five block description update requires editing one file | Short-term churn: 4 Python string changes + 2 new TOML files |
| Mobility place prompts: one file to audit and update | Caller must rename the context key from `poi_category`/`place_list` to `options` |
| Cleaner `prompts/` directory | The old TOML files remain as tombstones (disk noise, but safe) |
| Future prompt improvements benefit all callers at once | Activity-domain-specific examples are lost in the merged prompt (see Rejected Approaches) |

## Rejected Approaches

**Approach: Single unified time-estimate prompt with `activity_domain` selector input.**
Why rejected: TOML has no conditional rendering. The `PromptManager` does simple string interpolation (`prompt_manager.py:316`). To vary the examples block by domain, the Python caller would need to inject the entire examples sub-string as a field value, losing the readability benefit of a TOML template. The two-file split (activity/sleep) achieves the same deduplication goal without this complexity.

**Approach: Add TOML include/inherit mechanism to `PromptManager`.**
Why rejected: This is a significant scope expansion to the infrastructure layer. It would benefit the cognition persona header duplication (Group 3) and the Big Five input block (Group 4), but those are lower-priority than the time-estimate and mobility groups. Doing this first would delay the high-value deduplication. Noted in Proposed Next Steps as a future option.

**Approach: Merge all three cognition update prompts (`thought_update`, `emotion_update`, `attitude_update`) into one with a `task` parameter.**
Why rejected: While the persona header is identical, the body (the actual task instruction and output schema) is completely different in all three. A unified prompt would require conditional rendering that TOML cannot express, and the output schemas differ in field names and types. These prompts should remain separate.

**Approach: Merge `mobility_neighborhood_selection` with `mobility_aoi_area_selection`.**
Why rejected: On surface inspection these look similar (both select 3-5 area IDs from a ranked list), but they operate at different geographic abstraction levels, have different input field names (`candidate_neighborhoods` vs `ranked_areas`), and return different key names (`selected_neighborhood_ids` vs `selected_area_ids`). Merging them would obscure that semantic difference.

**Approach: Delete old TOML files immediately.**
Why rejected: The `PromptManager` scans the entire directory. Deleting files before confirming the new prompts work correctly in a live run removes the ability to quickly revert by pointing `active_config` at the old name+version.

## Assumptions & Open Questions

1. **Which prompt names does `place_selection_block.py` use?** The file was not read in full during exploration. Before Step 2 can be committed, confirm that the three mobility place-selection prompt names appear as `self.prompt_name` strings in that file, and confirm the exact context key names used when calling `build_agent_state`.

2. **`intention` vs `current_intention` field name choice.** The `PromptMemoryHandler` resolves both field names to the same memory path (`prompt_memory_handler.py:154`). However, `WorkBlock.forward()` at `economy_block.py:88` passes `required_fields` to `build_agent_state` with `context` derived from the caller-supplied `DotDict`. Confirm that switching from `current_intention` to `intention` in the TOML does not break the `build_agent_state` resolution path for that specific call.

3. **`social_frequency` input in `social_time_estimate` — present or absent?** A check of `social_time_estimate_agentsociety_v1_0.toml` shows it does NOT include `social_frequency` (unlike the needs-related prompts). The merged `activity_time_estimate` should also omit it.

4. **Are there other callers of the four time-estimate prompt names outside the three block files identified?** A grep for the exact strings `"other_time_estimate"`, `"social_time_estimate"`, `"worktime_estimate"`, `"other_sleep_time_estimate"` should be run before the refactor to confirm no additional callers exist in institution agent files or tests.

## Code That Could Be Refactored *(informational)*

- `agentsociety/prompts/blocks/cognitionblock/cognition_initialize_big5_agentsociety_v1_0.toml:71-73` — The `DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.` instruction is repeated three times. This is a copy-paste artifact and could be reduced to one line.
- `agentsociety/prompts/blocks/cognitionblock/cognition_initialize_preferences_agentsociety_v1_0.toml:84-86` — Same triple-repeat artifact.
- `agentsociety/prompts/blocks/needsblock/needs_initialize_agentsociety_v1_0.toml:119-121` — Same triple-repeat artifact.
- `agentsociety/cityagent/blocks/plan_block.py:70-92` — `select_guidance()` manually computes `current_location` using the same position-checking logic that `PromptMemoryHandler.resolve_location()` already implements (`prompt_memory_handler.py:81-114`). The method could delegate this to the handler via `build_agent_state` instead.
- `agentsociety/prompts/prompt_memory_handler.py:193-199` — The generic fallback `resolve_field` silently returns `"unknown"` for unregistered fields. Any TOML input field that is not registered in `build_handlers()` and not supplied in the caller `context` dict will produce `"unknown"` with no warning. Adding a `get_logger().warning()` here would surface misconfigured prompts during development.

## Proposed Next Steps

1. **Confirm call sites** — grep for all four time-estimate prompt name strings and all three mobility place-selection strings across the entire Python codebase to ensure no hidden callers (institution agents, test scripts, etc.).

2. **Confirm `place_selection_block.py` field names** — read the file in full to verify `poi_category` and `place_list` are the exact context keys used, and which of the three prompt names each call site uses.

3. **Create `agentsociety/prompts/blocks/shared/` directory** with two new TOML files (`activity_time_estimate_citysim_v1_0.toml`, `sleep_time_estimate_citysim_v1_0.toml`).

4. **Create `agentsociety/prompts/blocks/mobilityblock/mobility_place_selection_citysim_v1_0.toml`**.

5. **Update Python prompt name strings** — 4 changes in `other_block.py`, `social_block.py`, `economy_block.py`; N changes in `place_selection_block.py` (count after step 2).

6. **Run a simulation** using `sh tests/run_e2e_tests.sh` to confirm behavior is unchanged.

7. **Optional future work** — Evaluate adding an `[includes]` or TOML-anchor mechanism to `PromptManager` to address Group 3 (cognition persona header) and Group 4 (Big Five input block) without code duplication.
