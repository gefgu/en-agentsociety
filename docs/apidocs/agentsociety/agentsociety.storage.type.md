# {py:mod}`agentsociety.storage.type`

```{py:module} agentsociety.storage.type
```

```{autodoc2-docstring} agentsociety.storage.type
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`StorageExpInfo <agentsociety.storage.type.StorageExpInfo>`
  -
* - {py:obj}`StorageSurvey <agentsociety.storage.type.StorageSurvey>`
  -
* - {py:obj}`StorageDialog <agentsociety.storage.type.StorageDialog>`
  -
* - {py:obj}`StorageGlobalPrompt <agentsociety.storage.type.StorageGlobalPrompt>`
  -
* - {py:obj}`StorageProfile <agentsociety.storage.type.StorageProfile>`
  -
* - {py:obj}`StorageStatus <agentsociety.storage.type.StorageStatus>`
  -
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.storage.type.__all__>`
  - ```{autodoc2-docstring} agentsociety.storage.type.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.storage.type.__all__
:value: >
   ['StorageSurvey', 'StorageDialog', 'StorageGlobalPrompt', 'StorageProfile', 'StorageStatus']

```{autodoc2-docstring} agentsociety.storage.type.__all__
```

````

`````{py:class} StorageExpInfo(/, **data: typing.Any)
:canonical: agentsociety.storage.type.StorageExpInfo

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} tenant_id
:canonical: agentsociety.storage.type.StorageExpInfo.tenant_id
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.tenant_id
```

````

````{py:attribute} id
:canonical: agentsociety.storage.type.StorageExpInfo.id
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.id
```

````

````{py:attribute} name
:canonical: agentsociety.storage.type.StorageExpInfo.name
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.name
```

````

````{py:attribute} num_day
:canonical: agentsociety.storage.type.StorageExpInfo.num_day
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.num_day
```

````

````{py:attribute} status
:canonical: agentsociety.storage.type.StorageExpInfo.status
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.status
```

````

````{py:attribute} cur_day
:canonical: agentsociety.storage.type.StorageExpInfo.cur_day
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.cur_day
```

````

````{py:attribute} cur_t
:canonical: agentsociety.storage.type.StorageExpInfo.cur_t
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.cur_t
```

````

````{py:attribute} config
:canonical: agentsociety.storage.type.StorageExpInfo.config
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.config
```

````

````{py:attribute} error
:canonical: agentsociety.storage.type.StorageExpInfo.error
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.error
```

````

````{py:attribute} input_tokens
:canonical: agentsociety.storage.type.StorageExpInfo.input_tokens
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.input_tokens
```

````

````{py:attribute} output_tokens
:canonical: agentsociety.storage.type.StorageExpInfo.output_tokens
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.output_tokens
```

````

````{py:attribute} created_at
:canonical: agentsociety.storage.type.StorageExpInfo.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.created_at
```

````

````{py:attribute} updated_at
:canonical: agentsociety.storage.type.StorageExpInfo.updated_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageExpInfo.updated_at
```

````

`````

`````{py:class} StorageSurvey(/, **data: typing.Any)
:canonical: agentsociety.storage.type.StorageSurvey

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: agentsociety.storage.type.StorageSurvey.id
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageSurvey.id
```

````

````{py:attribute} day
:canonical: agentsociety.storage.type.StorageSurvey.day
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageSurvey.day
```

````

````{py:attribute} t
:canonical: agentsociety.storage.type.StorageSurvey.t
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageSurvey.t
```

````

````{py:attribute} survey_id
:canonical: agentsociety.storage.type.StorageSurvey.survey_id
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageSurvey.survey_id
```

````

````{py:attribute} result
:canonical: agentsociety.storage.type.StorageSurvey.result
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageSurvey.result
```

````

````{py:attribute} created_at
:canonical: agentsociety.storage.type.StorageSurvey.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageSurvey.created_at
```

````

`````

`````{py:class} StorageDialog(/, **data: typing.Any)
:canonical: agentsociety.storage.type.StorageDialog

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: agentsociety.storage.type.StorageDialog.id
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageDialog.id
```

````

````{py:attribute} day
:canonical: agentsociety.storage.type.StorageDialog.day
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageDialog.day
```

````

````{py:attribute} t
:canonical: agentsociety.storage.type.StorageDialog.t
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageDialog.t
```

````

````{py:attribute} type
:canonical: agentsociety.storage.type.StorageDialog.type
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageDialog.type
```

````

````{py:attribute} speaker
:canonical: agentsociety.storage.type.StorageDialog.speaker
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageDialog.speaker
```

````

````{py:attribute} content
:canonical: agentsociety.storage.type.StorageDialog.content
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageDialog.content
```

````

````{py:attribute} created_at
:canonical: agentsociety.storage.type.StorageDialog.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageDialog.created_at
```

````

`````

`````{py:class} StorageGlobalPrompt(/, **data: typing.Any)
:canonical: agentsociety.storage.type.StorageGlobalPrompt

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} day
:canonical: agentsociety.storage.type.StorageGlobalPrompt.day
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageGlobalPrompt.day
```

````

````{py:attribute} t
:canonical: agentsociety.storage.type.StorageGlobalPrompt.t
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageGlobalPrompt.t
```

````

````{py:attribute} prompt
:canonical: agentsociety.storage.type.StorageGlobalPrompt.prompt
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageGlobalPrompt.prompt
```

````

````{py:attribute} created_at
:canonical: agentsociety.storage.type.StorageGlobalPrompt.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageGlobalPrompt.created_at
```

````

`````

`````{py:class} StorageProfile(/, **data: typing.Any)
:canonical: agentsociety.storage.type.StorageProfile

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: agentsociety.storage.type.StorageProfile.id
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageProfile.id
```

````

````{py:attribute} name
:canonical: agentsociety.storage.type.StorageProfile.name
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageProfile.name
```

````

````{py:attribute} profile
:canonical: agentsociety.storage.type.StorageProfile.profile
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageProfile.profile
```

````

`````

`````{py:class} StorageStatus(/, **data: typing.Any)
:canonical: agentsociety.storage.type.StorageStatus

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: agentsociety.storage.type.StorageStatus.id
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.id
```

````

````{py:attribute} day
:canonical: agentsociety.storage.type.StorageStatus.day
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.day
```

````

````{py:attribute} t
:canonical: agentsociety.storage.type.StorageStatus.t
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.t
```

````

````{py:attribute} lng
:canonical: agentsociety.storage.type.StorageStatus.lng
:type: typing.Optional[float]
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.lng
```

````

````{py:attribute} lat
:canonical: agentsociety.storage.type.StorageStatus.lat
:type: typing.Optional[float]
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.lat
```

````

````{py:attribute} parent_id
:canonical: agentsociety.storage.type.StorageStatus.parent_id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.parent_id
```

````

````{py:attribute} friend_ids
:canonical: agentsociety.storage.type.StorageStatus.friend_ids
:type: list[int]
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.friend_ids
```

````

````{py:attribute} action
:canonical: agentsociety.storage.type.StorageStatus.action
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.action
```

````

````{py:attribute} status
:canonical: agentsociety.storage.type.StorageStatus.status
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.status
```

````

````{py:attribute} created_at
:canonical: agentsociety.storage.type.StorageStatus.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.type.StorageStatus.created_at
```

````

`````
