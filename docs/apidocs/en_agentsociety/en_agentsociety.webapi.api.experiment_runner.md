# {py:mod}`en_agentsociety.webapi.api.experiment_runner`

```{py:module} en_agentsociety.webapi.api.experiment_runner
```

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ConfigPrimaryKey <en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey
    :summary:
    ```
* - {py:obj}`ExperimentRequest <en_agentsociety.webapi.api.experiment_runner.ExperimentRequest>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest
    :summary:
    ```
* - {py:obj}`ExperimentResponse <en_agentsociety.webapi.api.experiment_runner.ExperimentResponse>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentResponse
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`run_experiment <en_agentsociety.webapi.api.experiment_runner.run_experiment>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.run_experiment
    :summary:
    ```
* - {py:obj}`delete_experiment <en_agentsociety.webapi.api.experiment_runner.delete_experiment>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.delete_experiment
    :summary:
    ```
* - {py:obj}`get_experiment_logs <en_agentsociety.webapi.api.experiment_runner.get_experiment_logs>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.get_experiment_logs
    :summary:
    ```
* - {py:obj}`get_experiment_status <en_agentsociety.webapi.api.experiment_runner.get_experiment_status>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.get_experiment_status
    :summary:
    ```
* - {py:obj}`finish_experiment <en_agentsociety.webapi.api.experiment_runner.finish_experiment>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.finish_experiment
    :summary:
    ```
* - {py:obj}`_compute_commercial_bill <en_agentsociety.webapi.api.experiment_runner._compute_commercial_bill>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner._compute_commercial_bill
    :summary:
    ```
* - {py:obj}`_check_commercial_balance <en_agentsociety.webapi.api.experiment_runner._check_commercial_balance>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner._check_commercial_balance
    :summary:
    ```
* - {py:obj}`_record_experiment_bill <en_agentsociety.webapi.api.experiment_runner._record_experiment_bill>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner._record_experiment_bill
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.webapi.api.experiment_runner.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.__all__
    :summary:
    ```
* - {py:obj}`router <en_agentsociety.webapi.api.experiment_runner.router>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.router
    :summary:
    ```
* - {py:obj}`logger <en_agentsociety.webapi.api.experiment_runner.logger>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.logger
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.webapi.api.experiment_runner.__all__
:value: >
   ['router']

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.__all__
```

````

````{py:data} router
:canonical: en_agentsociety.webapi.api.experiment_runner.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.router
```

````

````{py:data} logger
:canonical: en_agentsociety.webapi.api.experiment_runner.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.logger
```

````

`````{py:class} ConfigPrimaryKey(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey.__init__
```

````{py:attribute} tenant_id
:canonical: en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey.tenant_id
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey.tenant_id
```

````

````{py:attribute} id
:canonical: en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey.id
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey.id
```

````

`````

`````{py:class} ExperimentRequest(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentRequest

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.__init__
```

````{py:attribute} llm
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.llm
:type: en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.llm
```

````

````{py:attribute} agents
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.agents
:type: en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.agents
```

````

````{py:attribute} map
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.map
:type: en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.map
```

````

````{py:attribute} workflow
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.workflow
:type: en_agentsociety.webapi.api.experiment_runner.ConfigPrimaryKey
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.workflow
```

````

````{py:attribute} exp_name
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.exp_name
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentRequest.exp_name
```

````

`````

`````{py:class} ExperimentResponse(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentResponse

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentResponse
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentResponse.__init__
```

````{py:attribute} id
:canonical: en_agentsociety.webapi.api.experiment_runner.ExperimentResponse.id
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.ExperimentResponse.id
```

````

`````

````{py:function} run_experiment(request: fastapi.Request, config: en_agentsociety.webapi.api.experiment_runner.ExperimentRequest = Body(...)) -> en_agentsociety.webapi.models.ApiResponseWrapper[en_agentsociety.webapi.api.experiment_runner.ExperimentResponse]
:canonical: en_agentsociety.webapi.api.experiment_runner.run_experiment
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.run_experiment
```
````

````{py:function} delete_experiment(request: fastapi.Request, exp_id: str)
:canonical: en_agentsociety.webapi.api.experiment_runner.delete_experiment
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.delete_experiment
```
````

````{py:function} get_experiment_logs(request: fastapi.Request, exp_id: str) -> str
:canonical: en_agentsociety.webapi.api.experiment_runner.get_experiment_logs
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.get_experiment_logs
```
````

````{py:function} get_experiment_status(request: fastapi.Request, exp_id: str) -> en_agentsociety.webapi.models.ApiResponseWrapper[str]
:canonical: en_agentsociety.webapi.api.experiment_runner.get_experiment_status
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.get_experiment_status
```
````

````{py:function} finish_experiment(request: fastapi.Request, exp_id: str, callback_auth_token: str = Query(...))
:canonical: en_agentsociety.webapi.api.experiment_runner.finish_experiment
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner.finish_experiment
```
````

````{py:function} _compute_commercial_bill(app_state, db: sqlalchemy.ext.asyncio.AsyncSession, experiment: en_agentsociety.webapi.models.experiment.Experiment)
:canonical: en_agentsociety.webapi.api.experiment_runner._compute_commercial_bill
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner._compute_commercial_bill
```
````

````{py:function} _check_commercial_balance(app_state, tenant_id: str, db: sqlalchemy.ext.asyncio.AsyncSession)
:canonical: en_agentsociety.webapi.api.experiment_runner._check_commercial_balance
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner._check_commercial_balance
```
````

````{py:function} _record_experiment_bill(app_state, db: sqlalchemy.ext.asyncio.AsyncSession, tenant_id: str, exp_id: uuid.UUID, llm_config_id: typing.Optional[uuid.UUID] = None)
:canonical: en_agentsociety.webapi.api.experiment_runner._record_experiment_bill
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.experiment_runner._record_experiment_bill
```
````
