# {py:mod}`agentsociety.configs`

```{py:module} agentsociety.configs
```

```{autodoc2-docstring} agentsociety.configs
:allowtitles:
```

## Submodules

```{toctree}
:titlesonly:
:maxdepth: 1

agentsociety.configs.exp
agentsociety.configs.utils
agentsociety.configs.env
agentsociety.configs.agent
```

## Package Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AgentsConfig <agentsociety.configs.AgentsConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.AgentsConfig
    :summary:
    ```
* - {py:obj}`AdvancedConfig <agentsociety.configs.AdvancedConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.AdvancedConfig
    :summary:
    ```
* - {py:obj}`Config <agentsociety.configs.Config>`
  - ```{autodoc2-docstring} agentsociety.configs.Config
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.configs.__all__>`
  - ```{autodoc2-docstring} agentsociety.configs.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.configs.__all__
:value: >
   ['EnvConfig', 'AgentConfig', 'WorkflowStepConfig', 'ExpConfig', 'MetricExtractorConfig', 'Environmen...

```{autodoc2-docstring} agentsociety.configs.__all__
```

````

`````{py:class} AgentsConfig(**data: typing.Any)
:canonical: agentsociety.configs.AgentsConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.AgentsConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.__init__
```

````{py:attribute} citizens
:canonical: agentsociety.configs.AgentsConfig.citizens
:type: list[agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.citizens
```

````

````{py:attribute} firms
:canonical: agentsociety.configs.AgentsConfig.firms
:type: list[agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.firms
```

````

````{py:attribute} banks
:canonical: agentsociety.configs.AgentsConfig.banks
:type: list[agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.banks
```

````

````{py:attribute} nbs
:canonical: agentsociety.configs.AgentsConfig.nbs
:type: list[agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.nbs
```

````

````{py:attribute} governments
:canonical: agentsociety.configs.AgentsConfig.governments
:type: list[agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.governments
```

````

````{py:attribute} others
:canonical: agentsociety.configs.AgentsConfig.others
:type: list[agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.others
```

````

````{py:attribute} supervisor
:canonical: agentsociety.configs.AgentsConfig.supervisor
:type: typing.Optional[agentsociety.configs.agent.AgentConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.supervisor
```

````

````{py:attribute} init_funcs
:canonical: agentsociety.configs.AgentsConfig.init_funcs
:type: list[typing.Callable[[typing.Any], typing.Union[None, typing.Awaitable[None]]]]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.init_funcs
```

````

````{py:method} serialize_init_funcs(init_funcs, info)
:canonical: agentsociety.configs.AgentsConfig.serialize_init_funcs

```{autodoc2-docstring} agentsociety.configs.AgentsConfig.serialize_init_funcs
```

````

`````

`````{py:class} AdvancedConfig(**data: typing.Any)
:canonical: agentsociety.configs.AdvancedConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.AdvancedConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.AdvancedConfig.__init__
```

````{py:attribute} simulator
:canonical: agentsociety.configs.AdvancedConfig.simulator
:type: agentsociety.environment.SimulatorConfig
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AdvancedConfig.simulator
```

````

````{py:attribute} logging_level
:canonical: agentsociety.configs.AdvancedConfig.logging_level
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.AdvancedConfig.logging_level
```

````

`````

`````{py:class} Config(**data: typing.Any)
:canonical: agentsociety.configs.Config

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.Config
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.Config.__init__
```

````{py:attribute} llm
:canonical: agentsociety.configs.Config.llm
:type: typing.List[agentsociety.llm.LLMConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.Config.llm
```

````

````{py:attribute} env
:canonical: agentsociety.configs.Config.env
:type: agentsociety.configs.env.EnvConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.Config.env
```

````

````{py:attribute} map
:canonical: agentsociety.configs.Config.map
:type: agentsociety.environment.MapConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.Config.map
```

````

````{py:attribute} agents
:canonical: agentsociety.configs.Config.agents
:type: agentsociety.configs.AgentsConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.Config.agents
```

````

````{py:attribute} exp
:canonical: agentsociety.configs.Config.exp
:type: agentsociety.configs.exp.ExpConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.Config.exp
```

````

````{py:attribute} advanced
:canonical: agentsociety.configs.Config.advanced
:type: agentsociety.configs.AdvancedConfig
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.Config.advanced
```

````

`````
