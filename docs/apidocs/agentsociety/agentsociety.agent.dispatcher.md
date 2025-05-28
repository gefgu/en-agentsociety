# {py:mod}`agentsociety.agent.dispatcher`

```{py:module} agentsociety.agent.dispatcher
```

```{autodoc2-docstring} agentsociety.agent.dispatcher
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`BlockDispatcher <agentsociety.agent.dispatcher.BlockDispatcher>`
  - ```{autodoc2-docstring} agentsociety.agent.dispatcher.BlockDispatcher
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DISPATCHER_PROMPT <agentsociety.agent.dispatcher.DISPATCHER_PROMPT>`
  - ```{autodoc2-docstring} agentsociety.agent.dispatcher.DISPATCHER_PROMPT
    :summary:
    ```
````

### API

````{py:data} DISPATCHER_PROMPT
:canonical: agentsociety.agent.dispatcher.DISPATCHER_PROMPT
:value: <Multiline-String>

```{autodoc2-docstring} agentsociety.agent.dispatcher.DISPATCHER_PROMPT
```

````

`````{py:class} BlockDispatcher(llm: agentsociety.llm.LLM, memory: agentsociety.memory.Memory, selection_prompt: str = DISPATCHER_PROMPT)
:canonical: agentsociety.agent.dispatcher.BlockDispatcher

```{autodoc2-docstring} agentsociety.agent.dispatcher.BlockDispatcher
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.agent.dispatcher.BlockDispatcher.__init__
```

````{py:method} register_blocks(blocks: list[agentsociety.agent.block.Block]) -> None
:canonical: agentsociety.agent.dispatcher.BlockDispatcher.register_blocks

```{autodoc2-docstring} agentsociety.agent.dispatcher.BlockDispatcher.register_blocks
```

````

````{py:method} _get_function_schema() -> openai.types.chat.ChatCompletionToolParam
:canonical: agentsociety.agent.dispatcher.BlockDispatcher._get_function_schema

```{autodoc2-docstring} agentsociety.agent.dispatcher.BlockDispatcher._get_function_schema
```

````

````{py:method} dispatch(context: agentsociety.agent.context.DotDict) -> agentsociety.agent.block.Block | None
:canonical: agentsociety.agent.dispatcher.BlockDispatcher.dispatch
:async:

```{autodoc2-docstring} agentsociety.agent.dispatcher.BlockDispatcher.dispatch
```

````

`````
