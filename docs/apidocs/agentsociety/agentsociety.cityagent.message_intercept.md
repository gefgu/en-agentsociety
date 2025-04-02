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
* - {py:obj}`DoNothingListener <agentsociety.cityagent.message_intercept.DoNothingListener>`
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

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.cityagent.message_intercept.__all__>`
  - ```{autodoc2-docstring} agentsociety.cityagent.message_intercept.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.cityagent.message_intercept.__all__
:value: >
   ['EdgeMessageBlock', 'PointMessageBlock', 'DoNothingListener']

```{autodoc2-docstring} agentsociety.cityagent.message_intercept.__all__
```

````

````{py:function} check_message(from_id: int, to_id: int, llm_client: agentsociety.llm.LLM, content: str) -> bool
:canonical: agentsociety.cityagent.message_intercept.check_message
:async:

```{autodoc2-docstring} agentsociety.cityagent.message_intercept.check_message
```
````

`````{py:class} EdgeMessageBlock(name: str, max_violation_time: int)
:canonical: agentsociety.cityagent.message_intercept.EdgeMessageBlock

Bases: {py:obj}`agentsociety.message.MessageBlockBase`

````{py:method} forward(llm: agentsociety.llm.LLM, from_id: int, to_id: int, msg: str, violation_counts: dict[int, int], black_set: agentsociety.message.message_interceptor.BlackSet) -> tuple[bool, str]
:canonical: agentsociety.cityagent.message_intercept.EdgeMessageBlock.forward
:async:

````

`````

`````{py:class} PointMessageBlock(name: str, max_violation_time: int)
:canonical: agentsociety.cityagent.message_intercept.PointMessageBlock

Bases: {py:obj}`agentsociety.message.MessageBlockBase`

````{py:method} forward(llm: agentsociety.llm.LLM, from_id: int, to_id: int, msg: str, violation_counts: dict[int, int], black_set: agentsociety.message.message_interceptor.BlackSet) -> tuple[bool, str]
:canonical: agentsociety.cityagent.message_intercept.PointMessageBlock.forward
:async:

````

`````

`````{py:class} DoNothingListener(queue: ray.util.queue.Queue)
:canonical: agentsociety.cityagent.message_intercept.DoNothingListener

Bases: {py:obj}`agentsociety.message.MessageBlockListenerBase`

````{py:method} forward(msg: typing.Any)
:canonical: agentsociety.cityagent.message_intercept.DoNothingListener.forward
:async:

````

`````
