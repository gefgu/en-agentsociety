# {py:mod}`agentsociety.webapi.api.experiment_runner`

```{py:module} agentsociety.webapi.api.experiment_runner
```

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ExperimentResponse <agentsociety.webapi.api.experiment_runner.ExperimentResponse>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.ExperimentResponse
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`run_experiment <agentsociety.webapi.api.experiment_runner.run_experiment>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.run_experiment
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.api.experiment_runner.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.__all__
    :summary:
    ```
* - {py:obj}`router <agentsociety.webapi.api.experiment_runner.router>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.router
    :summary:
    ```
* - {py:obj}`logger <agentsociety.webapi.api.experiment_runner.logger>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.logger
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.api.experiment_runner.__all__
:value: >
   ['router']

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.__all__
```

````

````{py:data} router
:canonical: agentsociety.webapi.api.experiment_runner.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.router
```

````

````{py:data} logger
:canonical: agentsociety.webapi.api.experiment_runner.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.logger
```

````

`````{py:class} ExperimentResponse(/, **data: typing.Any)
:canonical: agentsociety.webapi.api.experiment_runner.ExperimentResponse

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.ExperimentResponse
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.ExperimentResponse.__init__
```

````{py:attribute} id
:canonical: agentsociety.webapi.api.experiment_runner.ExperimentResponse.id
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.ExperimentResponse.id
```

````

````{py:attribute} name
:canonical: agentsociety.webapi.api.experiment_runner.ExperimentResponse.name
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.ExperimentResponse.name
```

````

````{py:attribute} status
:canonical: agentsociety.webapi.api.experiment_runner.ExperimentResponse.status
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.ExperimentResponse.status
```

````

`````

````{py:function} run_experiment(request: fastapi.Request, config: typing.Dict[str, typing.Any]) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.api.experiment_runner.ExperimentResponse]
:canonical: agentsociety.webapi.api.experiment_runner.run_experiment
:async:

```{autodoc2-docstring} agentsociety.webapi.api.experiment_runner.run_experiment
```
````
