# {py:mod}`en_agentsociety.webapi.models.agent_template`

```{py:module} en_agentsociety.webapi.models.agent_template
```

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DistributionType <en_agentsociety.webapi.models.agent_template.DistributionType>`
  -
* - {py:obj}`ChoiceDistributionConfig <en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig>`
  -
* - {py:obj}`UniformIntDistributionConfig <en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig>`
  -
* - {py:obj}`NormalDistributionConfig <en_agentsociety.webapi.models.agent_template.NormalDistributionConfig>`
  -
* - {py:obj}`AgentTemplateDB <en_agentsociety.webapi.models.agent_template.AgentTemplateDB>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB
    :summary:
    ```
* - {py:obj}`AgentParams <en_agentsociety.webapi.models.agent_template.AgentParams>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams
    :summary:
    ```
* - {py:obj}`ApiAgentTemplate <en_agentsociety.webapi.models.agent_template.ApiAgentTemplate>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.webapi.models.agent_template.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.__all__
    :summary:
    ```
* - {py:obj}`DistributionConfig <en_agentsociety.webapi.models.agent_template.DistributionConfig>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.DistributionConfig
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.webapi.models.agent_template.__all__
:value: >
   ['AgentTemplateDB', 'ApiAgentTemplate']

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.__all__
```

````

`````{py:class} DistributionType()
:canonical: en_agentsociety.webapi.models.agent_template.DistributionType

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

````{py:attribute} CHOICE
:canonical: en_agentsociety.webapi.models.agent_template.DistributionType.CHOICE
:value: >
   'choice'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.DistributionType.CHOICE
```

````

````{py:attribute} UNIFORM_INT
:canonical: en_agentsociety.webapi.models.agent_template.DistributionType.UNIFORM_INT
:value: >
   'uniform_int'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.DistributionType.UNIFORM_INT
```

````

````{py:attribute} NORMAL
:canonical: en_agentsociety.webapi.models.agent_template.DistributionType.NORMAL
:value: >
   'normal'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.DistributionType.NORMAL
```

````

`````

`````{py:class} ChoiceDistributionConfig(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.type
:type: en_agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.type
```

````

````{py:attribute} choices
:canonical: en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.choices
:type: typing.List[str]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.choices
```

````

````{py:attribute} weights
:canonical: en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.weights
:type: typing.List[float]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ChoiceDistributionConfig.weights
```

````

`````

`````{py:class} UniformIntDistributionConfig(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.type
:type: en_agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.type
```

````

````{py:attribute} min_value
:canonical: en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.min_value
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.min_value
```

````

````{py:attribute} max_value
:canonical: en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.max_value
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.UniformIntDistributionConfig.max_value
```

````

`````

`````{py:class} NormalDistributionConfig(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.models.agent_template.NormalDistributionConfig

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} type
:canonical: en_agentsociety.webapi.models.agent_template.NormalDistributionConfig.type
:type: en_agentsociety.webapi.models.agent_template.DistributionType
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.NormalDistributionConfig.type
```

````

````{py:attribute} mean
:canonical: en_agentsociety.webapi.models.agent_template.NormalDistributionConfig.mean
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.NormalDistributionConfig.mean
```

````

````{py:attribute} std
:canonical: en_agentsociety.webapi.models.agent_template.NormalDistributionConfig.std
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.NormalDistributionConfig.std
```

````

`````

````{py:data} DistributionConfig
:canonical: en_agentsociety.webapi.models.agent_template.DistributionConfig
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.DistributionConfig
```

````

`````{py:class} AgentTemplateDB
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB

Bases: {py:obj}`en_agentsociety.webapi.models._base.Base`

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB
```

````{py:attribute} __tablename__
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.__tablename__
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.__tablename__
```

````

````{py:attribute} tenant_id
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.tenant_id
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.tenant_id
```

````

````{py:attribute} id
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.id
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.id
```

````

````{py:attribute} name
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.name
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.name
```

````

````{py:attribute} description
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.description
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.description
```

````

````{py:attribute} agent_type
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_type
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_type
```

````

````{py:attribute} agent_class
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_class
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_class
```

````

````{py:attribute} profile
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.profile
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.profile
```

````

````{py:attribute} agent_params
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_params
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.agent_params
```

````

````{py:attribute} blocks
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.blocks
:type: sqlalchemy.orm.Mapped[typing.Dict]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.blocks
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.created_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.created_at
```

````

````{py:attribute} updated_at
:canonical: en_agentsociety.webapi.models.agent_template.AgentTemplateDB.updated_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentTemplateDB.updated_at
```

````

`````

``````{py:class} AgentParams(**data)
:canonical: en_agentsociety.webapi.models.agent_template.AgentParams

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams.__init__
```

`````{py:class} Config
:canonical: en_agentsociety.webapi.models.agent_template.AgentParams.Config

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams.Config
```

````{py:attribute} extra
:canonical: en_agentsociety.webapi.models.agent_template.AgentParams.Config.extra
:value: >
   'allow'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams.Config.extra
```

````

````{py:attribute} arbitrary_types_allowed
:canonical: en_agentsociety.webapi.models.agent_template.AgentParams.Config.arbitrary_types_allowed
:value: >
   True

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams.Config.arbitrary_types_allowed
```

````

`````

````{py:method} from_dict(data: typing.Dict[str, typing.Any]) -> en_agentsociety.webapi.models.agent_template.AgentParams
:canonical: en_agentsociety.webapi.models.agent_template.AgentParams.from_dict
:classmethod:

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams.from_dict
```

````

````{py:method} to_dict() -> typing.Dict[str, typing.Any]
:canonical: en_agentsociety.webapi.models.agent_template.AgentParams.to_dict

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.AgentParams.to_dict
```

````

``````

``````{py:class} ApiAgentTemplate(/, **data: typing.Any)
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.__init__
```

````{py:attribute} tenant_id
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.tenant_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.tenant_id
```

````

````{py:attribute} id
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.id
```

````

````{py:attribute} name
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.name
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.name
```

````

````{py:attribute} description
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.description
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.description
```

````

````{py:attribute} agent_type
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_type
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_type
```

````

````{py:attribute} agent_class
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_class
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_class
```

````

````{py:attribute} memory_distributions
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.memory_distributions
:type: typing.Dict[str, en_agentsociety.webapi.models.agent_template.DistributionConfig]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.memory_distributions
```

````

````{py:attribute} agent_params
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_params
:type: en_agentsociety.webapi.models.agent_template.AgentParams
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.agent_params
```

````

````{py:attribute} blocks
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.blocks
:type: typing.Dict[str, typing.Dict[str, typing.Any]]
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.blocks
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.created_at
:type: typing.Optional[pydantic.AwareDatetime]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.created_at
```

````

````{py:attribute} updated_at
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.updated_at
:type: typing.Optional[pydantic.AwareDatetime]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.updated_at
```

````

`````{py:class} Config
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config
```

````{py:attribute} from_attributes
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.from_attributes
:value: >
   True

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.from_attributes
```

````

````{py:attribute} json_schema_extra
:canonical: en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.json_schema_extra
:value: >
   None

```{autodoc2-docstring} en_agentsociety.webapi.models.agent_template.ApiAgentTemplate.Config.json_schema_extra
```

````

`````

``````
