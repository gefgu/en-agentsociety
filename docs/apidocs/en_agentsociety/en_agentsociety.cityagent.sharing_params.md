# {py:mod}`en_agentsociety.cityagent.sharing_params`

```{py:module} en_agentsociety.cityagent.sharing_params
```

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SocietyAgentConfig <en_agentsociety.cityagent.sharing_params.SocietyAgentConfig>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig
    :summary:
    ```
* - {py:obj}`SocietyAgentBlockOutput <en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput>`
  -
* - {py:obj}`SocietyAgentContext <en_agentsociety.cityagent.sharing_params.SocietyAgentContext>`
  -
````

### API

`````{py:class} SocietyAgentConfig(/, **data: typing.Any)
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentConfig

Bases: {py:obj}`en_agentsociety.agent.AgentParams`

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.__init__
```

````{py:attribute} block_dispatch_prompt
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.block_dispatch_prompt
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.block_dispatch_prompt
```

````

````{py:attribute} enable_cognition
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.enable_cognition
:type: bool
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.enable_cognition
```

````

````{py:attribute} need_initialization_prompt
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.need_initialization_prompt
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.need_initialization_prompt
```

````

````{py:attribute} max_plan_steps
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.max_plan_steps
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.max_plan_steps
```

````

````{py:attribute} plan_generation_prompt
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.plan_generation_prompt
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentConfig.plan_generation_prompt
```

````

`````

`````{py:class} SocietyAgentBlockOutput(/, **data: typing.Any)
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput

Bases: {py:obj}`en_agentsociety.agent.BlockOutput`

````{py:attribute} success
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.success
:type: bool
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.success
```

````

````{py:attribute} evaluation
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.evaluation
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.evaluation
```

````

````{py:attribute} consumed_time
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.consumed_time
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.consumed_time
```

````

````{py:attribute} node_id
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.node_id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentBlockOutput.node_id
```

````

`````

`````{py:class} SocietyAgentContext(/, **data: typing.Any)
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext

Bases: {py:obj}`en_agentsociety.agent.AgentContext`

````{py:attribute} current_time
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_time
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_time
```

````

````{py:attribute} current_need
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_need
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_need
```

````

````{py:attribute} current_intention
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_intention
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_intention
```

````

````{py:attribute} current_emotion
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_emotion
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_emotion
```

````

````{py:attribute} current_thought
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_thought
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_thought
```

````

````{py:attribute} current_location
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_location
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_location
```

````

````{py:attribute} area_information
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.area_information
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.area_information
```

````

````{py:attribute} weather
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.weather
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.weather
```

````

````{py:attribute} temperature
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.temperature
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.temperature
```

````

````{py:attribute} other_information
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.other_information
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.other_information
```

````

````{py:attribute} plan_target
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.plan_target
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.plan_target
```

````

````{py:attribute} max_plan_steps
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.max_plan_steps
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.max_plan_steps
```

````

````{py:attribute} current_step
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_step
:type: dict
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.current_step
```

````

````{py:attribute} plan_context
:canonical: en_agentsociety.cityagent.sharing_params.SocietyAgentContext.plan_context
:type: dict
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.sharing_params.SocietyAgentContext.plan_context
```

````

`````
