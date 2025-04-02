# {py:mod}`agentsociety.agent.block`

```{py:module} agentsociety.agent.block
```

```{autodoc2-docstring} agentsociety.agent.block
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Block <agentsociety.agent.block.Block>`
  - ```{autodoc2-docstring} agentsociety.agent.block.Block
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`log_and_check_with_memory <agentsociety.agent.block.log_and_check_with_memory>`
  - ```{autodoc2-docstring} agentsociety.agent.block.log_and_check_with_memory
    :summary:
    ```
* - {py:obj}`log_and_check <agentsociety.agent.block.log_and_check>`
  - ```{autodoc2-docstring} agentsociety.agent.block.log_and_check
    :summary:
    ```
* - {py:obj}`trigger_class <agentsociety.agent.block.trigger_class>`
  - ```{autodoc2-docstring} agentsociety.agent.block.trigger_class
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`TRIGGER_INTERVAL <agentsociety.agent.block.TRIGGER_INTERVAL>`
  - ```{autodoc2-docstring} agentsociety.agent.block.TRIGGER_INTERVAL
    :summary:
    ```
* - {py:obj}`__all__ <agentsociety.agent.block.__all__>`
  - ```{autodoc2-docstring} agentsociety.agent.block.__all__
    :summary:
    ```
````

### API

````{py:data} TRIGGER_INTERVAL
:canonical: agentsociety.agent.block.TRIGGER_INTERVAL
:value: >
   1

```{autodoc2-docstring} agentsociety.agent.block.TRIGGER_INTERVAL
```

````

````{py:data} __all__
:canonical: agentsociety.agent.block.__all__
:value: >
   ['Block', 'log_and_check', 'log_and_check_with_memory', 'trigger_class']

```{autodoc2-docstring} agentsociety.agent.block.__all__
```

````

````{py:function} log_and_check_with_memory(condition: typing.Union[collections.abc.Callable[[agentsociety.memory.Memory], collections.abc.Coroutine[typing.Any, typing.Any, bool]], collections.abc.Callable[[], collections.abc.Coroutine[typing.Any, typing.Any, bool]], collections.abc.Callable[[agentsociety.memory.Memory], bool], collections.abc.Callable[[], bool]] = lambda: True, trigger_interval: float = TRIGGER_INTERVAL, record_function_calling: bool = False)
:canonical: agentsociety.agent.block.log_and_check_with_memory

```{autodoc2-docstring} agentsociety.agent.block.log_and_check_with_memory
```
````

````{py:function} log_and_check(condition: typing.Union[collections.abc.Callable[[], collections.abc.Coroutine[typing.Any, typing.Any, bool]], collections.abc.Callable[[], bool]] = lambda: True, trigger_interval: float = TRIGGER_INTERVAL, record_function_calling: bool = False)
:canonical: agentsociety.agent.block.log_and_check

```{autodoc2-docstring} agentsociety.agent.block.log_and_check
```
````

````{py:function} trigger_class()
:canonical: agentsociety.agent.block.trigger_class

```{autodoc2-docstring} agentsociety.agent.block.trigger_class
```
````

`````{py:class} Block(name: str, llm: typing.Optional[agentsociety.llm.LLM] = None, environment: typing.Optional[agentsociety.environment.Environment] = None, memory: typing.Optional[agentsociety.memory.Memory] = None, trigger: typing.Optional[agentsociety.agent.trigger.EventTrigger] = None, description: str = '')
:canonical: agentsociety.agent.block.Block

```{autodoc2-docstring} agentsociety.agent.block.Block
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.agent.block.Block.__init__
```

````{py:attribute} configurable_fields
:canonical: agentsociety.agent.block.Block.configurable_fields
:type: list[str]
:value: >
   []

```{autodoc2-docstring} agentsociety.agent.block.Block.configurable_fields
```

````

````{py:attribute} default_values
:canonical: agentsociety.agent.block.Block.default_values
:type: dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.block.Block.default_values
```

````

````{py:attribute} fields_description
:canonical: agentsociety.agent.block.Block.fields_description
:type: dict[str, str]
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.block.Block.fields_description
```

````

````{py:method} export_config() -> dict[str, typing.Optional[str]]
:canonical: agentsociety.agent.block.Block.export_config

```{autodoc2-docstring} agentsociety.agent.block.Block.export_config
```

````

````{py:method} export_class_config() -> tuple[dict[str, typing.Any], dict[str, typing.Any]]
:canonical: agentsociety.agent.block.Block.export_class_config
:classmethod:

```{autodoc2-docstring} agentsociety.agent.block.Block.export_class_config
```

````

````{py:method} import_config(config: dict[str, typing.Union[str, dict]]) -> agentsociety.agent.block.Block
:canonical: agentsociety.agent.block.Block.import_config
:classmethod:

```{autodoc2-docstring} agentsociety.agent.block.Block.import_config
```

````

````{py:method} load_from_config(config: dict[str, list[dict]]) -> None
:canonical: agentsociety.agent.block.Block.load_from_config

```{autodoc2-docstring} agentsociety.agent.block.Block.load_from_config
```

````

````{py:method} forward(step, context)
:canonical: agentsociety.agent.block.Block.forward
:abstractmethod:
:async:

```{autodoc2-docstring} agentsociety.agent.block.Block.forward
```

````

````{py:property} llm
:canonical: agentsociety.agent.block.Block.llm
:type: agentsociety.llm.LLM

```{autodoc2-docstring} agentsociety.agent.block.Block.llm
```

````

````{py:property} memory
:canonical: agentsociety.agent.block.Block.memory
:type: agentsociety.memory.Memory

```{autodoc2-docstring} agentsociety.agent.block.Block.memory
```

````

````{py:property} environment
:canonical: agentsociety.agent.block.Block.environment
:type: agentsociety.environment.Environment

```{autodoc2-docstring} agentsociety.agent.block.Block.environment
```

````

`````
