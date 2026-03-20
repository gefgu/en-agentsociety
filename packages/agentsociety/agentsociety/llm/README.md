# `llm/` — LLM Adapter

This package provides a unified LLM client that works with any OpenAI-compatible API.

---

## Files

| File | Purpose |
|---|---|
| `llm.py` | `LLM` class and `LLMConfig` |

---

## Features

- **OpenAI-compatible API**: Works with OpenAI, Azure OpenAI, vLLM, Ollama, and any other provider that supports the OpenAI REST format.
- **Round-robin load balancing**: Pass multiple `LLMConfig` entries to distribute load across providers or API keys.
- **Token tracking**: Automatically records input/output token counts per call for cost monitoring.
- **Embedding support**: The same client supports text embedding requests alongside completions.
- **Error handling**: Automatic retries with exponential back-off on rate-limit and server errors.
- **Async-native**: All methods are `async` for non-blocking use inside Ray actors.

---

## `LLMConfig`

```python
class LLMConfig(BaseModel):
    model: str                    # e.g. "gpt-4o", "qwen-max"
    api_key: str
    base_url: str                 # e.g. "https://api.openai.com/v1"
    max_tokens: int = 4096
    temperature: float = 1.0
    # ... additional OpenAI parameters
```

---

## `LLM` API

```python
llm = LLM(configs=[LLMConfig(...)])

# Chat completion
response: str = await llm.atext_request(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "Hello!"},
    ]
)

# Function-calling completion
response = await llm.atext_request(
    messages=[...],
    tools=[{...}],              # OpenAI function-calling tools schema
    tool_choice="auto",
)

# Text embedding
vectors = await llm.aembedding_request(texts=["hello world", "foo bar"])

# Token usage
usage = llm.get_token_usage()    # {"prompt_tokens": N, "completion_tokens": M}
```

---

## Round-Robin Example

```python
llm = LLM(configs=[
    LLMConfig(model="gpt-4o",    api_key="sk-aaa", base_url="https://api.openai.com/v1"),
    LLMConfig(model="gpt-4o",    api_key="sk-bbb", base_url="https://api.openai.com/v1"),
    LLMConfig(model="qwen-max",  api_key="...",    base_url="https://dashscope.aliyuncs.com/..."),
])
# Each call automatically rotates among the three providers
```

---

## Notes

- The `LLM` instance is shared across all agents within an `AgentGroup` via the `AgentToolbox`.
- Token usage is aggregated at the engine level and written to the experiment's storage record for cost tracking.
