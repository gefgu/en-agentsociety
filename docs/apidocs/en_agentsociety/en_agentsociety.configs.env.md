# {py:mod}`en_agentsociety.configs.env`

```{py:module} en_agentsociety.configs.env
```

```{autodoc2-docstring} en_agentsociety.configs.env
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`EnvConfig <en_agentsociety.configs.env.EnvConfig>`
  - ```{autodoc2-docstring} en_agentsociety.configs.env.EnvConfig
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.configs.env.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.configs.env.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.configs.env.__all__
:value: >
   ['EnvConfig']

```{autodoc2-docstring} en_agentsociety.configs.env.__all__
```

````

`````{py:class} EnvConfig(/, **data: typing.Any)
:canonical: en_agentsociety.configs.env.EnvConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.configs.env.EnvConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.configs.env.EnvConfig.__init__
```

````{py:attribute} db
:canonical: en_agentsociety.configs.env.EnvConfig.db
:type: en_agentsociety.storage.DatabaseConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.configs.env.EnvConfig.db
```

````

````{py:attribute} s3
:canonical: en_agentsociety.configs.env.EnvConfig.s3
:type: en_agentsociety.s3.S3Config
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.env.EnvConfig.s3
```

````

````{py:attribute} home_dir
:canonical: en_agentsociety.configs.env.EnvConfig.home_dir
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.configs.env.EnvConfig.home_dir
```

````

````{py:property} fs_client
:canonical: en_agentsociety.configs.env.EnvConfig.fs_client
:type: typing.Union[en_agentsociety.s3.S3Client, en_agentsociety.filesystem.FileSystemClient]

```{autodoc2-docstring} en_agentsociety.configs.env.EnvConfig.fs_client
```

````

`````
