# {py:mod}`en_agentsociety.configs`

```{py:module} en_agentsociety.configs
```

```{autodoc2-docstring} en_agentsociety.configs
:allowtitles:
```

## Submodules

```{toctree}
:titlesonly:
:maxdepth: 1

en_agentsociety.configs.exp
en_agentsociety.configs.utils
en_agentsociety.configs.env
en_agentsociety.configs.agent
```

## Package Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AgentsConfig <en_agentsociety.configs.AgentsConfig>`
  - ```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig
    :summary:
    ```
* - {py:obj}`Config <en_agentsociety.configs.Config>`
  - ```{autodoc2-docstring} en_agentsociety.configs.Config
    :summary:
    ```
* - {py:obj}`TaskLoaderConfig <en_agentsociety.configs.TaskLoaderConfig>`
  - ```{autodoc2-docstring} en_agentsociety.configs.TaskLoaderConfig
    :summary:
    ```
* - {py:obj}`IndividualConfig <en_agentsociety.configs.IndividualConfig>`
  - ```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.configs.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.configs.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.configs.__all__
:value: >
   ['EnvConfig', 'AgentConfig', 'WorkflowStepConfig', 'ExpConfig', 'EnvironmentConfig', 'Config', 'load...

```{autodoc2-docstring} en_agentsociety.configs.__all__
```

````

`````{py:class} AgentsConfig(/, **data: typing.Any)
:canonical: en_agentsociety.configs.AgentsConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.__init__
```

````{py:attribute} citizens
:canonical: en_agentsociety.configs.AgentsConfig.citizens
:type: list[en_agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.citizens
```

````

````{py:attribute} firms
:canonical: en_agentsociety.configs.AgentsConfig.firms
:type: list[en_agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.firms
```

````

````{py:attribute} banks
:canonical: en_agentsociety.configs.AgentsConfig.banks
:type: list[en_agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.banks
```

````

````{py:attribute} nbs
:canonical: en_agentsociety.configs.AgentsConfig.nbs
:type: list[en_agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.nbs
```

````

````{py:attribute} governments
:canonical: en_agentsociety.configs.AgentsConfig.governments
:type: list[en_agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.governments
```

````

````{py:attribute} supervisor
:canonical: en_agentsociety.configs.AgentsConfig.supervisor
:type: typing.Optional[en_agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.supervisor
```

````

````{py:attribute} init_funcs
:canonical: en_agentsociety.configs.AgentsConfig.init_funcs
:type: list[typing.Callable[[typing.Any], typing.Union[None, typing.Awaitable[None]]]]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.init_funcs
```

````

````{py:method} serialize_init_funcs(init_funcs, info)
:canonical: en_agentsociety.configs.AgentsConfig.serialize_init_funcs

```{autodoc2-docstring} en_agentsociety.configs.AgentsConfig.serialize_init_funcs
```

````

`````

`````{py:class} Config(/, **data: typing.Any)
:canonical: en_agentsociety.configs.Config

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.configs.Config
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.configs.Config.__init__
```

````{py:attribute} llm
:canonical: en_agentsociety.configs.Config.llm
:type: typing.List[en_agentsociety.llm.LLMConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.Config.llm
```

````

````{py:attribute} env
:canonical: en_agentsociety.configs.Config.env
:type: en_agentsociety.configs.env.EnvConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.Config.env
```

````

````{py:attribute} map
:canonical: en_agentsociety.configs.Config.map
:type: en_agentsociety.environment.MapConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.Config.map
```

````

````{py:attribute} agents
:canonical: en_agentsociety.configs.Config.agents
:type: en_agentsociety.configs.AgentsConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.Config.agents
```

````

````{py:attribute} exp
:canonical: en_agentsociety.configs.Config.exp
:type: en_agentsociety.configs.exp.ExpConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.Config.exp
```

````

````{py:attribute} logging_level
:canonical: en_agentsociety.configs.Config.logging_level
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.Config.logging_level
```

````

`````

`````{py:class} TaskLoaderConfig(/, **data: typing.Any)
:canonical: en_agentsociety.configs.TaskLoaderConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.configs.TaskLoaderConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.configs.TaskLoaderConfig.__init__
```

````{py:attribute} task_type
:canonical: en_agentsociety.configs.TaskLoaderConfig.task_type
:type: type[en_agentsociety.taskloader.Task]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.TaskLoaderConfig.task_type
```

````

````{py:attribute} file_path
:canonical: en_agentsociety.configs.TaskLoaderConfig.file_path
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.TaskLoaderConfig.file_path
```

````

````{py:attribute} shuffle
:canonical: en_agentsociety.configs.TaskLoaderConfig.shuffle
:type: bool
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.TaskLoaderConfig.shuffle
```

````

`````

`````{py:class} IndividualConfig(/, **data: typing.Any)
:canonical: en_agentsociety.configs.IndividualConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.__init__
```

````{py:attribute} name
:canonical: en_agentsociety.configs.IndividualConfig.name
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.name
```

````

````{py:attribute} llm
:canonical: en_agentsociety.configs.IndividualConfig.llm
:type: typing.List[en_agentsociety.llm.LLMConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.llm
```

````

````{py:attribute} env
:canonical: en_agentsociety.configs.IndividualConfig.env
:type: en_agentsociety.configs.env.EnvConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.env
```

````

````{py:attribute} id
:canonical: en_agentsociety.configs.IndividualConfig.id
:type: uuid.UUID
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.id
```

````

````{py:attribute} individual
:canonical: en_agentsociety.configs.IndividualConfig.individual
:type: en_agentsociety.configs.agent.AgentConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.individual
```

````

````{py:attribute} task_loader
:canonical: en_agentsociety.configs.IndividualConfig.task_loader
:type: en_agentsociety.configs.TaskLoaderConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.task_loader
```

````

````{py:attribute} logging_level
:canonical: en_agentsociety.configs.IndividualConfig.logging_level
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.logging_level
```

````

````{py:method} serialize_id(id, info)
:canonical: en_agentsociety.configs.IndividualConfig.serialize_id

```{autodoc2-docstring} en_agentsociety.configs.IndividualConfig.serialize_id
```

````

`````
