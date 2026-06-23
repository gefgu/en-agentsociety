# {py:mod}`en_agentsociety.cityagent.blocks.cognition_block`

```{py:module} en_agentsociety.cityagent.blocks.cognition_block
```

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`CognitionBlockParams <en_agentsociety.cityagent.blocks.cognition_block.CognitionBlockParams>`
  -
* - {py:obj}`CognitionBlock <en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`extract_json <en_agentsociety.cityagent.blocks.cognition_block.extract_json>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.extract_json
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.cityagent.blocks.cognition_block.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.cityagent.blocks.cognition_block.__all__
:value: >
   ['CognitionBlock']

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.__all__
```

````

````{py:function} extract_json(output_str)
:canonical: en_agentsociety.cityagent.blocks.cognition_block.extract_json

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.extract_json
```
````

`````{py:class} CognitionBlockParams(/, **data: typing.Any)
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlockParams

Bases: {py:obj}`en_agentsociety.agent.BlockParams`

````{py:attribute} top_k
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlockParams.top_k
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlockParams.top_k
```

````

`````

`````{py:class} CognitionBlock(toolbox: en_agentsociety.agent.AgentToolbox, agent_memory: en_agentsociety.memory.Memory, block_params: typing.Optional[en_agentsociety.cityagent.blocks.cognition_block.CognitionBlockParams] = None)
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock

Bases: {py:obj}`en_agentsociety.agent.Block`

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.__init__
```

````{py:attribute} ParamsType
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.ParamsType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.ParamsType
```

````

````{py:attribute} name
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.name
:value: >
   'CognitionBlock'

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.name
```

````

````{py:attribute} description
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.description
:value: >
   'Handles daily updates of attitudes, thoughts, and emotions'

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.description
```

````

````{py:attribute} actions
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.actions
:value: >
   None

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.actions
```

````

````{py:method} set_status(status)
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.set_status
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.set_status
```

````

````{py:method} attitude_update()
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.attitude_update
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.attitude_update
```

````

````{py:method} thought_update()
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.thought_update
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.thought_update
```

````

````{py:method} cross_day()
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.cross_day
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.cross_day
```

````

````{py:method} forward()
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.forward
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.forward
```

````

````{py:method} emotion_update(incident)
:canonical: en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.emotion_update
:async:

```{autodoc2-docstring} en_agentsociety.cityagent.blocks.cognition_block.CognitionBlock.emotion_update
```

````

`````
