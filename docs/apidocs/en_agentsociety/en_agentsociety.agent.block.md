# {py:mod}`en_agentsociety.agent.block`

```{py:module} en_agentsociety.agent.block
```

```{autodoc2-docstring} en_agentsociety.agent.block
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`BlockParams <en_agentsociety.agent.block.BlockParams>`
  -
* - {py:obj}`BlockOutput <en_agentsociety.agent.block.BlockOutput>`
  -
* - {py:obj}`Block <en_agentsociety.agent.block.Block>`
  - ```{autodoc2-docstring} en_agentsociety.agent.block.Block
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`TRIGGER_INTERVAL <en_agentsociety.agent.block.TRIGGER_INTERVAL>`
  - ```{autodoc2-docstring} en_agentsociety.agent.block.TRIGGER_INTERVAL
    :summary:
    ```
* - {py:obj}`__all__ <en_agentsociety.agent.block.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.agent.block.__all__
    :summary:
    ```
````

### API

````{py:data} TRIGGER_INTERVAL
:canonical: en_agentsociety.agent.block.TRIGGER_INTERVAL
:value: >
   1

```{autodoc2-docstring} en_agentsociety.agent.block.TRIGGER_INTERVAL
```

````

````{py:data} __all__
:canonical: en_agentsociety.agent.block.__all__
:value: >
   ['Block', 'BlockParams', 'BlockOutput']

```{autodoc2-docstring} en_agentsociety.agent.block.__all__
```

````

`````{py:class} BlockParams(/, **data: typing.Any)
:canonical: en_agentsociety.agent.block.BlockParams

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} block_memory
:canonical: en_agentsociety.agent.block.BlockParams.block_memory
:type: typing.Optional[dict[str, typing.Any]]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.block.BlockParams.block_memory
```

````

`````

```{py:class} BlockOutput(/, **data: typing.Any)
:canonical: en_agentsociety.agent.block.BlockOutput

Bases: {py:obj}`pydantic.BaseModel`

```

`````{py:class} Block(toolbox: en_agentsociety.agent.toolbox.AgentToolbox, agent_memory: typing.Optional[en_agentsociety.memory.Memory] = None, block_params: typing.Optional[typing.Any] = None)
:canonical: en_agentsociety.agent.block.Block

```{autodoc2-docstring} en_agentsociety.agent.block.Block
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.block.Block.__init__
```

````{py:attribute} ParamsType
:canonical: en_agentsociety.agent.block.Block.ParamsType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.block.Block.ParamsType
```

````

````{py:attribute} Context
:canonical: en_agentsociety.agent.block.Block.Context
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.block.Block.Context
```

````

````{py:attribute} OutputType
:canonical: en_agentsociety.agent.block.Block.OutputType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.block.Block.OutputType
```

````

````{py:attribute} NeedAgent
:canonical: en_agentsociety.agent.block.Block.NeedAgent
:type: bool
:value: >
   False

```{autodoc2-docstring} en_agentsociety.agent.block.Block.NeedAgent
```

````

````{py:attribute} name
:canonical: en_agentsociety.agent.block.Block.name
:type: str
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.agent.block.Block.name
```

````

````{py:attribute} description
:canonical: en_agentsociety.agent.block.Block.description
:type: str
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.agent.block.Block.description
```

````

````{py:attribute} actions
:canonical: en_agentsociety.agent.block.Block.actions
:type: dict[str, str]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.block.Block.actions
```

````

````{py:method} default_params() -> ParamsType
:canonical: en_agentsociety.agent.block.Block.default_params
:classmethod:

```{autodoc2-docstring} en_agentsociety.agent.block.Block.default_params
```

````

````{py:method} default_context() -> Context
:canonical: en_agentsociety.agent.block.Block.default_context
:classmethod:

```{autodoc2-docstring} en_agentsociety.agent.block.Block.default_context
```

````

````{py:method} __init_subclass__(**kwargs)
:canonical: en_agentsociety.agent.block.Block.__init_subclass__
:classmethod:

```{autodoc2-docstring} en_agentsociety.agent.block.Block.__init_subclass__
```

````

````{py:method} set_agent(agent: typing.Any)
:canonical: en_agentsociety.agent.block.Block.set_agent

```{autodoc2-docstring} en_agentsociety.agent.block.Block.set_agent
```

````

````{py:property} agent
:canonical: en_agentsociety.agent.block.Block.agent
:type: typing.Any

```{autodoc2-docstring} en_agentsociety.agent.block.Block.agent
```

````

````{py:property} toolbox
:canonical: en_agentsociety.agent.block.Block.toolbox
:type: en_agentsociety.agent.toolbox.AgentToolbox

```{autodoc2-docstring} en_agentsociety.agent.block.Block.toolbox
```

````

````{py:property} llm
:canonical: en_agentsociety.agent.block.Block.llm
:type: en_agentsociety.llm.LLM

```{autodoc2-docstring} en_agentsociety.agent.block.Block.llm
```

````

````{py:property} memory
:canonical: en_agentsociety.agent.block.Block.memory
:type: en_agentsociety.memory.Memory

```{autodoc2-docstring} en_agentsociety.agent.block.Block.memory
```

````

````{py:property} agent_memory
:canonical: en_agentsociety.agent.block.Block.agent_memory
:type: en_agentsociety.memory.Memory

```{autodoc2-docstring} en_agentsociety.agent.block.Block.agent_memory
```

````

````{py:property} block_memory
:canonical: en_agentsociety.agent.block.Block.block_memory
:type: en_agentsociety.memory.KVMemory

```{autodoc2-docstring} en_agentsociety.agent.block.Block.block_memory
```

````

````{py:property} environment
:canonical: en_agentsociety.agent.block.Block.environment
:type: en_agentsociety.environment.Environment

```{autodoc2-docstring} en_agentsociety.agent.block.Block.environment
```

````

````{py:method} before_forward()
:canonical: en_agentsociety.agent.block.Block.before_forward
:async:

```{autodoc2-docstring} en_agentsociety.agent.block.Block.before_forward
```

````

````{py:method} after_forward()
:canonical: en_agentsociety.agent.block.Block.after_forward
:async:

```{autodoc2-docstring} en_agentsociety.agent.block.Block.after_forward
```

````

````{py:method} forward(agent_context: en_agentsociety.agent.context.DotDict)
:canonical: en_agentsociety.agent.block.Block.forward
:abstractmethod:
:async:

```{autodoc2-docstring} en_agentsociety.agent.block.Block.forward
```

````

`````
