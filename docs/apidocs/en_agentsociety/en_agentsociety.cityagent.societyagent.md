# {py:mod}`en_agentsociety.cityagent.societyagent`

```{py:module} en_agentsociety.cityagent.societyagent
```

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SocietyAgent <en_agentsociety.cityagent.societyagent.SocietyAgent>`
  -
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ENVIRONMENT_REFLECTION_PROMPT <en_agentsociety.cityagent.societyagent.ENVIRONMENT_REFLECTION_PROMPT>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.ENVIRONMENT_REFLECTION_PROMPT
    :summary:
    ```
````

### API

````{py:data} ENVIRONMENT_REFLECTION_PROMPT
:canonical: en_agentsociety.cityagent.societyagent.ENVIRONMENT_REFLECTION_PROMPT
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.ENVIRONMENT_REFLECTION_PROMPT
```

````

`````{py:class} SocietyAgent(id: int, name: str, toolbox: en_agentsociety.agent.AgentToolbox, memory: en_agentsociety.memory.Memory, agent_params: typing.Optional[en_agentsociety.cityagent.sharing_params.SocietyAgentConfig] = None, blocks: typing.Optional[list[en_agentsociety.agent.Block]] = None)
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent

Bases: {py:obj}`en_agentsociety.agent.CitizenAgentBase`

````{py:attribute} ParamsType
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.ParamsType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.ParamsType
```

````

````{py:attribute} BlockOutputType
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.BlockOutputType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.BlockOutputType
```

````

````{py:attribute} Context
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.Context
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.Context
```

````

````{py:attribute} StatusAttributes
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.StatusAttributes
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.StatusAttributes
```

````

````{py:attribute} description
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.description
:type: str
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.description
```

````

````{py:method} status_summary()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.status_summary
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.status_summary
```

````

````{py:method} before_forward()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.before_forward
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.before_forward
```

````

````{py:method} reset()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.reset
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.reset
```

````

````{py:method} plan_generation()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.plan_generation
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.plan_generation
```

````

````{py:method} reflect_to_environment()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.reflect_to_environment
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.reflect_to_environment
```

````

````{py:method} forward()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.forward
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.forward
```

````

````{py:method} check_and_update_step()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.check_and_update_step
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.check_and_update_step
```

````

````{py:method} do_chat(message: en_agentsociety.message.Message) -> str
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.do_chat
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.do_chat
```

````

````{py:method} react_to_intervention(intervention_message: str)
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.react_to_intervention
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.react_to_intervention
```

````

````{py:method} reset_position()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.reset_position
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.reset_position
```

````

````{py:method} step_execution()
:canonical: en_agentsociety.cityagent.societyagent.SocietyAgent.step_execution
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.societyagent.SocietyAgent.step_execution
```

````

`````
