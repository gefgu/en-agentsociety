# {py:mod}`en_agentsociety.storage.type`

```{py:module} en_agentsociety.storage.type
```

```{autodoc2-docstring} en_agentsociety.storage.type
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`StorageExpInfo <en_agentsociety.storage.type.StorageExpInfo>`
  -
* - {py:obj}`StorageSurvey <en_agentsociety.storage.type.StorageSurvey>`
  -
* - {py:obj}`StorageDialogType <en_agentsociety.storage.type.StorageDialogType>`
  - ```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialogType
    :summary:
    ```
* - {py:obj}`StorageDialog <en_agentsociety.storage.type.StorageDialog>`
  -
* - {py:obj}`StorageGlobalPrompt <en_agentsociety.storage.type.StorageGlobalPrompt>`
  -
* - {py:obj}`StorageProfile <en_agentsociety.storage.type.StorageProfile>`
  -
* - {py:obj}`StorageStatus <en_agentsociety.storage.type.StorageStatus>`
  -
* - {py:obj}`StoragePendingDialog <en_agentsociety.storage.type.StoragePendingDialog>`
  - ```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog
    :summary:
    ```
* - {py:obj}`StoragePendingSurvey <en_agentsociety.storage.type.StoragePendingSurvey>`
  - ```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey
    :summary:
    ```
* - {py:obj}`StorageTaskResult <en_agentsociety.storage.type.StorageTaskResult>`
  -
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.storage.type.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.storage.type.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.storage.type.__all__
:value: >
   ['StorageSurvey', 'StorageDialogType', 'StorageDialog', 'StorageGlobalPrompt', 'StorageProfile', 'St...

```{autodoc2-docstring} en_agentsociety.storage.type.__all__
```

````

`````{py:class} StorageExpInfo(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StorageExpInfo

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} tenant_id
:canonical: en_agentsociety.storage.type.StorageExpInfo.tenant_id
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.tenant_id
```

````

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StorageExpInfo.id
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.id
```

````

````{py:attribute} name
:canonical: en_agentsociety.storage.type.StorageExpInfo.name
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.name
```

````

````{py:attribute} num_day
:canonical: en_agentsociety.storage.type.StorageExpInfo.num_day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.num_day
```

````

````{py:attribute} status
:canonical: en_agentsociety.storage.type.StorageExpInfo.status
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.status
```

````

````{py:attribute} cur_day
:canonical: en_agentsociety.storage.type.StorageExpInfo.cur_day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.cur_day
```

````

````{py:attribute} cur_t
:canonical: en_agentsociety.storage.type.StorageExpInfo.cur_t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.cur_t
```

````

````{py:attribute} config
:canonical: en_agentsociety.storage.type.StorageExpInfo.config
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.config
```

````

````{py:attribute} error
:canonical: en_agentsociety.storage.type.StorageExpInfo.error
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.error
```

````

````{py:attribute} input_tokens
:canonical: en_agentsociety.storage.type.StorageExpInfo.input_tokens
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.input_tokens
```

````

````{py:attribute} output_tokens
:canonical: en_agentsociety.storage.type.StorageExpInfo.output_tokens
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.output_tokens
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StorageExpInfo.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.created_at
```

````

````{py:attribute} updated_at
:canonical: en_agentsociety.storage.type.StorageExpInfo.updated_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageExpInfo.updated_at
```

````

`````

`````{py:class} StorageSurvey(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StorageSurvey

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StorageSurvey.id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageSurvey.id
```

````

````{py:attribute} day
:canonical: en_agentsociety.storage.type.StorageSurvey.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageSurvey.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.storage.type.StorageSurvey.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageSurvey.t
```

````

````{py:attribute} survey_id
:canonical: en_agentsociety.storage.type.StorageSurvey.survey_id
:type: uuid.UUID
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageSurvey.survey_id
```

````

````{py:attribute} result
:canonical: en_agentsociety.storage.type.StorageSurvey.result
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageSurvey.result
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StorageSurvey.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageSurvey.created_at
```

````

`````

`````{py:class} StorageDialogType()
:canonical: en_agentsociety.storage.type.StorageDialogType

Bases: {py:obj}`enum.IntEnum`

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialogType
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialogType.__init__
```

````{py:attribute} Thought
:canonical: en_agentsociety.storage.type.StorageDialogType.Thought
:value: >
   0

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialogType.Thought
```

````

````{py:attribute} Talk
:canonical: en_agentsociety.storage.type.StorageDialogType.Talk
:value: >
   1

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialogType.Talk
```

````

````{py:attribute} User
:canonical: en_agentsociety.storage.type.StorageDialogType.User
:value: >
   2

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialogType.User
```

````

`````

`````{py:class} StorageDialog(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StorageDialog

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StorageDialog.id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialog.id
```

````

````{py:attribute} day
:canonical: en_agentsociety.storage.type.StorageDialog.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialog.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.storage.type.StorageDialog.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialog.t
```

````

````{py:attribute} type
:canonical: en_agentsociety.storage.type.StorageDialog.type
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialog.type
```

````

````{py:attribute} speaker
:canonical: en_agentsociety.storage.type.StorageDialog.speaker
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialog.speaker
```

````

````{py:attribute} content
:canonical: en_agentsociety.storage.type.StorageDialog.content
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialog.content
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StorageDialog.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageDialog.created_at
```

````

`````

`````{py:class} StorageGlobalPrompt(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StorageGlobalPrompt

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} day
:canonical: en_agentsociety.storage.type.StorageGlobalPrompt.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageGlobalPrompt.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.storage.type.StorageGlobalPrompt.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageGlobalPrompt.t
```

````

````{py:attribute} prompt
:canonical: en_agentsociety.storage.type.StorageGlobalPrompt.prompt
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageGlobalPrompt.prompt
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StorageGlobalPrompt.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageGlobalPrompt.created_at
```

````

`````

`````{py:class} StorageProfile(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StorageProfile

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StorageProfile.id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageProfile.id
```

````

````{py:attribute} name
:canonical: en_agentsociety.storage.type.StorageProfile.name
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageProfile.name
```

````

````{py:attribute} profile
:canonical: en_agentsociety.storage.type.StorageProfile.profile
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageProfile.profile
```

````

`````

`````{py:class} StorageStatus(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StorageStatus

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StorageStatus.id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.id
```

````

````{py:attribute} day
:canonical: en_agentsociety.storage.type.StorageStatus.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.storage.type.StorageStatus.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.t
```

````

````{py:attribute} lng
:canonical: en_agentsociety.storage.type.StorageStatus.lng
:type: typing.Optional[float]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.lng
```

````

````{py:attribute} lat
:canonical: en_agentsociety.storage.type.StorageStatus.lat
:type: typing.Optional[float]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.lat
```

````

````{py:attribute} parent_id
:canonical: en_agentsociety.storage.type.StorageStatus.parent_id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.parent_id
```

````

````{py:attribute} action
:canonical: en_agentsociety.storage.type.StorageStatus.action
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.action
```

````

````{py:attribute} status
:canonical: en_agentsociety.storage.type.StorageStatus.status
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.status
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StorageStatus.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageStatus.created_at
```

````

`````

`````{py:class} StoragePendingDialog(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StoragePendingDialog

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.__init__
```

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StoragePendingDialog.id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.id
```

````

````{py:attribute} agent_id
:canonical: en_agentsociety.storage.type.StoragePendingDialog.agent_id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.agent_id
```

````

````{py:attribute} day
:canonical: en_agentsociety.storage.type.StoragePendingDialog.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.storage.type.StoragePendingDialog.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.t
```

````

````{py:attribute} content
:canonical: en_agentsociety.storage.type.StoragePendingDialog.content
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.content
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StoragePendingDialog.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.created_at
```

````

````{py:attribute} processed
:canonical: en_agentsociety.storage.type.StoragePendingDialog.processed
:type: bool
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingDialog.processed
```

````

`````

`````{py:class} StoragePendingSurvey(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StoragePendingSurvey

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.__init__
```

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.id
```

````

````{py:attribute} agent_id
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.agent_id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.agent_id
```

````

````{py:attribute} day
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.t
```

````

````{py:attribute} survey_id
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.survey_id
:type: uuid.UUID
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.survey_id
```

````

````{py:attribute} data
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.data
:type: dict
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.data
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.created_at
```

````

````{py:attribute} processed
:canonical: en_agentsociety.storage.type.StoragePendingSurvey.processed
:type: bool
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StoragePendingSurvey.processed
```

````

`````

`````{py:class} StorageTaskResult(/, **data: typing.Any)
:canonical: en_agentsociety.storage.type.StorageTaskResult

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: en_agentsociety.storage.type.StorageTaskResult.id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageTaskResult.id
```

````

````{py:attribute} agent_id
:canonical: en_agentsociety.storage.type.StorageTaskResult.agent_id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageTaskResult.agent_id
```

````

````{py:attribute} context
:canonical: en_agentsociety.storage.type.StorageTaskResult.context
:type: dict
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageTaskResult.context
```

````

````{py:attribute} ground_truth
:canonical: en_agentsociety.storage.type.StorageTaskResult.ground_truth
:type: dict
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageTaskResult.ground_truth
```

````

````{py:attribute} result
:canonical: en_agentsociety.storage.type.StorageTaskResult.result
:type: dict
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageTaskResult.result
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.type.StorageTaskResult.created_at
:type: datetime.datetime
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.type.StorageTaskResult.created_at
```

````

`````
