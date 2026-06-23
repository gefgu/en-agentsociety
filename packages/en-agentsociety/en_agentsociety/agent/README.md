# `agent/` — Agent Base Framework

This package contains the base classes, interfaces, and utilities that all agents and blocks are built on. It is the core abstraction layer of AgentSociety.

---

## Files

| File | Purpose |
|---|---|
| `agent_base.py` | Abstract `Agent` base class and `AgentType` enum |
| `agent.py` | Concrete agent base classes: `CitizenAgentBase`, `IndividualAgentBase`, `SupervisorBase`, institution bases |
| `block.py` | `Block` base class, `BlockParams`, `BlockOutput` |
| `context.py` | `AgentContext`, `BlockContext`, `DotDict`, and context utilities |
| `decorator.py` | `@register_get` and `@param_docs` decorators |
| `dispatcher.py` | `BlockDispatcher` — LLM-powered block router |
| `distribution.py` | `Distribution` and `DistributionConfig` for random attribute sampling |
| `memory_config_generator.py` | `MemoryAttribute`, `MemoryConfig`, `MemoryConfigGenerator` |
| `prompt.py` | `FormatPrompt` — template-based prompt construction from memory + context |
| `toolbox.py` | `AgentToolbox` and `CustomTool` — shared services container |

---

## Key Types

### `Agent` (abstract)

```python
class Agent(ABC):
    ParamsType: type[AgentParams]      # agent configuration schema
    Context: type[AgentContext]        # context schema
    BlockOutputType: type[BlockOutput] # expected output from blocks
    StatusAttributes: list[MemoryAttribute]  # memory field declarations

    async def forward(self): ...       # main decision loop — implement this
```

### `Block` (abstract)

```python
class Block:
    name: str                   # unique block name
    description: str            # used by BlockDispatcher for routing
    OutputType: type[BlockOutput]
    NeedAgent: bool = False     # inject parent agent if True

    async def forward(self, context) -> BlockOutput: ...
```

### `AgentToolbox`

Shared services injected into every agent and block:

- `toolbox.llm` — LLM client
- `toolbox.environment` — city environment client
- `toolbox.messager` — message bus
- `toolbox.database_writer` — persistence writer
- `toolbox.embedding` — sparse text embedding model
- `toolbox.add_tool(tool)` / `toolbox.get_tool(name)` — custom tool management

### `BlockDispatcher`

Routes agent intentions to blocks via LLM function-calling:

```python
dispatcher.register_blocks([block1, block2])
block, output = await dispatcher.dispatch(context)
```

### `FormatPrompt`

Template engine filling `${memory.field}` and `{variable}` placeholders:

```python
prompt = FormatPrompt("Hello ${profile.name}, your energy is ${status.energy}.", memory=mem)
text = await prompt.format(context, extra_var="value")
```

### `@register_get`

Decorator that exposes agent methods as queryable getters:

```python
@register_get("Current hunger level")
async def get_hunger(self) -> float:
    return await self.memory.status.get("hunger_satisfaction")
```

### `DotDict`

Dictionary with attribute-style access, used for context objects:

```python
ctx = DotDict({"intention": "rest"})
ctx.intention    # "rest"
ctx["intention"] # "rest"
ctx.new_key = "value"  # auto-creates key
```

---

## Agent Type Hierarchy

```
Agent (ABC)
├── CitizenAgentBase    — city simulation citizen
│   └── SocietyAgent   (cityagent/)
├── IndividualAgentBase — task-solving agent
├── SupervisorBase      — oversight / message interception
├── FirmAgentBase       — institution: firm
├── BankAgentBase       — institution: bank
├── GovernmentAgentBase — institution: government
└── NBSAgentBase        — institution: national bureau of statistics
```

---

## Adding a New Agent Type

1. Subclass the appropriate base class.
2. Declare `StatusAttributes` for memory fields.
3. Implement `async def forward(self)`.
4. Use `@register_get` for observable properties.
5. Provide a list of `Block` subclasses via `AgentConfig(blocks=[...])`.
