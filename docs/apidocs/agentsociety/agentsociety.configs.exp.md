# {py:mod}`agentsociety.configs.exp`

```{py:module} agentsociety.configs.exp
```

```{autodoc2-docstring} agentsociety.configs.exp
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`WorkflowType <agentsociety.configs.exp.WorkflowType>`
  - ```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType
    :summary:
    ```
* - {py:obj}`WorkflowStepConfig <agentsociety.configs.exp.WorkflowStepConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig
    :summary:
    ```
* - {py:obj}`MetricType <agentsociety.configs.exp.MetricType>`
  - ```{autodoc2-docstring} agentsociety.configs.exp.MetricType
    :summary:
    ```
* - {py:obj}`MetricExtractorConfig <agentsociety.configs.exp.MetricExtractorConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig
    :summary:
    ```
* - {py:obj}`MessageInterceptConfig <agentsociety.configs.exp.MessageInterceptConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig
    :summary:
    ```
* - {py:obj}`ExpConfig <agentsociety.configs.exp.ExpConfig>`
  - ```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.configs.exp.__all__>`
  - ```{autodoc2-docstring} agentsociety.configs.exp.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.configs.exp.__all__
:value: >
   ['WorkflowStepConfig', 'MetricExtractorConfig', 'EnvironmentConfig', 'MessageInterceptConfig', 'ExpC...

```{autodoc2-docstring} agentsociety.configs.exp.__all__
```

````

`````{py:class} WorkflowType()
:canonical: agentsociety.configs.exp.WorkflowType

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.__init__
```

````{py:attribute} STEP
:canonical: agentsociety.configs.exp.WorkflowType.STEP
:value: >
   'step'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.STEP
```

````

````{py:attribute} RUN
:canonical: agentsociety.configs.exp.WorkflowType.RUN
:value: >
   'run'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.RUN
```

````

````{py:attribute} INTERVIEW
:canonical: agentsociety.configs.exp.WorkflowType.INTERVIEW
:value: >
   'interview'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.INTERVIEW
```

````

````{py:attribute} SURVEY
:canonical: agentsociety.configs.exp.WorkflowType.SURVEY
:value: >
   'survey'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.SURVEY
```

````

````{py:attribute} ENVIRONMENT_INTERVENE
:canonical: agentsociety.configs.exp.WorkflowType.ENVIRONMENT_INTERVENE
:value: >
   'environment'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.ENVIRONMENT_INTERVENE
```

````

````{py:attribute} UPDATE_STATE_INTERVENE
:canonical: agentsociety.configs.exp.WorkflowType.UPDATE_STATE_INTERVENE
:value: >
   'update_state'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.UPDATE_STATE_INTERVENE
```

````

````{py:attribute} MESSAGE_INTERVENE
:canonical: agentsociety.configs.exp.WorkflowType.MESSAGE_INTERVENE
:value: >
   'message'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.MESSAGE_INTERVENE
```

````

````{py:attribute} INTERVENE
:canonical: agentsociety.configs.exp.WorkflowType.INTERVENE
:value: >
   'other'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.INTERVENE
```

````

````{py:attribute} FUNCTION
:canonical: agentsociety.configs.exp.WorkflowType.FUNCTION
:value: >
   'function'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowType.FUNCTION
```

````

`````

`````{py:class} WorkflowStepConfig(/, **data: typing.Any)
:canonical: agentsociety.configs.exp.WorkflowStepConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.__init__
```

````{py:attribute} model_config
:canonical: agentsociety.configs.exp.WorkflowStepConfig.model_config
:value: >
   'ConfigDict(...)'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.model_config
```

````

````{py:attribute} type
:canonical: agentsociety.configs.exp.WorkflowStepConfig.type
:type: agentsociety.configs.exp.WorkflowType
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.type
```

````

````{py:attribute} func
:canonical: agentsociety.configs.exp.WorkflowStepConfig.func
:type: typing.Optional[collections.abc.Callable]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.func
```

````

````{py:attribute} days
:canonical: agentsociety.configs.exp.WorkflowStepConfig.days
:type: int
:value: >
   1

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.days
```

````

````{py:attribute} steps
:canonical: agentsociety.configs.exp.WorkflowStepConfig.steps
:type: int
:value: >
   1

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.steps
```

````

````{py:attribute} ticks_per_step
:canonical: agentsociety.configs.exp.WorkflowStepConfig.ticks_per_step
:type: int
:value: >
   300

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.ticks_per_step
```

````

````{py:attribute} target_agent
:canonical: agentsociety.configs.exp.WorkflowStepConfig.target_agent
:type: typing.Optional[list[int]]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.target_agent
```

````

````{py:attribute} interview_message
:canonical: agentsociety.configs.exp.WorkflowStepConfig.interview_message
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.interview_message
```

````

````{py:attribute} survey
:canonical: agentsociety.configs.exp.WorkflowStepConfig.survey
:type: typing.Optional[agentsociety.survey.Survey]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.survey
```

````

````{py:attribute} key
:canonical: agentsociety.configs.exp.WorkflowStepConfig.key
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.key
```

````

````{py:attribute} value
:canonical: agentsociety.configs.exp.WorkflowStepConfig.value
:type: typing.Optional[typing.Any]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.value
```

````

````{py:attribute} intervene_message
:canonical: agentsociety.configs.exp.WorkflowStepConfig.intervene_message
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.intervene_message
```

````

````{py:attribute} description
:canonical: agentsociety.configs.exp.WorkflowStepConfig.description
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.description
```

````

````{py:method} serialize_func(func, info)
:canonical: agentsociety.configs.exp.WorkflowStepConfig.serialize_func

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.serialize_func
```

````

````{py:method} serialize_survey(survey: typing.Optional[agentsociety.survey.Survey], info)
:canonical: agentsociety.configs.exp.WorkflowStepConfig.serialize_survey

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.serialize_survey
```

````

````{py:method} validate_func()
:canonical: agentsociety.configs.exp.WorkflowStepConfig.validate_func

```{autodoc2-docstring} agentsociety.configs.exp.WorkflowStepConfig.validate_func
```

````

`````

`````{py:class} MetricType()
:canonical: agentsociety.configs.exp.MetricType

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

```{autodoc2-docstring} agentsociety.configs.exp.MetricType
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.exp.MetricType.__init__
```

````{py:attribute} FUNCTION
:canonical: agentsociety.configs.exp.MetricType.FUNCTION
:value: >
   'function'

```{autodoc2-docstring} agentsociety.configs.exp.MetricType.FUNCTION
```

````

````{py:attribute} STATE
:canonical: agentsociety.configs.exp.MetricType.STATE
:value: >
   'state'

```{autodoc2-docstring} agentsociety.configs.exp.MetricType.STATE
```

````

`````

`````{py:class} MetricExtractorConfig(/, **data: typing.Any)
:canonical: agentsociety.configs.exp.MetricExtractorConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.__init__
```

````{py:attribute} model_config
:canonical: agentsociety.configs.exp.MetricExtractorConfig.model_config
:value: >
   'ConfigDict(...)'

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.model_config
```

````

````{py:attribute} type
:canonical: agentsociety.configs.exp.MetricExtractorConfig.type
:type: agentsociety.configs.exp.MetricType
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.type
```

````

````{py:attribute} func
:canonical: agentsociety.configs.exp.MetricExtractorConfig.func
:type: typing.Optional[collections.abc.Callable]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.func
```

````

````{py:attribute} step_interval
:canonical: agentsociety.configs.exp.MetricExtractorConfig.step_interval
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.step_interval
```

````

````{py:attribute} target_agent
:canonical: agentsociety.configs.exp.MetricExtractorConfig.target_agent
:type: typing.Optional[list]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.target_agent
```

````

````{py:attribute} key
:canonical: agentsociety.configs.exp.MetricExtractorConfig.key
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.key
```

````

````{py:attribute} method
:canonical: agentsociety.configs.exp.MetricExtractorConfig.method
:type: typing.Optional[typing.Literal[mean, sum, max, min]]
:value: >
   'sum'

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.method
```

````

````{py:attribute} extract_time
:canonical: agentsociety.configs.exp.MetricExtractorConfig.extract_time
:type: int
:value: >
   0

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.extract_time
```

````

````{py:attribute} description
:canonical: agentsociety.configs.exp.MetricExtractorConfig.description
:type: str
:value: >
   'None'

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.description
```

````

````{py:method} validate_target_agent()
:canonical: agentsociety.configs.exp.MetricExtractorConfig.validate_target_agent

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.validate_target_agent
```

````

````{py:method} serialize_func(func, info)
:canonical: agentsociety.configs.exp.MetricExtractorConfig.serialize_func

```{autodoc2-docstring} agentsociety.configs.exp.MetricExtractorConfig.serialize_func
```

````

`````

`````{py:class} MessageInterceptConfig(/, **data: typing.Any)
:canonical: agentsociety.configs.exp.MessageInterceptConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.__init__
```

````{py:attribute} model_config
:canonical: agentsociety.configs.exp.MessageInterceptConfig.model_config
:value: >
   'ConfigDict(...)'

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.model_config
```

````

````{py:attribute} mode
:canonical: agentsociety.configs.exp.MessageInterceptConfig.mode
:type: typing.Optional[typing.Union[typing.Literal[point], typing.Literal[edge]]]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.mode
```

````

````{py:attribute} max_violation_time
:canonical: agentsociety.configs.exp.MessageInterceptConfig.max_violation_time
:type: int
:value: >
   3

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.max_violation_time
```

````

````{py:attribute} blocks
:canonical: agentsociety.configs.exp.MessageInterceptConfig.blocks
:type: list[agentsociety.message.message_interceptor.MessageBlockBase]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.blocks
```

````

````{py:attribute} listener
:canonical: agentsociety.configs.exp.MessageInterceptConfig.listener
:type: typing.Optional[type[agentsociety.message.message_interceptor.MessageBlockListenerBase]]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.listener
```

````

````{py:method} serialize_blocks(blocks, info)
:canonical: agentsociety.configs.exp.MessageInterceptConfig.serialize_blocks

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.serialize_blocks
```

````

````{py:method} serialize_listener(listener, info)
:canonical: agentsociety.configs.exp.MessageInterceptConfig.serialize_listener

```{autodoc2-docstring} agentsociety.configs.exp.MessageInterceptConfig.serialize_listener
```

````

`````

`````{py:class} ExpConfig(/, **data: typing.Any)
:canonical: agentsociety.configs.exp.ExpConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.__init__
```

````{py:attribute} model_config
:canonical: agentsociety.configs.exp.ExpConfig.model_config
:value: >
   'ConfigDict(...)'

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.model_config
```

````

````{py:attribute} name
:canonical: agentsociety.configs.exp.ExpConfig.name
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.name
```

````

````{py:attribute} id
:canonical: agentsociety.configs.exp.ExpConfig.id
:type: uuid.UUID
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.id
```

````

````{py:attribute} workflow
:canonical: agentsociety.configs.exp.ExpConfig.workflow
:type: typing.List[agentsociety.configs.exp.WorkflowStepConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.workflow
```

````

````{py:attribute} environment
:canonical: agentsociety.configs.exp.ExpConfig.environment
:type: agentsociety.environment.EnvironmentConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.environment
```

````

````{py:attribute} message_intercept
:canonical: agentsociety.configs.exp.ExpConfig.message_intercept
:type: typing.Optional[agentsociety.configs.exp.MessageInterceptConfig]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.message_intercept
```

````

````{py:attribute} metric_extractors
:canonical: agentsociety.configs.exp.ExpConfig.metric_extractors
:type: typing.Optional[list[agentsociety.configs.exp.MetricExtractorConfig]]
:value: >
   None

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.metric_extractors
```

````

````{py:method} serialize_id(id, info)
:canonical: agentsociety.configs.exp.ExpConfig.serialize_id

```{autodoc2-docstring} agentsociety.configs.exp.ExpConfig.serialize_id
```

````

`````
