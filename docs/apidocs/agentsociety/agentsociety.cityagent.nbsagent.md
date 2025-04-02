# {py:mod}`agentsociety.cityagent.nbsagent`

```{py:module} agentsociety.cityagent.nbsagent
```

```{autodoc2-docstring} agentsociety.cityagent.nbsagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`NBSAgent <agentsociety.cityagent.nbsagent.NBSAgent>`
  - ```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.cityagent.nbsagent.__all__>`
  - ```{autodoc2-docstring} agentsociety.cityagent.nbsagent.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.cityagent.nbsagent.__all__
:value: >
   ['NBSAgent']

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.__all__
```

````

`````{py:class} NBSAgent(id: int, name: str, toolbox: agentsociety.agent.AgentToolbox, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.nbsagent.NBSAgent

Bases: {py:obj}`agentsociety.agent.NBSAgentBase`

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent.__init__
```

````{py:attribute} configurable_fields
:canonical: agentsociety.cityagent.nbsagent.NBSAgent.configurable_fields
:value: >
   ['time_diff', 'num_labor_hours', 'productivity_per_labor']

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent.configurable_fields
```

````

````{py:attribute} default_values
:canonical: agentsociety.cityagent.nbsagent.NBSAgent.default_values
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent.default_values
```

````

````{py:attribute} fields_description
:canonical: agentsociety.cityagent.nbsagent.NBSAgent.fields_description
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent.fields_description
```

````

````{py:method} month_trigger()
:canonical: agentsociety.cityagent.nbsagent.NBSAgent.month_trigger
:async:

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent.month_trigger
```

````

````{py:method} gather_messages(agent_ids, content)
:canonical: agentsociety.cityagent.nbsagent.NBSAgent.gather_messages
:async:

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent.gather_messages
```

````

````{py:method} forward()
:canonical: agentsociety.cityagent.nbsagent.NBSAgent.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.nbsagent.NBSAgent.forward
```

````

`````
