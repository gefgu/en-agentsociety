# {py:mod}`agentsociety.configs.env`

```{py:module} agentsociety.configs.env
```

```{autodoc2-docstring} agentsociety.configs.env
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`EnvConfig <agentsociety.configs.env.EnvConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.env.EnvConfig
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.configs.env.__all__>`
  - ```{autodoc2-docstring} agentsociety.configs.env.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.configs.env.__all__
:value: >
   ['EnvConfig']

```{autodoc2-docstring} agentsociety.configs.env.__all__
```

````

`````{py:class} EnvConfig(/, **data: typing.Any)
:canonical: agentsociety.configs.env.EnvConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.env.EnvConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.env.EnvConfig.__init__
```

````{py:attribute} redis
:canonical: agentsociety.configs.env.EnvConfig.redis
:type: agentsociety.message.RedisConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.env.EnvConfig.redis
```

````

````{py:attribute} pgsql
:canonical: agentsociety.configs.env.EnvConfig.pgsql
:type: agentsociety.storage.PostgreSQLConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.env.EnvConfig.pgsql
```

````

````{py:attribute} avro
:canonical: agentsociety.configs.env.EnvConfig.avro
:type: agentsociety.storage.AvroConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.env.EnvConfig.avro
```

````

````{py:attribute} mlflow
:canonical: agentsociety.configs.env.EnvConfig.mlflow
:type: agentsociety.metrics.MlflowConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.env.EnvConfig.mlflow
```

````

`````
