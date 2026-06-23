# {py:mod}`en_agentsociety.cityagent.blocks.needs_block`

```{py:module} en_agentsociety.cityagent.blocks.needs_block
```

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`NeedsBlock <en_agentsociety.cityagent.blocks.needs_block.NeedsBlock>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`INITIAL_NEEDS_PROMPT <en_agentsociety.cityagent.blocks.needs_block.INITIAL_NEEDS_PROMPT>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.INITIAL_NEEDS_PROMPT
    :summary:
    ```
* - {py:obj}`EVALUATION_PROMPT <en_agentsociety.cityagent.blocks.needs_block.EVALUATION_PROMPT>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.EVALUATION_PROMPT
    :summary:
    ```
* - {py:obj}`REFLECTION_PROMPT <en_agentsociety.cityagent.blocks.needs_block.REFLECTION_PROMPT>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.REFLECTION_PROMPT
    :summary:
    ```
````

### API

````{py:data} INITIAL_NEEDS_PROMPT
:canonical: en_agentsociety.cityagent.blocks.needs_block.INITIAL_NEEDS_PROMPT
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.INITIAL_NEEDS_PROMPT
```

````

````{py:data} EVALUATION_PROMPT
:canonical: en_agentsociety.cityagent.blocks.needs_block.EVALUATION_PROMPT
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.EVALUATION_PROMPT
```

````

````{py:data} REFLECTION_PROMPT
:canonical: en_agentsociety.cityagent.blocks.needs_block.REFLECTION_PROMPT
:value: <Multiline-String>

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.REFLECTION_PROMPT
```

````

`````{py:class} NeedsBlock(toolbox: en_agentsociety.agent.AgentToolbox, agent_memory: en_agentsociety.memory.Memory, agent_context: en_agentsociety.agent.DotDict, evaluation_prompt: str = EVALUATION_PROMPT, reflection_prompt: str = REFLECTION_PROMPT, initial_prompt: str = INITIAL_NEEDS_PROMPT)
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock

Bases: {py:obj}`en_agentsociety.agent.Block`

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.__init__
```

````{py:method} reset()
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.reset
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.reset
```

````

````{py:method} initialize()
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.initialize
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.initialize
```

````

````{py:method} reflect_to_intervention(intervention: str)
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.reflect_to_intervention
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.reflect_to_intervention
```

````

````{py:method} time_decay()
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.time_decay
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.time_decay
```

````

````{py:method} update_when_plan_completed()
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.update_when_plan_completed
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.update_when_plan_completed
```

````

````{py:method} determine_current_need()
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.determine_current_need
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.determine_current_need
```

````

````{py:method} evaluate_and_adjust_needs(completed_plan)
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.evaluate_and_adjust_needs
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.evaluate_and_adjust_needs
```

````

````{py:method} forward()
:canonical: en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.forward
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.needs_block.NeedsBlock.forward
```

````

`````
