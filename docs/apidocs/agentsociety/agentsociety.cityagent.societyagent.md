# {py:mod}`agentsociety.cityagent.societyagent`

```{py:module} agentsociety.cityagent.societyagent
```

```{autodoc2-docstring} agentsociety.cityagent.societyagent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`PlanAndActionBlock <agentsociety.cityagent.societyagent.PlanAndActionBlock>`
  - ```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock
    :summary:
    ```
* - {py:obj}`MindBlock <agentsociety.cityagent.societyagent.MindBlock>`
  - ```{autodoc2-docstring} agentsociety.cityagent.societyagent.MindBlock
    :summary:
    ```
* - {py:obj}`SocietyAgent <agentsociety.cityagent.societyagent.SocietyAgent>`
  - ```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent
    :summary:
    ```
````

### API

`````{py:class} PlanAndActionBlock(agent: agentsociety.agent.Agent, llm: agentsociety.llm.LLM, environment: agentsociety.environment.Environment, memory: agentsociety.memory.Memory, enable_mobility: bool = True, enable_social: bool = True, enable_economy: bool = True, enable_cognition: bool = True)
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock

Bases: {py:obj}`agentsociety.agent.Block`

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.__init__
```

````{py:attribute} month_plan_block
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.month_plan_block
:type: agentsociety.cityagent.blocks.economy_block.MonthPlanBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.month_plan_block
```

````

````{py:attribute} needs_block
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.needs_block
:type: agentsociety.cityagent.blocks.NeedsBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.needs_block
```

````

````{py:attribute} plan_block
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.plan_block
:type: agentsociety.cityagent.blocks.PlanBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.plan_block
```

````

````{py:attribute} mobility_block
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.mobility_block
:type: agentsociety.cityagent.blocks.MobilityBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.mobility_block
```

````

````{py:attribute} social_block
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.social_block
:type: agentsociety.cityagent.blocks.SocialBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.social_block
```

````

````{py:attribute} economy_block
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.economy_block
:type: agentsociety.cityagent.blocks.EconomyBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.economy_block
```

````

````{py:attribute} other_block
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.other_block
:type: agentsociety.cityagent.blocks.OtherBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.other_block
```

````

````{py:method} plan_generation()
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.plan_generation
:async:

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.plan_generation
```

````

````{py:method} step_execution()
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.step_execution
:async:

```{autodoc2-docstring} agentsociety.cityagent.societyagent.PlanAndActionBlock.step_execution
```

````

````{py:method} forward()
:canonical: agentsociety.cityagent.societyagent.PlanAndActionBlock.forward
:async:

````

`````

`````{py:class} MindBlock(llm: agentsociety.llm.LLM, environment: agentsociety.environment.Environment, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.societyagent.MindBlock

Bases: {py:obj}`agentsociety.agent.Block`

```{autodoc2-docstring} agentsociety.cityagent.societyagent.MindBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.societyagent.MindBlock.__init__
```

````{py:attribute} cognition_block
:canonical: agentsociety.cityagent.societyagent.MindBlock.cognition_block
:type: agentsociety.cityagent.blocks.CognitionBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.MindBlock.cognition_block
```

````

````{py:method} forward()
:canonical: agentsociety.cityagent.societyagent.MindBlock.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.societyagent.MindBlock.forward
```

````

`````

`````{py:class} SocietyAgent(id: int, name: str, toolbox: agentsociety.agent.AgentToolbox, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.societyagent.SocietyAgent

Bases: {py:obj}`agentsociety.agent.CitizenAgentBase`

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.__init__
```

````{py:attribute} update_with_sim
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.update_with_sim
:value: >
   'UpdateWithSimulator(...)'

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.update_with_sim
```

````

````{py:attribute} mind_block
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.mind_block
:type: agentsociety.cityagent.societyagent.MindBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.mind_block
```

````

````{py:attribute} plan_and_action_block
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.plan_and_action_block
:type: agentsociety.cityagent.societyagent.PlanAndActionBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.plan_and_action_block
```

````

````{py:attribute} configurable_fields
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.configurable_fields
:value: >
   ['enable_cognition', 'enable_mobility', 'enable_social', 'enable_economy']

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.configurable_fields
```

````

````{py:attribute} default_values
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.default_values
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.default_values
```

````

````{py:attribute} fields_description
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.fields_description
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.fields_description
```

````

````{py:method} forward()
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.forward
```

````

````{py:method} check_and_update_step()
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.check_and_update_step
:async:

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.check_and_update_step
```

````

````{py:method} process_agent_chat_response(payload: dict) -> str
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.process_agent_chat_response
:async:

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.process_agent_chat_response
```

````

````{py:method} react_to_intervention(intervention_message: str)
:canonical: agentsociety.cityagent.societyagent.SocietyAgent.react_to_intervention
:async:

```{autodoc2-docstring} agentsociety.cityagent.societyagent.SocietyAgent.react_to_intervention
```

````

`````
