# {py:mod}`en_agentsociety.cityagent.nbsagent`

```{py:module} en_agentsociety.cityagent.nbsagent
```

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`NBSAgentConfig <en_agentsociety.cityagent.nbsagent.NBSAgentConfig>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgentConfig
    :summary:
    ```
* - {py:obj}`NBSAgent <en_agentsociety.cityagent.nbsagent.NBSAgent>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.cityagent.nbsagent.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.cityagent.nbsagent.__all__
:value: >
   ['NBSAgent']

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.__all__
```

````

`````{py:class} NBSAgentConfig(/, **data: typing.Any)
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgentConfig

Bases: {py:obj}`en_agentsociety.agent.AgentParams`

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgentConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgentConfig.__init__
```

````{py:attribute} time_diff
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgentConfig.time_diff
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgentConfig.time_diff
```

````

````{py:attribute} num_labor_hours
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgentConfig.num_labor_hours
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgentConfig.num_labor_hours
```

````

````{py:attribute} productivity_per_labor
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgentConfig.productivity_per_labor
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgentConfig.productivity_per_labor
```

````

`````

`````{py:class} NBSAgent(id: int, name: str, toolbox: en_agentsociety.agent.AgentToolbox, memory: en_agentsociety.memory.Memory, agent_params: typing.Optional[en_agentsociety.cityagent.nbsagent.NBSAgentConfig] = None, blocks: typing.Optional[list[en_agentsociety.agent.block.Block]] = None)
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgent

Bases: {py:obj}`en_agentsociety.agent.NBSAgentBase`

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent.__init__
```

````{py:attribute} ParamsType
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgent.ParamsType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent.ParamsType
```

````

````{py:attribute} description
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgent.description
:type: str
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent.description
```

````

````{py:method} reset()
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgent.reset
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent.reset
```

````

````{py:method} month_trigger()
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgent.month_trigger
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent.month_trigger
```

````

````{py:method} forward()
:canonical: en_agentsociety.cityagent.nbsagent.NBSAgent.forward
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.nbsagent.NBSAgent.forward
```

````

`````
