# VLLM Configuration Fix Guide

## Problem Summary

You encountered two types of errors when using the Qwen3-32B-AWQ model via Modal/vLLM:

1. **"Error parsing guidance selection response: Invalid guidance selection format"**
2. **"Initial response error: 'current_satisfaction'"**

These errors occurred because the model was not returning properly formatted JSON responses.

## Root Causes

### 1. Tool Calling Parser Interference
Your Modal configuration included:
```python
"--enable-auto-tool-choice",
"--tool-call-parser", "hermes",
```

These flags make vLLM interpret ALL JSON responses as tool calls, which interferes with the `response_format={"type": "json_object"}` mode that your application uses for regular JSON responses.

### 2. System Role Support
The Qwen model served via vLLM may not properly support system roles in message dialogs, leading to confused responses.

### 3. Insufficient Context Length
The original `max-model-len` of 8096 tokens may be too short for complex agent reasoning tasks.

### 4. Ambiguous JSON Instructions
The prompts didn't explicitly emphasize the JSON-only requirement, allowing the model to add commentary or use incorrect formats.

## Solutions Implemented

### 1. Fixed Modal vLLM Configuration ✅

Created new file: `modal_vllm_fixed.py`

**Key changes:**
- ❌ Removed `--enable-auto-tool-choice` (causing JSON parsing issues)
- ❌ Removed `--tool-call-parser hermes` (interfering with response_format)
- ✅ Increased `--max-model-len` from 8096 to 16384 (better context handling)
- ✅ Added `--guided-decoding-backend outlines` (better JSON mode support)

**To deploy the fixed configuration:**
```bash
cd /mnt/raid5/gustavo/agentsociety/packages/agentsociety/agentsociety
modal deploy modal_vllm_fixed.py
```

Then update your LLM config to use the new endpoint:
```python
llm_config3 = LLMConfig(
    provider=LLMProviderType.VLLM,
    base_url="https://gustavohenriquesantos--qwen32b-awq-fixed-serve.modal.run/v1",
    api_key="EMPTY",
    model="Qwen/Qwen3-32B-AWQ",
    concurrency=30,
    timeout=300,
)
```

### 2. Improved LLM Client ✅

Modified `llm/llm.py`:

**Key improvements:**
- ✅ LLMActor now accepts provider parameter to configure system role support
- ✅ Proactively disables system role for VLLM and DeepSeek providers
- ✅ Better error logging for JSON parsing failures with response content preview
- ✅ Passes provider info to all actors for consistent behavior

**What this fixes:**
- System messages are automatically converted to user messages for VLLM
- More detailed error messages help debug future issues
- Consistent behavior across all actor instances

### 3. Enhanced Prompt Instructions ✅

Modified `cityagent/blocks/plan_block.py` and `cityagent/blocks/needs_block.py`:

**Prompt improvements:**
```
IMPORTANT: You MUST respond with ONLY valid JSON. Do not include any text before or after the JSON.
Your response must be a single JSON object with this EXACT structure:
{
    "key": value
}

All numeric scores MUST be between 0 and 1.
```

**Error handling improvements:**
- Added retry attempts WITH new LLM requests (not just re-parsing)
- Lower temperature (0.5-0.7) on retries for more consistent output
- Better error logging showing raw response content (first 500 chars)
- Attempt counter in log messages (e.g., "attempt 1/3")

## How to Apply the Fixes

### Step 1: Update your Modal deployment
```bash
cd /mnt/raid5/gustavo/agentsociety/packages/agentsociety/agentsociety
modal deploy modal_vllm_fixed.py
```

### Step 2: Update your configuration
Change your LLM config to use the new endpoint:
```python
from agentsociety.llm import LLMConfig, LLMProviderType

llm_config = LLMConfig(
    provider=LLMProviderType.VLLM,
    base_url="https://gustavohenriquesantos--qwen32b-awq-fixed-serve.modal.run/v1",
    api_key="EMPTY",
    model="Qwen/Qwen3-32B-AWQ",
    concurrency=30,
    timeout=300,
)
```

### Step 3: Restart your application
The code changes to `llm.py`, `plan_block.py`, and `needs_block.py` are already applied and will take effect on restart.

## Expected Improvements

After applying these fixes, you should see:

1. **Fewer JSON parsing errors**: The model will reliably return valid JSON
2. **Better error messages**: When errors do occur, you'll see detailed logs with response content
3. **Automatic retries**: Failed JSON parses will trigger new LLM requests with adjusted parameters
4. **No system role errors**: Messages are automatically converted for VLLM compatibility

## Monitoring

Watch your logs for these improved messages:
```
✅ Good: Successful JSON parsing (no logs)
⚠️  Warning: "Error parsing guidance selection response (attempt 1/3): ..."
   Shows attempt number and raw response for debugging
❌ Error: "JSON parsing error from LLM: ..."
   Shows response content from model
```

## Testing

Test the fixes with a simple simulation run:
```python
from agentsociety import SimulationEngine, Config

# Your config with the new LLM settings
config = Config(...)
engine = SimulationEngine(config)
await engine.init()
await engine.step()  # Should execute without JSON parsing errors
```

## Additional Optimizations (Optional)

If you still see occasional errors, consider:

1. **Further reduce temperature**: Change default from 1.0 to 0.7 in prompts
2. **Add few-shot examples**: Include 2-3 valid JSON examples in prompts
3. **Use structured output**: If available in future vLLM versions
4. **Model fine-tuning**: Fine-tune Qwen on your specific JSON formats

## Rollback (if needed)

If the new configuration causes issues:

1. Redeploy original Modal configuration
2. Revert llm.py changes:
```bash
git checkout llm/llm.py
git checkout cityagent/blocks/plan_block.py
git checkout cityagent/blocks/needs_block.py
```

## Additional Notes

- The `--guided-decoding-backend outlines` flag requires vLLM 0.13.0+
- Max model length of 16384 uses more VRAM (~20GB vs 15GB)
- System role conversion adds minimal latency (~5ms)
- Lower temperatures (0.5-0.7) reduce creativity but improve consistency

## Support

If errors persist after applying all fixes, check:

1. Modal deployment logs: `modal logs qwen32b-awq-fixed`
2. Application logs: Look for "JSON parsing error from LLM" messages
3. Model response content: Check the truncated response in error logs
4. Network connectivity: Ensure stable connection to Modal endpoint

## Summary of Changes

| Component | Change | Benefit |
|-----------|--------|---------|
| Modal config | Removed tool calling parser | Fixes JSON mode interference |
| Modal config | Increased context length | Better reasoning capability |
| Modal config | Added guided decoding | Improved JSON structure |
| LLM client | System role autoconversion | VLLM compatibility |
| LLM client | Better error logging | Easier debugging |
| Prompts | Explicit JSON instructions | Clearer model expectations |
| Error handling | Retry with new requests | Higher success rate |

---

**Created**: 2026-02-21  
**Last Updated**: 2026-02-21  
**Status**: Ready for deployment
