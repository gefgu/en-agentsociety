# {py:mod}`en_agentsociety.cityagent.firmagent`

```{py:module} en_agentsociety.cityagent.firmagent
```

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`FirmAgentConfig <en_agentsociety.cityagent.firmagent.FirmAgentConfig>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgentConfig
    :summary:
    ```
* - {py:obj}`FirmAgent <en_agentsociety.cityagent.firmagent.FirmAgent>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.cityagent.firmagent.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.cityagent.firmagent.__all__
:value: >
   ['FirmAgent']

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.__all__
```

````

`````{py:class} FirmAgentConfig(/, **data: typing.Any)
:canonical: en_agentsociety.cityagent.firmagent.FirmAgentConfig

Bases: {py:obj}`en_agentsociety.agent.AgentParams`

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgentConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgentConfig.__init__
```

````{py:attribute} time_diff
:canonical: en_agentsociety.cityagent.firmagent.FirmAgentConfig.time_diff
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgentConfig.time_diff
```

````

````{py:attribute} max_price_inflation
:canonical: en_agentsociety.cityagent.firmagent.FirmAgentConfig.max_price_inflation
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgentConfig.max_price_inflation
```

````

````{py:attribute} max_wage_inflation
:canonical: en_agentsociety.cityagent.firmagent.FirmAgentConfig.max_wage_inflation
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgentConfig.max_wage_inflation
```

````

`````

`````{py:class} FirmAgent(id: int, name: str, toolbox: en_agentsociety.agent.AgentToolbox, memory: en_agentsociety.memory.Memory, agent_params: typing.Optional[en_agentsociety.cityagent.firmagent.FirmAgentConfig] = None, blocks: typing.Optional[list[en_agentsociety.agent.Block]] = None)
:canonical: en_agentsociety.cityagent.firmagent.FirmAgent

Bases: {py:obj}`en_agentsociety.agent.FirmAgentBase`

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent.__init__
```

````{py:attribute} ParamsType
:canonical: en_agentsociety.cityagent.firmagent.FirmAgent.ParamsType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent.ParamsType
```

````

````{py:attribute} description
:canonical: en_agentsociety.cityagent.firmagent.FirmAgent.description
:type: str
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent.description
```

````

````{py:method} reset()
:canonical: en_agentsociety.cityagent.firmagent.FirmAgent.reset
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent.reset
```

````

````{py:method} month_trigger()
:canonical: en_agentsociety.cityagent.firmagent.FirmAgent.month_trigger
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent.month_trigger
```

````

````{py:method} forward()
:canonical: en_agentsociety.cityagent.firmagent.FirmAgent.forward
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.firmagent.FirmAgent.forward
```

````

`````
