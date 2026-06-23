# prompts migration guide

This folder contains TOML prompt definitions used by `PromptManager`.

## 1. Add a TOML prompt file

Create a file under `prompts/blocks/<blockname>/` using the naming style:

`<prompt_name>_<origin>_v<major>_<minor>.toml`

Required structure:

```toml
[metadata]
name = "worktime_estimate"
version = "1.1.0"
origin = "citysim"
description = "What this prompt does"

[inputs]
[inputs.plan]
type = "text"
description = "Current plan details."

[inputs.current_intention]
type = "text"
description = "Current intention text."

[inputs.work_ethic]
type = "categorical"
description = "Work ethic level."

[prompt]
input = """Your prompt text with {placeholders}."""
```

Rules:
- `metadata.name` is the key you use in code.
- All `[inputs.<field>]` entries are treated as required prompt fields.
- Use `{field}` placeholders only.

## 2. Use PromptManager in the block

In your block `forward()`:

```python
if self.prompt_manager is None:
    raise RuntimeError("PromptManager is not initialized")

prompt_name = "worktime_estimate"
required_fields = self.prompt_manager.get_required_fields(prompt_name)

# context_extra is optional extra data (precomputed values, expensive calls, etc.)
state = await self.prompt_manager.build_agent_state(
    required_fields=required_fields,
    context=context_extra,
    memory=self.memory,
)

dialog = self.prompt_manager.format_prompt_to_dialog(prompt_name, state)
result = await self.llm.atext_request(dialog, response_format={"type": "json_object"})
```

## 3. Fetch only what is required

Use `required_fields` to avoid unnecessary work:
- Compute expensive values only if their field exists in typed inputs.
- Put precomputed values into `context` so `PromptManager` uses them first.
- Let `build_agent_state()` fetch remaining fields from memory.

## 4. Fallback behavior

Prompt resolution order:
1. exact match (`name + version + origin`)
2. same `name + version` with different origin
3. highest available version for the name

If `active_config` is empty/None, latest version for each prompt name is loaded.

## 5. Migration checklist

- Move inline prompt string into TOML.
- Add typed `[inputs.<field>]` entries for all placeholders.
- Replace inline formatting with `PromptManager` calls.
- Keep parsing/business logic unchanged.
- Validate prompt output format (`json_object` if needed).
