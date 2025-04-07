# {py:mod}`agentsociety.metrics.mlflow_client`

```{py:module} agentsociety.metrics.mlflow_client
```

```{autodoc2-docstring} agentsociety.metrics.mlflow_client
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`MlflowConfig <agentsociety.metrics.mlflow_client.MlflowConfig>`
  - ```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowConfig
    :summary:
    ```
* - {py:obj}`MlflowClient <agentsociety.metrics.mlflow_client.MlflowClient>`
  - ```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.metrics.mlflow_client.__all__>`
  - ```{autodoc2-docstring} agentsociety.metrics.mlflow_client.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.metrics.mlflow_client.__all__
:value: >
   ['MlflowClient', 'MlflowConfig']

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.__all__
```

````

`````{py:class} MlflowConfig(/, **data: typing.Any)
:canonical: agentsociety.metrics.mlflow_client.MlflowConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowConfig.__init__
```

````{py:attribute} enabled
:canonical: agentsociety.metrics.mlflow_client.MlflowConfig.enabled
:type: bool
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowConfig.enabled
```

````

````{py:attribute} username
:canonical: agentsociety.metrics.mlflow_client.MlflowConfig.username
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowConfig.username
```

````

````{py:attribute} password
:canonical: agentsociety.metrics.mlflow_client.MlflowConfig.password
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowConfig.password
```

````

````{py:attribute} mlflow_uri
:canonical: agentsociety.metrics.mlflow_client.MlflowConfig.mlflow_uri
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowConfig.mlflow_uri
```

````

`````

`````{py:class} MlflowClient(config: agentsociety.metrics.mlflow_client.MlflowConfig, exp_name: str, exp_id: str, current_run_id: typing.Optional[str] = None)
:canonical: agentsociety.metrics.mlflow_client.MlflowClient

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient.__init__
```

````{py:property} enabled
:canonical: agentsociety.metrics.mlflow_client.MlflowClient.enabled

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient.enabled
```

````

````{py:method} close()
:canonical: agentsociety.metrics.mlflow_client.MlflowClient.close

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient.close
```

````

````{py:property} client
:canonical: agentsociety.metrics.mlflow_client.MlflowClient.client

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient.client
```

````

````{py:property} run_id
:canonical: agentsociety.metrics.mlflow_client.MlflowClient.run_id
:type: str

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient.run_id
```

````

````{py:method} log_batch(metrics: collections.abc.Sequence[mlflow.entities.Metric] = (), params: collections.abc.Sequence[mlflow.entities.Param] = (), tags: collections.abc.Sequence[mlflow.entities.RunTag] = ())
:canonical: agentsociety.metrics.mlflow_client.MlflowClient.log_batch
:async:

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient.log_batch
```

````

````{py:method} log_metric(key: str, value: float, step: typing.Optional[int] = None, timestamp: typing.Optional[int] = None)
:canonical: agentsociety.metrics.mlflow_client.MlflowClient.log_metric
:async:

```{autodoc2-docstring} agentsociety.metrics.mlflow_client.MlflowClient.log_metric
```

````

`````
