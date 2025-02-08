# {py:mod}`agentsociety.cityagent.message_intercept`

```{py:module} agentsociety.cityagent.message_intercept
```

```{autodoc2-docstring} agentsociety.cityagent.message_intercept
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`EdgeMessageBlock <agentsociety.cityagent.message_intercept.EdgeMessageBlock>`
  -
* - {py:obj}`PointMessageBlock <agentsociety.cityagent.message_intercept.PointMessageBlock>`
  -
* - {py:obj}`MessageBlockListener <agentsociety.cityagent.message_intercept.MessageBlockListener>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`check_message <agentsociety.cityagent.message_intercept.check_message>`
  - ```{autodoc2-docstring} agentsociety.cityagent.message_intercept.check_message
    :summary:
    ```
````

### API

````{py:function} check_message(from_uuid: str, to_uuid: str, llm_client: agentsociety.llm.LLM, content: str) -> bool
:canonical: agentsociety.cityagent.message_intercept.check_message
:async:

```{autodoc2-docstring} agentsociety.cityagent.message_intercept.check_message
```
````

`````{py:class} EdgeMessageBlock(name: str = '', max_violation_time: int = 3)
:canonical: agentsociety.cityagent.message_intercept.EdgeMessageBlock

Bases: {py:obj}`agentsociety.message.MessageBlockBase`

````{py:method} forward(from_uuid: str, to_uuid: str, msg: str, violation_counts: dict[str, int], black_list: list[tuple[str, str]])
:canonical: agentsociety.cityagent.message_intercept.EdgeMessageBlock.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.message_intercept.EdgeMessageBlock.forward
```

````

`````

`````{py:class} PointMessageBlock(name: str = '', max_violation_time: int = 3)
:canonical: agentsociety.cityagent.message_intercept.PointMessageBlock

Bases: {py:obj}`agentsociety.message.MessageBlockBase`

````{py:method} forward(from_uuid: str, to_uuid: str, msg: str, violation_counts: dict[str, int], black_list: list[tuple[str, str]])
:canonical: agentsociety.cityagent.message_intercept.PointMessageBlock.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.message_intercept.PointMessageBlock.forward
```

````

`````

`````{py:class} MessageBlockListener(save_queue_values: bool = False, get_queue_period: float = 0.1)
:canonical: agentsociety.cityagent.message_intercept.MessageBlockListener

Bases: {py:obj}`agentsociety.message.MessageBlockListenerBase`

````{py:method} forward()
:canonical: agentsociety.cityagent.message_intercept.MessageBlockListener.forward
:async:

````

`````
