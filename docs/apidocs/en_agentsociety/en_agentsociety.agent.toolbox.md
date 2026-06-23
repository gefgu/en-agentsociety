# {py:mod}`en_agentsociety.agent.toolbox`

```{py:module} en_agentsociety.agent.toolbox
```

```{autodoc2-docstring} en_agentsociety.agent.toolbox
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`CustomTool <en_agentsociety.agent.toolbox.CustomTool>`
  - ```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool
    :summary:
    ```
* - {py:obj}`AgentToolbox <en_agentsociety.agent.toolbox.AgentToolbox>`
  - ```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.agent.toolbox.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.agent.toolbox.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.agent.toolbox.__all__
:value: >
   ['AgentToolbox', 'CustomTool']

```{autodoc2-docstring} en_agentsociety.agent.toolbox.__all__
```

````

``````{py:class} CustomTool(/, **data: typing.Any)
:canonical: en_agentsociety.agent.toolbox.CustomTool

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.__init__
```

````{py:attribute} name
:canonical: en_agentsociety.agent.toolbox.CustomTool.name
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.name
```

````

````{py:attribute} tool
:canonical: en_agentsociety.agent.toolbox.CustomTool.tool
:type: typing.Any
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.tool
```

````

````{py:attribute} description
:canonical: en_agentsociety.agent.toolbox.CustomTool.description
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.description
```

````

`````{py:class} Config
:canonical: en_agentsociety.agent.toolbox.CustomTool.Config

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.Config
```

````{py:attribute} arbitrary_types_allowed
:canonical: en_agentsociety.agent.toolbox.CustomTool.Config.arbitrary_types_allowed
:value: >
   True

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.Config.arbitrary_types_allowed
```

````

`````

````{py:method} __call__(*args, **kwargs)
:canonical: en_agentsociety.agent.toolbox.CustomTool.__call__

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.__call__
```

````

````{py:method} get_info() -> typing.Dict[str, typing.Any]
:canonical: en_agentsociety.agent.toolbox.CustomTool.get_info

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.get_info
```

````

````{py:method} get_tool() -> typing.Any
:canonical: en_agentsociety.agent.toolbox.CustomTool.get_tool

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.get_tool
```

````

````{py:method} create_mcp_tool(name: str, tool: typing.Any, description: str, metadata: typing.Optional[typing.Dict[str, typing.Any]] = None) -> en_agentsociety.agent.toolbox.CustomTool
:canonical: en_agentsociety.agent.toolbox.CustomTool.create_mcp_tool
:classmethod:

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.create_mcp_tool
```

````

````{py:method} create_normal_tool(name: str, tool: typing.Any, description: str, metadata: typing.Optional[typing.Dict[str, typing.Any]] = None) -> en_agentsociety.agent.toolbox.CustomTool
:canonical: en_agentsociety.agent.toolbox.CustomTool.create_normal_tool
:classmethod:

```{autodoc2-docstring} en_agentsociety.agent.toolbox.CustomTool.create_normal_tool
```

````

``````

``````{py:class} AgentToolbox(/, **data: typing.Any)
:canonical: en_agentsociety.agent.toolbox.AgentToolbox

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.__init__
```

````{py:attribute} llm
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.llm
:type: en_agentsociety.llm.llm.LLM
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.llm
```

````

````{py:attribute} environment
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.environment
:type: typing.Optional[en_agentsociety.environment.environment.Environment]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.environment
```

````

````{py:attribute} messager
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.messager
:type: typing.Optional[en_agentsociety.message.Messager]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.messager
```

````

````{py:attribute} embedding
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.embedding
:type: fastembed.SparseTextEmbedding
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.embedding
```

````

````{py:attribute} database_writer
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.database_writer
:type: typing.Optional[en_agentsociety.storage.DatabaseWriter]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.database_writer
```

````

````{py:attribute} custom_tools
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.custom_tools
:type: typing.Dict[str, en_agentsociety.agent.toolbox.CustomTool]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.custom_tools
```

````

`````{py:class} Config
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.Config

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.Config
```

````{py:attribute} arbitrary_types_allowed
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.Config.arbitrary_types_allowed
:value: >
   True

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.Config.arbitrary_types_allowed
```

````

`````

````{py:method} add_tool(tool: en_agentsociety.agent.toolbox.CustomTool) -> None
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.add_tool

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.add_tool
```

````

````{py:method} add_custom_tool(tool: en_agentsociety.agent.toolbox.CustomTool) -> None
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.add_custom_tool

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.add_custom_tool
```

````

````{py:method} get_tool(name: str) -> typing.Optional[en_agentsociety.agent.toolbox.CustomTool]
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.get_tool

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.get_tool
```

````

````{py:method} get_tool_object(name: str) -> typing.Optional[typing.Any]
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.get_tool_object

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.get_tool_object
```

````

````{py:method} remove_tool(name: str) -> bool
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.remove_tool

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.remove_tool
```

````

````{py:method} list_tools() -> typing.Dict[str, en_agentsociety.agent.toolbox.CustomTool]
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.list_tools

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.list_tools
```

````

````{py:method} get_tool_info(name: str) -> typing.Optional[typing.Dict[str, typing.Any]]
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.get_tool_info

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.get_tool_info
```

````

````{py:method} get_all_tools_info() -> typing.Dict[str, typing.Dict[str, typing.Any]]
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.get_all_tools_info

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.get_all_tools_info
```

````

````{py:method} has_tool(name: str) -> bool
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.has_tool

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.has_tool
```

````

````{py:method} __getattr__(name: str) -> typing.Any
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.__getattr__

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.__getattr__
```

````

````{py:method} __contains__(name: str) -> bool
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.__contains__

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.__contains__
```

````

````{py:method} __len__() -> int
:canonical: en_agentsociety.agent.toolbox.AgentToolbox.__len__

```{autodoc2-docstring} en_agentsociety.agent.toolbox.AgentToolbox.__len__
```

````

``````
