# {py:mod}`agentsociety.cityagent.governmentagent`

```{py:module} agentsociety.cityagent.governmentagent
```

```{autodoc2-docstring} agentsociety.cityagent.governmentagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`GovernmentAgent <agentsociety.cityagent.governmentagent.GovernmentAgent>`
  - ```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.cityagent.governmentagent.__all__>`
  - ```{autodoc2-docstring} agentsociety.cityagent.governmentagent.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.cityagent.governmentagent.__all__
:value: >
   ['GovernmentAgent']

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.__all__
```

````

`````{py:class} GovernmentAgent(id: int, name: str, toolbox: agentsociety.agent.AgentToolbox, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent

Bases: {py:obj}`agentsociety.agent.GovernmentAgentBase`

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.__init__
```

````{py:attribute} configurable_fields
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent.configurable_fields
:value: >
   ['time_diff']

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.configurable_fields
```

````

````{py:attribute} default_values
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent.default_values
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.default_values
```

````

````{py:attribute} fields_description
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent.fields_description
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.fields_description
```

````

````{py:method} reset()
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent.reset
:async:

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.reset
```

````

````{py:method} month_trigger()
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent.month_trigger
:async:

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.month_trigger
```

````

````{py:method} gather_messages(agent_ids, content)
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent.gather_messages
:async:

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.gather_messages
```

````

````{py:method} forward()
:canonical: agentsociety.cityagent.governmentagent.GovernmentAgent.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.governmentagent.GovernmentAgent.forward
```

````

`````
