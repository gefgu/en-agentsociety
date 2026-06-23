# {py:mod}`en_agentsociety.agent.dispatcher`

```{py:module} en_agentsociety.agent.dispatcher
```

```{autodoc2-docstring} en_agentsociety.agent.dispatcher
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`BlockDispatcher <en_agentsociety.agent.dispatcher.BlockDispatcher>`
  - ```{autodoc2-docstring} en_agentsociety.agent.dispatcher.BlockDispatcher
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DISPATCHER_PROMPT <en_agentsociety.agent.dispatcher.DISPATCHER_PROMPT>`
  - ```{autodoc2-docstring} en_agentsociety.agent.dispatcher.DISPATCHER_PROMPT
    :summary:
    ```
````

### API

````{py:data} DISPATCHER_PROMPT
:canonical: en_agentsociety.agent.dispatcher.DISPATCHER_PROMPT
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.agent.dispatcher.DISPATCHER_PROMPT
```

````

`````{py:class} BlockDispatcher(toolbox: en_agentsociety.agent.toolbox.AgentToolbox, agent_memory: en_agentsociety.memory.Memory, selection_prompt: str = DISPATCHER_PROMPT)
:canonical: en_agentsociety.agent.dispatcher.BlockDispatcher

```{autodoc2-docstring} en_agentsociety.agent.dispatcher.BlockDispatcher
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.dispatcher.BlockDispatcher.__init__
```

````{py:method} register_dispatcher_prompt(dispatcher_prompt: str) -> None
:canonical: en_agentsociety.agent.dispatcher.BlockDispatcher.register_dispatcher_prompt

```{autodoc2-docstring} en_agentsociety.agent.dispatcher.BlockDispatcher.register_dispatcher_prompt
```

````

````{py:method} register_blocks(blocks: list[en_agentsociety.agent.block.Block]) -> None
:canonical: en_agentsociety.agent.dispatcher.BlockDispatcher.register_blocks

```{autodoc2-docstring} en_agentsociety.agent.dispatcher.BlockDispatcher.register_blocks
```

````

````{py:method} _get_function_schema() -> openai.types.chat.ChatCompletionToolParam
:canonical: en_agentsociety.agent.dispatcher.BlockDispatcher._get_function_schema

```{autodoc2-docstring} en_agentsociety.agent.dispatcher.BlockDispatcher._get_function_schema
```

````

````{py:method} dispatch(context: en_agentsociety.agent.context.DotDict) -> en_agentsociety.agent.block.Block | None
:canonical: en_agentsociety.agent.dispatcher.BlockDispatcher.dispatch
:async:

```{autodoc2-docstring} en_agentsociety.agent.dispatcher.BlockDispatcher.dispatch
```

````

`````
