# {py:mod}`agentsociety.cityagent.bankagent`

```{py:module} agentsociety.cityagent.bankagent
```

```{autodoc2-docstring} agentsociety.cityagent.bankagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`BankAgent <agentsociety.cityagent.bankagent.BankAgent>`
  - ```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`calculate_inflation <agentsociety.cityagent.bankagent.calculate_inflation>`
  - ```{autodoc2-docstring} agentsociety.cityagent.bankagent.calculate_inflation
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.cityagent.bankagent.__all__>`
  - ```{autodoc2-docstring} agentsociety.cityagent.bankagent.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.cityagent.bankagent.__all__
:value: >
   ['BankAgent']

```{autodoc2-docstring} agentsociety.cityagent.bankagent.__all__
```

````

````{py:function} calculate_inflation(prices)
:canonical: agentsociety.cityagent.bankagent.calculate_inflation

```{autodoc2-docstring} agentsociety.cityagent.bankagent.calculate_inflation
```
````

`````{py:class} BankAgent(id: int, name: str, toolbox: agentsociety.agent.AgentToolbox, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.bankagent.BankAgent

Bases: {py:obj}`agentsociety.agent.BankAgentBase`

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent.__init__
```

````{py:attribute} configurable_fields
:canonical: agentsociety.cityagent.bankagent.BankAgent.configurable_fields
:value: >
   ['time_diff']

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent.configurable_fields
```

````

````{py:attribute} default_values
:canonical: agentsociety.cityagent.bankagent.BankAgent.default_values
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent.default_values
```

````

````{py:attribute} fields_description
:canonical: agentsociety.cityagent.bankagent.BankAgent.fields_description
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent.fields_description
```

````

````{py:method} month_trigger()
:canonical: agentsociety.cityagent.bankagent.BankAgent.month_trigger
:async:

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent.month_trigger
```

````

````{py:method} gather_messages(agent_ids, content)
:canonical: agentsociety.cityagent.bankagent.BankAgent.gather_messages
:async:

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent.gather_messages
```

````

````{py:method} forward()
:canonical: agentsociety.cityagent.bankagent.BankAgent.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.bankagent.BankAgent.forward
```

````

`````
