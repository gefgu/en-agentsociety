# {py:mod}`en_agentsociety.cityagent.governmentagent`

```{py:module} en_agentsociety.cityagent.governmentagent
```

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`GovernmentAgentConfig <en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig
    :summary:
    ```
* - {py:obj}`GovernmentAgent <en_agentsociety.cityagent.governmentagent.GovernmentAgent>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.cityagent.governmentagent.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.cityagent.governmentagent.__all__
:value: >
   ['GovernmentAgent']

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.__all__
```

````

`````{py:class} GovernmentAgentConfig(/, **data: typing.Any)
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig

Bases: {py:obj}`en_agentsociety.agent.AgentParams`

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig.__init__
```

````{py:attribute} time_diff
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig.time_diff
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig.time_diff
```

````

`````

`````{py:class} GovernmentAgent(id: int, name: str, toolbox: en_agentsociety.agent.AgentToolbox, memory: en_agentsociety.memory.Memory, agent_params: typing.Optional[en_agentsociety.cityagent.governmentagent.GovernmentAgentConfig] = None, blocks: typing.Optional[list[en_agentsociety.agent.Block]] = None)
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgent

Bases: {py:obj}`en_agentsociety.agent.GovernmentAgentBase`

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent.__init__
```

````{py:attribute} ParamsType
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgent.ParamsType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent.ParamsType
```

````

````{py:attribute} description
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgent.description
:type: str
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent.description
```

````

````{py:method} reset()
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgent.reset
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent.reset
```

````

````{py:method} month_trigger()
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgent.month_trigger
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent.month_trigger
```

````

````{py:method} forward()
:canonical: en_agentsociety.cityagent.governmentagent.GovernmentAgent.forward
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.governmentagent.GovernmentAgent.forward
```

````

`````
