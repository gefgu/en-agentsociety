# {py:mod}`agentsociety.webapi.models.agent_template`

```{py:module} agentsociety.webapi.models.agent_template
```

```{autodoc2-docstring} agentsociety.webapi.models.agent_template
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DistributionType <agentsociety.webapi.models.agent_template.DistributionType>`
  -
* - {py:obj}`ChoiceDistribution <agentsociety.webapi.models.agent_template.ChoiceDistribution>`
  -
* - {py:obj}`UniformIntDistribution <agentsociety.webapi.models.agent_template.UniformIntDistribution>`
  -
* - {py:obj}`NormalDistribution <agentsociety.webapi.models.agent_template.NormalDistribution>`
  -
* - {py:obj}`ChoiceDistributionConfig <agentsociety.webapi.models.agent_template.ChoiceDistributionConfig>`
  -
* - {py:obj}`UniformIntDistributionConfig <agentsociety.webapi.models.agent_template.UniformIntDistributionConfig>`
  -
* - {py:obj}`NormalDistributionConfig <agentsociety.webapi.models.agent_template.NormalDistributionConfig>`
  -
* - {py:obj}`AgentTemplateDB <agentsociety.webapi.models.agent_template.AgentTemplateDB>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB
    :summary:
    ```
* - {py:obj}`AgentParams <agentsociety.webapi.models.agent_template.AgentParams>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams
    :summary:
    ```
* - {py:obj}`TemplateBlock <agentsociety.webapi.models.agent_template.TemplateBlock>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock
    :summary:
    ```
* - {py:obj}`BaseConfig <agentsociety.webapi.models.agent_template.BaseConfig>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.BaseConfig
    :summary:
    ```
* - {py:obj}`StatesConfig <agentsociety.webapi.models.agent_template.StatesConfig>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.StatesConfig
    :summary:
    ```
* - {py:obj}`ApiAgentTemplate <agentsociety.webapi.models.agent_template.ApiAgentTemplate>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.models.agent_template.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.__all__
    :summary:
    ```
* - {py:obj}`Distribution <agentsociety.webapi.models.agent_template.Distribution>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.Distribution
    :summary:
    ```
* - {py:obj}`DistributionConfig <agentsociety.webapi.models.agent_template.DistributionConfig>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.agent_template.DistributionConfig
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.models.agent_template.__all__
:value: >
   ['AgentTemplateDB', 'TemplateBlock', 'ApiAgentTemplate']

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.__all__
```

````

`````{py:class} DistributionType()
:canonical: agentsociety.webapi.models.agent_template.DistributionType

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

````{py:attribute} CHOICE
:canonical: agentsociety.webapi.models.agent_template.DistributionType.CHOICE
:value: >
   'choice'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.DistributionType.CHOICE
```

````

````{py:attribute} UNIFORM_INT
:canonical: agentsociety.webapi.models.agent_template.DistributionType.UNIFORM_INT
:value: >
   'uniform_int'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.DistributionType.UNIFORM_INT
```

````

````{py:attribute} NORMAL
:canonical: agentsociety.webapi.models.agent_template.DistributionType.NORMAL
:value: >
   'normal'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.DistributionType.NORMAL
```

````

`````

`````{py:class} ChoiceDistribution(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.ChoiceDistribution

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: agentsociety.webapi.models.agent_template.ChoiceDistribution.type
:type: agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ChoiceDistribution.type
```

````

````{py:attribute} params
:canonical: agentsociety.webapi.models.agent_template.ChoiceDistribution.params
:type: typing.Dict[str, typing.Union[typing.List[str], typing.List[float]]]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ChoiceDistribution.params
```

````

`````

`````{py:class} UniformIntDistribution(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.UniformIntDistribution

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: agentsociety.webapi.models.agent_template.UniformIntDistribution.type
:type: agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.UniformIntDistribution.type
```

````

````{py:attribute} params
:canonical: agentsociety.webapi.models.agent_template.UniformIntDistribution.params
:type: typing.Dict[str, int]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.UniformIntDistribution.params
```

````

`````

`````{py:class} NormalDistribution(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.NormalDistribution

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: agentsociety.webapi.models.agent_template.NormalDistribution.type
:type: agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.NormalDistribution.type
```

````

````{py:attribute} params
:canonical: agentsociety.webapi.models.agent_template.NormalDistribution.params
:type: typing.Dict[str, float]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.NormalDistribution.params
```

````

`````

`````{py:class} ChoiceDistributionConfig(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.ChoiceDistributionConfig

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.type
:type: agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.type
```

````

````{py:attribute} choices
:canonical: agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.choices
:type: typing.List[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.choices
```

````

````{py:attribute} weights
:canonical: agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.weights
:type: typing.List[float]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.weights
```

````

`````

`````{py:class} UniformIntDistributionConfig(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.UniformIntDistributionConfig

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.type
:type: agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.type
```

````

````{py:attribute} min_value
:canonical: agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.min_value
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.min_value
```

````

````{py:attribute} max_value
:canonical: agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.max_value
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.max_value
```

````

`````

`````{py:class} NormalDistributionConfig(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.NormalDistributionConfig

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: agentsociety.webapi.models.agent_template.NormalDistributionConfig.type
:type: agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.NormalDistributionConfig.type
```

````

````{py:attribute} mean
:canonical: agentsociety.webapi.models.agent_template.NormalDistributionConfig.mean
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.NormalDistributionConfig.mean
```

````

````{py:attribute} std
:canonical: agentsociety.webapi.models.agent_template.NormalDistributionConfig.std
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.NormalDistributionConfig.std
```

````

`````

````{py:data} Distribution
:canonical: agentsociety.webapi.models.agent_template.Distribution
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.Distribution
```

````

````{py:data} DistributionConfig
:canonical: agentsociety.webapi.models.agent_template.DistributionConfig
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.DistributionConfig
```

````

`````{py:class} AgentTemplateDB
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB

Bases: {py:obj}`agentsociety.webapi.models._base.Base`

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB
```

````{py:attribute} __tablename__
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.__tablename__
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.__tablename__
```

````

````{py:attribute} tenant_id
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.tenant_id
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.tenant_id
```

````

````{py:attribute} id
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.id
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.id
```

````

````{py:attribute} name
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.name
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.name
```

````

````{py:attribute} description
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.description
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.description
```

````

````{py:attribute} profile
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.profile
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.profile
```

````

````{py:attribute} base
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.base
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.base
```

````

````{py:attribute} states
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.states
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.states
```

````

````{py:attribute} agent_params
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_params
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_params
```

````

````{py:attribute} blocks
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.blocks
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.blocks
```

````

````{py:attribute} created_at
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.created_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.created_at
```

````

````{py:attribute} updated_at
:canonical: agentsociety.webapi.models.agent_template.AgentTemplateDB.updated_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentTemplateDB.updated_at
```

````

`````

`````{py:class} AgentParams(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.AgentParams

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.__init__
```

````{py:attribute} enable_cognition
:canonical: agentsociety.webapi.models.agent_template.AgentParams.enable_cognition
:type: bool
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.enable_cognition
```

````

````{py:attribute} UBI
:canonical: agentsociety.webapi.models.agent_template.AgentParams.UBI
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.UBI
```

````

````{py:attribute} num_labor_hours
:canonical: agentsociety.webapi.models.agent_template.AgentParams.num_labor_hours
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.num_labor_hours
```

````

````{py:attribute} productivity_per_labor
:canonical: agentsociety.webapi.models.agent_template.AgentParams.productivity_per_labor
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.productivity_per_labor
```

````

````{py:attribute} time_diff
:canonical: agentsociety.webapi.models.agent_template.AgentParams.time_diff
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.time_diff
```

````

````{py:attribute} max_plan_steps
:canonical: agentsociety.webapi.models.agent_template.AgentParams.max_plan_steps
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.max_plan_steps
```

````

````{py:attribute} need_initialization_prompt
:canonical: agentsociety.webapi.models.agent_template.AgentParams.need_initialization_prompt
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.need_initialization_prompt
```

````

````{py:attribute} need_evaluation_prompt
:canonical: agentsociety.webapi.models.agent_template.AgentParams.need_evaluation_prompt
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.need_evaluation_prompt
```

````

````{py:attribute} need_reflection_prompt
:canonical: agentsociety.webapi.models.agent_template.AgentParams.need_reflection_prompt
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.need_reflection_prompt
```

````

````{py:attribute} plan_generation_prompt
:canonical: agentsociety.webapi.models.agent_template.AgentParams.plan_generation_prompt
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.AgentParams.plan_generation_prompt
```

````

`````

`````{py:class} TemplateBlock(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.TemplateBlock

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock.__init__
```

````{py:attribute} id
:canonical: agentsociety.webapi.models.agent_template.TemplateBlock.id
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock.id
```

````

````{py:attribute} name
:canonical: agentsociety.webapi.models.agent_template.TemplateBlock.name
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock.name
```

````

````{py:attribute} type
:canonical: agentsociety.webapi.models.agent_template.TemplateBlock.type
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock.type
```

````

````{py:attribute} description
:canonical: agentsociety.webapi.models.agent_template.TemplateBlock.description
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock.description
```

````

````{py:attribute} dependencies
:canonical: agentsociety.webapi.models.agent_template.TemplateBlock.dependencies
:type: typing.Dict[str, str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock.dependencies
```

````

````{py:attribute} params
:canonical: agentsociety.webapi.models.agent_template.TemplateBlock.params
:type: typing.Dict[str, typing.Any]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.TemplateBlock.params
```

````

`````

`````{py:class} BaseConfig(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.BaseConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.BaseConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.BaseConfig.__init__
```

````{py:attribute} home
:canonical: agentsociety.webapi.models.agent_template.BaseConfig.home
:type: typing.Dict[str, typing.Any]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.BaseConfig.home
```

````

````{py:attribute} work
:canonical: agentsociety.webapi.models.agent_template.BaseConfig.work
:type: typing.Dict[str, typing.Any]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.BaseConfig.work
```

````

`````

`````{py:class} StatesConfig(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.StatesConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.StatesConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.StatesConfig.__init__
```

````{py:attribute} needs
:canonical: agentsociety.webapi.models.agent_template.StatesConfig.needs
:type: str
:value: >
   'str'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.StatesConfig.needs
```

````

````{py:attribute} plan
:canonical: agentsociety.webapi.models.agent_template.StatesConfig.plan
:type: str
:value: >
   'dict'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.StatesConfig.plan
```

````

````{py:attribute} selfDefine
:canonical: agentsociety.webapi.models.agent_template.StatesConfig.selfDefine
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.StatesConfig.selfDefine
```

````

`````

``````{py:class} ApiAgentTemplate(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.__init__
```

````{py:attribute} tenant_id
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.tenant_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.tenant_id
```

````

````{py:attribute} id
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.id
```

````

````{py:attribute} name
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.name
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.name
```

````

````{py:attribute} description
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.description
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.description
```

````

````{py:attribute} memory_distributions
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.memory_distributions
:type: typing.Dict[str, typing.Union[agentsociety.webapi.models.agent_template.Distribution, agentsociety.webapi.models.agent_template.DistributionConfig]]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.memory_distributions
```

````

````{py:attribute} base
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.base
:type: typing.Dict[str, typing.Dict[str, typing.Any]]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.base
```

````

````{py:attribute} states
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.states
:type: typing.Dict[str, str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.states
```

````

````{py:attribute} agent_params
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_params
:type: agentsociety.webapi.models.agent_template.AgentParams
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_params
```

````

````{py:attribute} blocks
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.blocks
:type: typing.Dict[str, typing.Dict[str, typing.Any]]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.blocks
```

````

````{py:attribute} created_at
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.created_at
:type: typing.Optional[datetime.datetime]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.created_at
```

````

````{py:attribute} updated_at
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.updated_at
:type: typing.Optional[datetime.datetime]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.updated_at
```

````

`````{py:class} Config
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config
```

````{py:attribute} from_attributes
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.from_attributes
:value: >
   True

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.from_attributes
```

````

````{py:attribute} json_schema_extra
:canonical: agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.json_schema_extra
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.json_schema_extra
```

````

`````

``````
