# {py:mod}`en_agentsociety.webapi.api.survey`

```{py:module} en_agentsociety.webapi.api.survey
```

```{autodoc2-docstring} en_agentsociety.webapi.api.survey
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ApiSurveyCreate <en_agentsociety.webapi.api.survey.ApiSurveyCreate>`
  -
* - {py:obj}`ApiSurveyUpdate <en_agentsociety.webapi.api.survey.ApiSurveyUpdate>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`list_survey <en_agentsociety.webapi.api.survey.list_survey>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.survey.list_survey
    :summary:
    ```
* - {py:obj}`get_survey <en_agentsociety.webapi.api.survey.get_survey>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.survey.get_survey
    :summary:
    ```
* - {py:obj}`create_survey <en_agentsociety.webapi.api.survey.create_survey>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.survey.create_survey
    :summary:
    ```
* - {py:obj}`update_survey <en_agentsociety.webapi.api.survey.update_survey>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.survey.update_survey
    :summary:
    ```
* - {py:obj}`delete_survey <en_agentsociety.webapi.api.survey.delete_survey>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.survey.delete_survey
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.webapi.api.survey.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.survey.__all__
    :summary:
    ```
* - {py:obj}`router <en_agentsociety.webapi.api.survey.router>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.survey.router
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.webapi.api.survey.__all__
:value: >
   ['router']

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.__all__
```

````

````{py:data} router
:canonical: en_agentsociety.webapi.api.survey.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.router
```

````

````{py:function} list_survey(request: fastapi.Request) -> en_agentsociety.webapi.models.ApiResponseWrapper[typing.List[en_agentsociety.webapi.models.survey.ApiSurvey]]
:canonical: en_agentsociety.webapi.api.survey.list_survey
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.list_survey
```
````

````{py:function} get_survey(request: fastapi.Request, id: uuid.UUID) -> en_agentsociety.webapi.models.ApiResponseWrapper[en_agentsociety.webapi.models.survey.ApiSurvey]
:canonical: en_agentsociety.webapi.api.survey.get_survey
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.get_survey
```
````

`````{py:class} ApiSurveyCreate(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.api.survey.ApiSurveyCreate

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} name
:canonical: en_agentsociety.webapi.api.survey.ApiSurveyCreate.name
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.ApiSurveyCreate.name
```

````

````{py:attribute} data
:canonical: en_agentsociety.webapi.api.survey.ApiSurveyCreate.data
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.ApiSurveyCreate.data
```

````

`````

````{py:function} create_survey(request: fastapi.Request, survey: en_agentsociety.webapi.api.survey.ApiSurveyCreate)
:canonical: en_agentsociety.webapi.api.survey.create_survey
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.create_survey
```
````

`````{py:class} ApiSurveyUpdate(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.api.survey.ApiSurveyUpdate

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} name
:canonical: en_agentsociety.webapi.api.survey.ApiSurveyUpdate.name
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.ApiSurveyUpdate.name
```

````

````{py:attribute} data
:canonical: en_agentsociety.webapi.api.survey.ApiSurveyUpdate.data
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.ApiSurveyUpdate.data
```

````

`````

````{py:function} update_survey(request: fastapi.Request, id: uuid.UUID, survey: en_agentsociety.webapi.api.survey.ApiSurveyUpdate)
:canonical: en_agentsociety.webapi.api.survey.update_survey
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.update_survey
```
````

````{py:function} delete_survey(request: fastapi.Request, id: uuid.UUID)
:canonical: en_agentsociety.webapi.api.survey.delete_survey
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.survey.delete_survey
```
````
