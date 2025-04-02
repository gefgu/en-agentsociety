# {py:mod}`agentsociety.agent.trigger`

```{py:module} agentsociety.agent.trigger
```

```{autodoc2-docstring} agentsociety.agent.trigger
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`EventTrigger <agentsociety.agent.trigger.EventTrigger>`
  - ```{autodoc2-docstring} agentsociety.agent.trigger.EventTrigger
    :summary:
    ```
* - {py:obj}`MemoryChangeTrigger <agentsociety.agent.trigger.MemoryChangeTrigger>`
  - ```{autodoc2-docstring} agentsociety.agent.trigger.MemoryChangeTrigger
    :summary:
    ```
* - {py:obj}`TimeTrigger <agentsociety.agent.trigger.TimeTrigger>`
  - ```{autodoc2-docstring} agentsociety.agent.trigger.TimeTrigger
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`KEY_TRIGGER_COMPONENTS <agentsociety.agent.trigger.KEY_TRIGGER_COMPONENTS>`
  - ```{autodoc2-docstring} agentsociety.agent.trigger.KEY_TRIGGER_COMPONENTS
    :summary:
    ```
* - {py:obj}`__all__ <agentsociety.agent.trigger.__all__>`
  - ```{autodoc2-docstring} agentsociety.agent.trigger.__all__
    :summary:
    ```
````

### API

````{py:data} KEY_TRIGGER_COMPONENTS
:canonical: agentsociety.agent.trigger.KEY_TRIGGER_COMPONENTS
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.trigger.KEY_TRIGGER_COMPONENTS
```

````

````{py:data} __all__
:canonical: agentsociety.agent.trigger.__all__
:value: >
   ['EventTrigger', 'MemoryChangeTrigger', 'TimeTrigger']

```{autodoc2-docstring} agentsociety.agent.trigger.__all__
```

````

`````{py:class} EventTrigger(block=None)
:canonical: agentsociety.agent.trigger.EventTrigger

```{autodoc2-docstring} agentsociety.agent.trigger.EventTrigger
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.agent.trigger.EventTrigger.__init__
```

````{py:attribute} required_components
:canonical: agentsociety.agent.trigger.EventTrigger.required_components
:type: list[type]
:value: >
   []

```{autodoc2-docstring} agentsociety.agent.trigger.EventTrigger.required_components
```

````

````{py:method} initialize() -> None
:canonical: agentsociety.agent.trigger.EventTrigger.initialize

```{autodoc2-docstring} agentsociety.agent.trigger.EventTrigger.initialize
```

````

````{py:method} wait_for_trigger() -> None
:canonical: agentsociety.agent.trigger.EventTrigger.wait_for_trigger
:abstractmethod:
:async:

```{autodoc2-docstring} agentsociety.agent.trigger.EventTrigger.wait_for_trigger
```

````

`````

`````{py:class} MemoryChangeTrigger(key: str)
:canonical: agentsociety.agent.trigger.MemoryChangeTrigger

Bases: {py:obj}`agentsociety.agent.trigger.EventTrigger`

```{autodoc2-docstring} agentsociety.agent.trigger.MemoryChangeTrigger
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.agent.trigger.MemoryChangeTrigger.__init__
```

````{py:attribute} required_components
:canonical: agentsociety.agent.trigger.MemoryChangeTrigger.required_components
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.trigger.MemoryChangeTrigger.required_components
```

````

````{py:method} initialize() -> None
:canonical: agentsociety.agent.trigger.MemoryChangeTrigger.initialize

```{autodoc2-docstring} agentsociety.agent.trigger.MemoryChangeTrigger.initialize
```

````

````{py:method} wait_for_trigger() -> None
:canonical: agentsociety.agent.trigger.MemoryChangeTrigger.wait_for_trigger
:async:

```{autodoc2-docstring} agentsociety.agent.trigger.MemoryChangeTrigger.wait_for_trigger
```

````

`````

`````{py:class} TimeTrigger(days: typing.Optional[int] = None, hours: typing.Optional[int] = None, minutes: typing.Optional[int] = None)
:canonical: agentsociety.agent.trigger.TimeTrigger

Bases: {py:obj}`agentsociety.agent.trigger.EventTrigger`

```{autodoc2-docstring} agentsociety.agent.trigger.TimeTrigger
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.agent.trigger.TimeTrigger.__init__
```

````{py:attribute} required_components
:canonical: agentsociety.agent.trigger.TimeTrigger.required_components
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.trigger.TimeTrigger.required_components
```

````

````{py:method} initialize() -> None
:canonical: agentsociety.agent.trigger.TimeTrigger.initialize

```{autodoc2-docstring} agentsociety.agent.trigger.TimeTrigger.initialize
```

````

````{py:method} _monitor_time()
:canonical: agentsociety.agent.trigger.TimeTrigger._monitor_time
:async:

```{autodoc2-docstring} agentsociety.agent.trigger.TimeTrigger._monitor_time
```

````

````{py:method} wait_for_trigger() -> None
:canonical: agentsociety.agent.trigger.TimeTrigger.wait_for_trigger
:async:

```{autodoc2-docstring} agentsociety.agent.trigger.TimeTrigger.wait_for_trigger
```

````

`````
