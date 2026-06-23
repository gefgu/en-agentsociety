# {py:mod}`en_agentsociety.agent.prompt`

```{py:module} en_agentsociety.agent.prompt
```

```{autodoc2-docstring} en_agentsociety.agent.prompt
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`FormatPrompt <en_agentsociety.agent.prompt.FormatPrompt>`
  - ```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt
    :summary:
    ```
````

### API

`````{py:class} FormatPrompt(template: str, format_prompt: typing.Optional[str] = None, system_prompt: typing.Optional[str] = None, memory: typing.Optional[en_agentsociety.memory.Memory] = None)
:canonical: en_agentsociety.agent.prompt.FormatPrompt

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt.__init__
```

````{py:method} _extract_variables() -> list[str]
:canonical: en_agentsociety.agent.prompt.FormatPrompt._extract_variables

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt._extract_variables
```

````

````{py:method} _is_safe_expression(expr: str) -> bool
:canonical: en_agentsociety.agent.prompt.FormatPrompt._is_safe_expression

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt._is_safe_expression
```

````

````{py:method} _eval_expr(expr: str, context: dict) -> typing.Any
:canonical: en_agentsociety.agent.prompt.FormatPrompt._eval_expr
:async:

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt._eval_expr
```

````

````{py:method} format(context: typing.Optional[dict] = None, **kwargs) -> str
:canonical: en_agentsociety.agent.prompt.FormatPrompt.format
:async:

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt.format
```

````

````{py:method} to_dialog() -> list[openai.types.chat.ChatCompletionMessageParam]
:canonical: en_agentsociety.agent.prompt.FormatPrompt.to_dialog

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt.to_dialog
```

````

````{py:method} log() -> None
:canonical: en_agentsociety.agent.prompt.FormatPrompt.log

```{autodoc2-docstring} en_agentsociety.agent.prompt.FormatPrompt.log
```

````

`````
