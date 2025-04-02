# {py:mod}`agentsociety.cityagent.blocks.other_block`

```{py:module} agentsociety.cityagent.blocks.other_block
```

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SleepBlock <agentsociety.cityagent.blocks.other_block.SleepBlock>`
  - ```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.SleepBlock
    :summary:
    ```
* - {py:obj}`OtherNoneBlock <agentsociety.cityagent.blocks.other_block.OtherNoneBlock>`
  - ```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherNoneBlock
    :summary:
    ```
* - {py:obj}`OtherBlock <agentsociety.cityagent.blocks.other_block.OtherBlock>`
  - ```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherBlock
    :summary:
    ```
````

### API

`````{py:class} SleepBlock(llm: agentsociety.llm.LLM, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.blocks.other_block.SleepBlock

Bases: {py:obj}`agentsociety.agent.Block`

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.SleepBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.SleepBlock.__init__
```

````{py:method} forward(step, context)
:canonical: agentsociety.cityagent.blocks.other_block.SleepBlock.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.SleepBlock.forward
```

````

`````

`````{py:class} OtherNoneBlock(llm: agentsociety.llm.LLM, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.blocks.other_block.OtherNoneBlock

Bases: {py:obj}`agentsociety.agent.Block`

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherNoneBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherNoneBlock.__init__
```

````{py:method} forward(step, context)
:canonical: agentsociety.cityagent.blocks.other_block.OtherNoneBlock.forward
:async:

````

`````

`````{py:class} OtherBlock(llm: agentsociety.llm.LLM, memory: agentsociety.memory.Memory)
:canonical: agentsociety.cityagent.blocks.other_block.OtherBlock

Bases: {py:obj}`agentsociety.agent.Block`

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherBlock.__init__
```

````{py:attribute} sleep_block
:canonical: agentsociety.cityagent.blocks.other_block.OtherBlock.sleep_block
:type: agentsociety.cityagent.blocks.other_block.SleepBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherBlock.sleep_block
```

````

````{py:attribute} other_none_block
:canonical: agentsociety.cityagent.blocks.other_block.OtherBlock.other_none_block
:type: agentsociety.cityagent.blocks.other_block.OtherNoneBlock
:value: >
   None

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherBlock.other_none_block
```

````

````{py:method} forward(step, context)
:canonical: agentsociety.cityagent.blocks.other_block.OtherBlock.forward
:async:

```{autodoc2-docstring} agentsociety.cityagent.blocks.other_block.OtherBlock.forward
```

````

`````
