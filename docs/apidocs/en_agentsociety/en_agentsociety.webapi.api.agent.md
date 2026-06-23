# {py:mod}`en_agentsociety.webapi.api.agent`

```{py:module} en_agentsociety.webapi.api.agent
```

```{autodoc2-docstring} en_agentsociety.webapi.api.agent
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AgentChatMessage <en_agentsociety.webapi.api.agent.AgentChatMessage>`
  -
* - {py:obj}`AgentSurveyMessage <en_agentsociety.webapi.api.agent.AgentSurveyMessage>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_agent_dialog_by_exp_id_and_agent_id <en_agentsociety.webapi.api.agent.get_agent_dialog_by_exp_id_and_agent_id>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_dialog_by_exp_id_and_agent_id
    :summary:
    ```
* - {py:obj}`list_agent_profile_by_exp_id <en_agentsociety.webapi.api.agent.list_agent_profile_by_exp_id>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.list_agent_profile_by_exp_id
    :summary:
    ```
* - {py:obj}`get_agent_profile_by_exp_id_and_agent_id <en_agentsociety.webapi.api.agent.get_agent_profile_by_exp_id_and_agent_id>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_profile_by_exp_id_and_agent_id
    :summary:
    ```
* - {py:obj}`list_agent_status_by_day_and_t <en_agentsociety.webapi.api.agent.list_agent_status_by_day_and_t>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.list_agent_status_by_day_and_t
    :summary:
    ```
* - {py:obj}`get_agent_status_by_exp_id_and_agent_id <en_agentsociety.webapi.api.agent.get_agent_status_by_exp_id_and_agent_id>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_status_by_exp_id_and_agent_id
    :summary:
    ```
* - {py:obj}`get_agent_survey_by_exp_id_and_agent_id <en_agentsociety.webapi.api.agent.get_agent_survey_by_exp_id_and_agent_id>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_survey_by_exp_id_and_agent_id
    :summary:
    ```
* - {py:obj}`get_global_prompt_by_day_t <en_agentsociety.webapi.api.agent.get_global_prompt_by_day_t>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_global_prompt_by_day_t
    :summary:
    ```
* - {py:obj}`post_agent_dialog <en_agentsociety.webapi.api.agent.post_agent_dialog>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.post_agent_dialog
    :summary:
    ```
* - {py:obj}`post_agent_survey <en_agentsociety.webapi.api.agent.post_agent_survey>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.post_agent_survey
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.webapi.api.agent.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.__all__
    :summary:
    ```
* - {py:obj}`router <en_agentsociety.webapi.api.agent.router>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.api.agent.router
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.webapi.api.agent.__all__
:value: >
   ['router']

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.__all__
```

````

````{py:data} router
:canonical: en_agentsociety.webapi.api.agent.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.router
```

````

````{py:function} get_agent_dialog_by_exp_id_and_agent_id(request: fastapi.Request, exp_id: uuid.UUID, agent_id: int) -> en_agentsociety.webapi.models.ApiResponseWrapper[typing.List[en_agentsociety.webapi.models.agent.ApiAgentDialog]]
:canonical: en_agentsociety.webapi.api.agent.get_agent_dialog_by_exp_id_and_agent_id
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_dialog_by_exp_id_and_agent_id
```
````

````{py:function} list_agent_profile_by_exp_id(request: fastapi.Request, exp_id: uuid.UUID) -> en_agentsociety.webapi.models.ApiResponseWrapper[typing.List[en_agentsociety.webapi.models.agent.ApiAgentProfile]]
:canonical: en_agentsociety.webapi.api.agent.list_agent_profile_by_exp_id
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.list_agent_profile_by_exp_id
```
````

````{py:function} get_agent_profile_by_exp_id_and_agent_id(request: fastapi.Request, exp_id: uuid.UUID, agent_id: int) -> en_agentsociety.webapi.models.ApiResponseWrapper[en_agentsociety.webapi.models.agent.ApiAgentProfile]
:canonical: en_agentsociety.webapi.api.agent.get_agent_profile_by_exp_id_and_agent_id
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_profile_by_exp_id_and_agent_id
```
````

````{py:function} list_agent_status_by_day_and_t(request: fastapi.Request, exp_id: uuid.UUID, day: typing.Optional[int] = Query(None, description='the day for getting agent status'), t: typing.Optional[float] = Query(None, description='the time for getting agent status')) -> en_agentsociety.webapi.models.ApiResponseWrapper[typing.List[en_agentsociety.webapi.models.agent.ApiAgentStatus]]
:canonical: en_agentsociety.webapi.api.agent.list_agent_status_by_day_and_t
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.list_agent_status_by_day_and_t
```
````

````{py:function} get_agent_status_by_exp_id_and_agent_id(request: fastapi.Request, exp_id: uuid.UUID, agent_id: int) -> en_agentsociety.webapi.models.ApiResponseWrapper[typing.List[en_agentsociety.webapi.models.agent.ApiAgentStatus]]
:canonical: en_agentsociety.webapi.api.agent.get_agent_status_by_exp_id_and_agent_id
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_status_by_exp_id_and_agent_id
```
````

````{py:function} get_agent_survey_by_exp_id_and_agent_id(request: fastapi.Request, exp_id: uuid.UUID, agent_id: int) -> en_agentsociety.webapi.models.ApiResponseWrapper[typing.List[en_agentsociety.webapi.models.agent.ApiAgentSurvey]]
:canonical: en_agentsociety.webapi.api.agent.get_agent_survey_by_exp_id_and_agent_id
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_agent_survey_by_exp_id_and_agent_id
```
````

````{py:function} get_global_prompt_by_day_t(request: fastapi.Request, exp_id: uuid.UUID, day: typing.Optional[int] = Query(None, description='the day for getting agent status'), t: typing.Optional[float] = Query(None, description='the time for getting agent status')) -> en_agentsociety.webapi.models.ApiResponseWrapper[typing.Optional[en_agentsociety.webapi.models.agent.ApiGlobalPrompt]]
:canonical: en_agentsociety.webapi.api.agent.get_global_prompt_by_day_t
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.get_global_prompt_by_day_t
```
````

`````{py:class} AgentChatMessage(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.api.agent.AgentChatMessage

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} content
:canonical: en_agentsociety.webapi.api.agent.AgentChatMessage.content
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.AgentChatMessage.content
```

````

````{py:attribute} day
:canonical: en_agentsociety.webapi.api.agent.AgentChatMessage.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.AgentChatMessage.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.webapi.api.agent.AgentChatMessage.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.AgentChatMessage.t
```

````

`````

````{py:function} post_agent_dialog(request: fastapi.Request, exp_id: uuid.UUID, agent_id: int, message: en_agentsociety.webapi.api.agent.AgentChatMessage = Body(...)) -> en_agentsociety.webapi.models.ApiResponseWrapper[None]
:canonical: en_agentsociety.webapi.api.agent.post_agent_dialog
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.post_agent_dialog
```
````

`````{py:class} AgentSurveyMessage(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.api.agent.AgentSurveyMessage

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} survey_id
:canonical: en_agentsociety.webapi.api.agent.AgentSurveyMessage.survey_id
:type: uuid.UUID
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.AgentSurveyMessage.survey_id
```

````

````{py:attribute} day
:canonical: en_agentsociety.webapi.api.agent.AgentSurveyMessage.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.AgentSurveyMessage.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.webapi.api.agent.AgentSurveyMessage.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.AgentSurveyMessage.t
```

````

`````

````{py:function} post_agent_survey(request: fastapi.Request, exp_id: uuid.UUID, agent_id: int, message: en_agentsociety.webapi.api.agent.AgentSurveyMessage = Body(...)) -> en_agentsociety.webapi.models.ApiResponseWrapper[None]
:canonical: en_agentsociety.webapi.api.agent.post_agent_survey
:async:

```{autodoc2-docstring} en_agentsociety.webapi.api.agent.post_agent_survey
```
````
