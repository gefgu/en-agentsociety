# {py:mod}`agentsociety.cityagent.firmagent`

```{py:module} agentsociety.cityagent.firmagent
```

```{autodoc2-docstring} agentsociety.cityagent.firmagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`FirmAgent <agentsociety.cityagent.firmagent.FirmAgent>`
  - ```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.cityagent.firmagent.__all__>`
  - ```{autodoc2-docstring} agentsociety.cityagent.firmagent.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.cityagent.firmagent.__all__
:value: >
   ['FirmAgent']

```{autodoc2-docstring} agentsociety.cityagent.firmagent.__all__
```

````

`````{py:class} FirmAgent(id: int, name: str, toolbox: agentsociety.agent.AgentToolbox, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.firmagent.FirmAgent

Bases: {py:obj}`agentsociety.agent.FirmAgentBase`

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent.__init__
```

````{py:attribute} configurable_fields
:canonical: agentsociety.cityagent.firmagent.FirmAgent.configurable_fields
:value: >
   ['time_diff', 'max_price_inflation', 'max_wage_inflation']

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent.configurable_fields
```

````

````{py:attribute} default_values
:canonical: agentsociety.cityagent.firmagent.FirmAgent.default_values
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent.default_values
```

````

````{py:attribute} fields_description
:canonical: agentsociety.cityagent.firmagent.FirmAgent.fields_description
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent.fields_description
```

````

````{py:method} month_trigger()
:canonical: agentsociety.cityagent.firmagent.FirmAgent.month_trigger
:async:

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent.month_trigger
```

````

````{py:method} gather_messages(agent_ids, content)
:canonical: agentsociety.cityagent.firmagent.FirmAgent.gather_messages
:async:

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent.gather_messages
```

````

````{py:method} forward()
:canonical: agentsociety.cityagent.firmagent.FirmAgent.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.firmagent.FirmAgent.forward
```

````

`````
