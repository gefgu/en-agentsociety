# {py:mod}`agentsociety.configs.sim_config`

```{py:module} agentsociety.configs.sim_config
```

```{autodoc2-docstring} agentsociety.configs.sim_config
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`LLMRequestConfig <agentsociety.configs.sim_config.LLMRequestConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.LLMRequestConfig
    :summary:
    ```
* - {py:obj}`MQTTConfig <agentsociety.configs.sim_config.MQTTConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.MQTTConfig
    :summary:
    ```
* - {py:obj}`SimulatorRequestConfig <agentsociety.configs.sim_config.SimulatorRequestConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig
    :summary:
    ```
* - {py:obj}`MapRequestConfig <agentsociety.configs.sim_config.MapRequestConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.MapRequestConfig
    :summary:
    ```
* - {py:obj}`MlflowConfig <agentsociety.configs.sim_config.MlflowConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.MlflowConfig
    :summary:
    ```
* - {py:obj}`PostgreSQLConfig <agentsociety.configs.sim_config.PostgreSQLConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.PostgreSQLConfig
    :summary:
    ```
* - {py:obj}`AvroConfig <agentsociety.configs.sim_config.AvroConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.AvroConfig
    :summary:
    ```
* - {py:obj}`MetricRequest <agentsociety.configs.sim_config.MetricRequest>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.MetricRequest
    :summary:
    ```
* - {py:obj}`SimStatus <agentsociety.configs.sim_config.SimStatus>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.SimStatus
    :summary:
    ```
* - {py:obj}`SimConfig <agentsociety.configs.sim_config.SimConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.configs.sim_config.__all__>`
  - ```{autodoc2-docstring} agentsociety.configs.sim_config.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.configs.sim_config.__all__
:value: >
   ['SimConfig']

```{autodoc2-docstring} agentsociety.configs.sim_config.__all__
```

````

`````{py:class} LLMRequestConfig
:canonical: agentsociety.configs.sim_config.LLMRequestConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.LLMRequestConfig
```

````{py:attribute} request_type
:canonical: agentsociety.configs.sim_config.LLMRequestConfig.request_type
:type: agentsociety.utils.LLMRequestType
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.LLMRequestConfig.request_type
```

````

````{py:attribute} api_key
:canonical: agentsociety.configs.sim_config.LLMRequestConfig.api_key
:type: typing.Union[list[str], str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.LLMRequestConfig.api_key
```

````

````{py:attribute} model
:canonical: agentsociety.configs.sim_config.LLMRequestConfig.model
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.LLMRequestConfig.model
```

````

`````

`````{py:class} MQTTConfig
:canonical: agentsociety.configs.sim_config.MQTTConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.MQTTConfig
```

````{py:attribute} server
:canonical: agentsociety.configs.sim_config.MQTTConfig.server
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MQTTConfig.server
```

````

````{py:attribute} port
:canonical: agentsociety.configs.sim_config.MQTTConfig.port
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MQTTConfig.port
```

````

````{py:attribute} password
:canonical: agentsociety.configs.sim_config.MQTTConfig.password
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MQTTConfig.password
```

````

````{py:attribute} username
:canonical: agentsociety.configs.sim_config.MQTTConfig.username
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MQTTConfig.username
```

````

`````

`````{py:class} SimulatorRequestConfig
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig
```

````{py:attribute} task_name
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.task_name
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.task_name
```

````

````{py:attribute} max_day
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.max_day
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.max_day
```

````

````{py:attribute} start_step
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.start_step
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.start_step
```

````

````{py:attribute} total_step
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.total_step
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.total_step
```

````

````{py:attribute} log_dir
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.log_dir
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.log_dir
```

````

````{py:attribute} steps_per_simulation_step
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.steps_per_simulation_step
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.steps_per_simulation_step
```

````

````{py:attribute} steps_per_simulation_day
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.steps_per_simulation_day
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.steps_per_simulation_day
```

````

````{py:attribute} primary_node_ip
:canonical: agentsociety.configs.sim_config.SimulatorRequestConfig.primary_node_ip
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimulatorRequestConfig.primary_node_ip
```

````

`````

`````{py:class} MapRequestConfig
:canonical: agentsociety.configs.sim_config.MapRequestConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.MapRequestConfig
```

````{py:attribute} file_path
:canonical: agentsociety.configs.sim_config.MapRequestConfig.file_path
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MapRequestConfig.file_path
```

````

`````

`````{py:class} MlflowConfig
:canonical: agentsociety.configs.sim_config.MlflowConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.MlflowConfig
```

````{py:attribute} username
:canonical: agentsociety.configs.sim_config.MlflowConfig.username
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MlflowConfig.username
```

````

````{py:attribute} password
:canonical: agentsociety.configs.sim_config.MlflowConfig.password
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MlflowConfig.password
```

````

````{py:attribute} mlflow_uri
:canonical: agentsociety.configs.sim_config.MlflowConfig.mlflow_uri
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MlflowConfig.mlflow_uri
```

````

`````

`````{py:class} PostgreSQLConfig
:canonical: agentsociety.configs.sim_config.PostgreSQLConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.PostgreSQLConfig
```

````{py:attribute} enabled
:canonical: agentsociety.configs.sim_config.PostgreSQLConfig.enabled
:type: typing.Optional[bool]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.PostgreSQLConfig.enabled
```

````

````{py:attribute} dsn
:canonical: agentsociety.configs.sim_config.PostgreSQLConfig.dsn
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.PostgreSQLConfig.dsn
```

````

`````

`````{py:class} AvroConfig
:canonical: agentsociety.configs.sim_config.AvroConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.AvroConfig
```

````{py:attribute} enabled
:canonical: agentsociety.configs.sim_config.AvroConfig.enabled
:type: typing.Optional[bool]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.AvroConfig.enabled
```

````

````{py:attribute} path
:canonical: agentsociety.configs.sim_config.AvroConfig.path
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.AvroConfig.path
```

````

`````

`````{py:class} MetricRequest
:canonical: agentsociety.configs.sim_config.MetricRequest

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.MetricRequest
```

````{py:attribute} mlflow
:canonical: agentsociety.configs.sim_config.MetricRequest.mlflow
:type: typing.Optional[agentsociety.configs.sim_config.MlflowConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.MetricRequest.mlflow
```

````

`````

`````{py:class} SimStatus
:canonical: agentsociety.configs.sim_config.SimStatus

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.SimStatus
```

````{py:attribute} simulator_activated
:canonical: agentsociety.configs.sim_config.SimStatus.simulator_activated
:type: bool
:value: >
   False

```{autodoc2-docstring} agentsociety.configs.sim_config.SimStatus.simulator_activated
```

````

`````

`````{py:class} SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig
```

````{py:attribute} llm_request
:canonical: agentsociety.configs.sim_config.SimConfig.llm_request
:type: typing.Optional[agentsociety.configs.sim_config.LLMRequestConfig]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.llm_request
```

````

````{py:attribute} simulator_request
:canonical: agentsociety.configs.sim_config.SimConfig.simulator_request
:type: typing.Optional[agentsociety.configs.sim_config.SimulatorRequestConfig]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.simulator_request
```

````

````{py:attribute} mqtt
:canonical: agentsociety.configs.sim_config.SimConfig.mqtt
:type: typing.Optional[agentsociety.configs.sim_config.MQTTConfig]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.mqtt
```

````

````{py:attribute} map_request
:canonical: agentsociety.configs.sim_config.SimConfig.map_request
:type: typing.Optional[agentsociety.configs.sim_config.MapRequestConfig]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.map_request
```

````

````{py:attribute} metric_request
:canonical: agentsociety.configs.sim_config.SimConfig.metric_request
:type: typing.Optional[agentsociety.configs.sim_config.MetricRequest]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.metric_request
```

````

````{py:attribute} pgsql
:canonical: agentsociety.configs.sim_config.SimConfig.pgsql
:type: typing.Optional[agentsociety.configs.sim_config.PostgreSQLConfig]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.pgsql
```

````

````{py:attribute} avro
:canonical: agentsociety.configs.sim_config.SimConfig.avro
:type: typing.Optional[agentsociety.configs.sim_config.AvroConfig]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.avro
```

````

````{py:attribute} simulator_server_address
:canonical: agentsociety.configs.sim_config.SimConfig.simulator_server_address
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.simulator_server_address
```

````

````{py:attribute} status
:canonical: agentsociety.configs.sim_config.SimConfig.status
:type: typing.Optional[agentsociety.configs.sim_config.SimStatus]
:value: >
   'SimStatus(...)'

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.status
```

````

````{py:property} prop_llm_request
:canonical: agentsociety.configs.sim_config.SimConfig.prop_llm_request
:type: agentsociety.configs.sim_config.LLMRequestConfig

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_llm_request
```

````

````{py:property} prop_status
:canonical: agentsociety.configs.sim_config.SimConfig.prop_status
:type: agentsociety.configs.sim_config.SimStatus

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_status
```

````

````{py:property} prop_simulator_request
:canonical: agentsociety.configs.sim_config.SimConfig.prop_simulator_request
:type: agentsociety.configs.sim_config.SimulatorRequestConfig

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_simulator_request
```

````

````{py:property} prop_mqtt
:canonical: agentsociety.configs.sim_config.SimConfig.prop_mqtt
:type: agentsociety.configs.sim_config.MQTTConfig

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_mqtt
```

````

````{py:property} prop_map_request
:canonical: agentsociety.configs.sim_config.SimConfig.prop_map_request
:type: agentsociety.configs.sim_config.MapRequestConfig

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_map_request
```

````

````{py:property} prop_avro_config
:canonical: agentsociety.configs.sim_config.SimConfig.prop_avro_config
:type: agentsociety.configs.sim_config.AvroConfig

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_avro_config
```

````

````{py:property} prop_postgre_sql_config
:canonical: agentsociety.configs.sim_config.SimConfig.prop_postgre_sql_config
:type: agentsociety.configs.sim_config.PostgreSQLConfig

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_postgre_sql_config
```

````

````{py:property} prop_simulator_server_address
:canonical: agentsociety.configs.sim_config.SimConfig.prop_simulator_server_address
:type: str

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_simulator_server_address
```

````

````{py:property} prop_metric_request
:canonical: agentsociety.configs.sim_config.SimConfig.prop_metric_request
:type: agentsociety.configs.sim_config.MetricRequest

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.prop_metric_request
```

````

````{py:method} SetLLMRequest(request_type: agentsociety.utils.LLMRequestType, api_key: typing.Union[list[str], str], model: str) -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetLLMRequest

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetLLMRequest
```

````

````{py:method} SetSimulatorRequest(task_name: str = 'citysim', max_day: int = 1000, start_step: int = 28800, total_step: int = 24 * 60 * 60 * 365, log_dir: str = './log', steps_per_simulation_step: int = 300, steps_per_simulation_day: int = 3600, primary_node_ip: str = 'localhost') -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetSimulatorRequest

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetSimulatorRequest
```

````

````{py:method} SetMQTT(server: str, port: int, username: typing.Optional[str] = None, password: typing.Optional[str] = None) -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetMQTT

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetMQTT
```

````

````{py:method} SetMapRequest(file_path: str) -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetMapRequest

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetMapRequest
```

````

````{py:method} SetMetricRequest(username: str, password: str, mlflow_uri: str) -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetMetricRequest

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetMetricRequest
```

````

````{py:method} SetAvro(path: str, enabled: bool = False) -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetAvro

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetAvro
```

````

````{py:method} SetPostgreSql(dsn: str, enabled: bool = False) -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetPostgreSql

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetPostgreSql
```

````

````{py:method} SetServerAddress(simulator_server_address: str) -> agentsociety.configs.sim_config.SimConfig
:canonical: agentsociety.configs.sim_config.SimConfig.SetServerAddress

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.SetServerAddress
```

````

````{py:method} model_dump(*args, **kwargs)
:canonical: agentsociety.configs.sim_config.SimConfig.model_dump

```{autodoc2-docstring} agentsociety.configs.sim_config.SimConfig.model_dump
```

````

`````
