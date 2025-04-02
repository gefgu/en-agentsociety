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

* - {py:obj}`MemoryConfigGenerator <agentsociety.agent.memory_config_generator.MemoryConfigGenerator>`
  - ```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

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
   ['MemoryConfigGenerator', 'MemoryT']

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.__all__
```

````

````{py:data} MemoryT
:canonical: agentsociety.agent.memory_config_generator.MemoryT
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryT
```

````

`````{py:class} MemoryConfigGenerator(config_func: typing.Callable[[dict[str, agentsociety.agent.distribution.Distribution]], tuple[dict[str, agentsociety.agent.memory_config_generator.MemoryT], dict[str, typing.Union[agentsociety.agent.memory_config_generator.MemoryT, float]], dict[str, typing.Any]]], file: typing.Optional[str] = None, distributions: dict[str, typing.Union[agentsociety.agent.distribution.Distribution, agentsociety.agent.distribution.DistributionConfig]] = {})
:canonical: agentsociety.agent.memory_config_generator.MemoryConfigGenerator

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator.__init__
```

````{py:method} generate(i: int)
:canonical: agentsociety.agent.memory_config_generator.MemoryConfigGenerator.generate

```{autodoc2-docstring} agentsociety.agent.memory_config_generator.MemoryConfigGenerator.generate
```

````

`````

````{py:function} _memory_config_load_file(file_path)
:canonical: agentsociety.agent.memory_config_generator._memory_config_load_file

```{autodoc2-docstring} agentsociety.agent.memory_config_generator._memory_config_load_file
```
````

````{py:function} _memory_config_merge(file_data: dict, base_extra_attrs: dict[str, agentsociety.agent.memory_config_generator.MemoryT], base_profile: dict[str, typing.Union[agentsociety.agent.memory_config_generator.MemoryT, float]], base_base: dict[str, typing.Any]) -> dict[str, typing.Any]
:canonical: agentsociety.agent.memory_config_generator._memory_config_merge

```{autodoc2-docstring} agentsociety.agent.memory_config_generator._memory_config_merge
```
````
