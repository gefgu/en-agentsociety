# {py:mod}`en_agentsociety.webapi.models`

```{py:module} en_agentsociety.webapi.models
```

```{autodoc2-docstring} en_agentsociety.webapi.models
:allowtitles:
```

## Submodules

```{toctree}
:titlesonly:
:maxdepth: 1

en_agentsociety.webapi.models.config
en_agentsociety.webapi.models._base
en_agentsociety.webapi.models.experiment
en_agentsociety.webapi.models.survey
en_agentsociety.webapi.models.metric
en_agentsociety.webapi.models.agent_profiles
en_agentsociety.webapi.models.agent_template
en_agentsociety.webapi.models.agent
```

## Package Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ApiResponseWrapper <en_agentsociety.webapi.models.ApiResponseWrapper>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.ApiResponseWrapper
    :summary:
    ```
* - {py:obj}`ApiPaginatedResponseWrapper <en_agentsociety.webapi.models.ApiPaginatedResponseWrapper>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.ApiPaginatedResponseWrapper
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.webapi.models.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.__all__
    :summary:
    ```
* - {py:obj}`T <en_agentsociety.webapi.models.T>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.T
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.webapi.models.__all__
:value: >
   ['ApiResponseWrapper']

```{autodoc2-docstring} en_agentsociety.webapi.models.__all__
```

````

````{py:data} T
:canonical: en_agentsociety.webapi.models.T
:value: >
   'TypeVar(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.T
```

````

`````{py:class} ApiResponseWrapper(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.models.ApiResponseWrapper

Bases: {py:obj}`pydantic.BaseModel`, {py:obj}`typing.Generic`\[{py:obj}`en_agentsociety.webapi.models.T`\]

```{autodoc2-docstring} en_agentsociety.webapi.models.ApiResponseWrapper
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.webapi.models.ApiResponseWrapper.__init__
```

````{py:attribute} data
:canonical: en_agentsociety.webapi.models.ApiResponseWrapper.data
:type: en_agentsociety.webapi.models.T
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.ApiResponseWrapper.data
```

````

`````

`````{py:class} ApiPaginatedResponseWrapper(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.models.ApiPaginatedResponseWrapper

Bases: {py:obj}`pydantic.BaseModel`, {py:obj}`typing.Generic`\[{py:obj}`en_agentsociety.webapi.models.T`\]

```{autodoc2-docstring} en_agentsociety.webapi.models.ApiPaginatedResponseWrapper
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.webapi.models.ApiPaginatedResponseWrapper.__init__
```

````{py:attribute} total
:canonical: en_agentsociety.webapi.models.ApiPaginatedResponseWrapper.total
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.ApiPaginatedResponseWrapper.total
```

````

````{py:attribute} data
:canonical: en_agentsociety.webapi.models.ApiPaginatedResponseWrapper.data
:type: typing.List[en_agentsociety.webapi.models.T]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.ApiPaginatedResponseWrapper.data
```

````

`````
