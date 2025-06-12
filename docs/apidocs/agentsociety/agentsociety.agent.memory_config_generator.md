# {py:mod}`agentsociety.agent.memory_config_generator`

```{py:module} agentsociety.agent.memory_config_generator
```

```{autodoc2-docstring} agentsociety.agent.memory_config_generator
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`StatusAttribute <agentsociety.agent.memory_config_generator.StatusAttribute>`
  -
* - {py:obj}`MemoryConfigGenerator <agentsociety.agent.memory_config_generator.MemoryConfigGenerator>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`default_memory_config_citizen <agentsociety.agent.memory_config_generator.default_memory_config_citizen>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator.default_memory_config_citizen
    :summary:
    ```
* - {py:obj}`default_memory_config_supervisor <agentsociety.agent.memory_config_generator.default_memory_config_supervisor>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator.default_memory_config_supervisor
    :summary:
    ```
* - {py:obj}`_memory_config_load_file <agentsociety.agent.memory_config_generator._memory_config_load_file>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator._memory_config_load_file
    :summary:
    ```
* - {py:obj}`_memory_config_merge <agentsociety.agent.memory_config_generator._memory_config_merge>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator._memory_config_merge
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.agent.memory_config_generator.__all__>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator.__all__
    :summary:
    ```
* - {py:obj}`MemoryT <agentsociety.agent.memory_config_generator.MemoryT>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryT
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.agent.memory_config_generator.__all__
:value: >
   ['MemoryConfigGenerator', 'MemoryT', 'StatusAttribute', 'default_memory_config_citizen']

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.__all__
```

````

`````{py:class} StatusAttribute(**data: typing.Any)
:canonical: agentsociety.agent.memory_config_generator.StatusAttribute

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} name
:canonical: agentsociety.agent.memory_config_generator.StatusAttribute.name
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.StatusAttribute.name
```

````

````{py:attribute} type
:canonical: agentsociety.agent.memory_config_generator.StatusAttribute.type
:type: agentsociety.agent.memory_config_generator.StatusAttribute.type
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.StatusAttribute.type
```

````

````{py:attribute} default
:canonical: agentsociety.agent.memory_config_generator.StatusAttribute.default
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.StatusAttribute.default
```

````

````{py:attribute} description
:canonical: agentsociety.agent.memory_config_generator.StatusAttribute.description
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.StatusAttribute.description
```

````

````{py:attribute} whether_embedding
:canonical: agentsociety.agent.memory_config_generator.StatusAttribute.whether_embedding
:type: bool
:value: >
   False

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.StatusAttribute.whether_embedding
```

````

````{py:attribute} embedding_template
:canonical: agentsociety.agent.memory_config_generator.StatusAttribute.embedding_template
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.StatusAttribute.embedding_template
```

````

`````

````{py:data} MemoryT
:canonical: agentsociety.agent.memory_config_generator.MemoryT
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryT
```

````

````{py:function} default_memory_config_citizen(distributions: dict[str, agentsociety.agent.distribution.Distribution], class_config: typing.Optional[list[agentsociety.agent.memory_config_generator.StatusAttribute]] = None) -> tuple[dict[str, agentsociety.agent.memory_config_generator.MemoryT], dict[str, agentsociety.agent.memory_config_generator.MemoryT], dict[str, typing.Any]]
:canonical: agentsociety.agent.memory_config_generator.default_memory_config_citizen

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.default_memory_config_citizen
```
````

````{py:function} default_memory_config_supervisor(distributions: dict[str, agentsociety.agent.distribution.Distribution], class_config: typing.Optional[list[agentsociety.agent.memory_config_generator.StatusAttribute]] = None) -> tuple[dict[str, agentsociety.agent.memory_config_generator.MemoryT], dict[str, agentsociety.agent.memory_config_generator.MemoryT], dict[str, typing.Any]]
:canonical: agentsociety.agent.memory_config_generator.default_memory_config_supervisor

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.default_memory_config_supervisor
```
````

`````{py:class} MemoryConfigGenerator(config_func: typing.Callable[[dict[str, agentsociety.agent.distribution.Distribution], typing.Optional[list[agentsociety.agent.memory_config_generator.StatusAttribute]]], tuple[dict[str, agentsociety.agent.memory_config_generator.MemoryT], dict[str, agentsociety.agent.memory_config_generator.MemoryT], dict[str, typing.Any]]], class_config: typing.Optional[list[agentsociety.agent.memory_config_generator.StatusAttribute]] = None, number: typing.Optional[int] = None, file: typing.Optional[str] = None, distributions: dict[str, typing.Union[agentsociety.agent.distribution.Distribution, agentsociety.agent.distribution.DistributionConfig]] = {}, s3config: agentsociety.s3.S3Config = S3Config.model_validate({}))
:canonical: agentsociety.agent.memory_config_generator.MemoryConfigGenerator

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator.__init__
```

````{py:method} merge_distributions(distributions: dict[str, typing.Union[agentsociety.agent.distribution.Distribution, agentsociety.agent.distribution.DistributionConfig]])
:canonical: agentsociety.agent.memory_config_generator.MemoryConfigGenerator.merge_distributions

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator.merge_distributions
```

````

````{py:method} generate(i: int)
:canonical: agentsociety.agent.memory_config_generator.MemoryConfigGenerator.generate

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator.generate
```

````

````{py:method} get_agent_data_from_file() -> typing.List[dict]
:canonical: agentsociety.agent.memory_config_generator.MemoryConfigGenerator.get_agent_data_from_file

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator.get_agent_data_from_file
```

````

`````

````{py:function} _memory_config_load_file(file_path: str, s3config: agentsociety.s3.S3Config)
:canonical: agentsociety.agent.memory_config_generator._memory_config_load_file

```{autodoc2-docstring} agentsociety.agent.memory_config_generator._memory_config_load_file
```
````

````{py:function} _memory_config_merge(file_data: dict, base_extra_attrs: dict[str, agentsociety.agent.memory_config_generator.MemoryT], base_profile: dict[str, agentsociety.agent.memory_config_generator.MemoryT], base_base: dict[str, typing.Any]) -> dict[str, typing.Any]
:canonical: agentsociety.agent.memory_config_generator._memory_config_merge

```{autodoc2-docstring} agentsociety.agent.memory_config_generator._memory_config_merge
```
````
