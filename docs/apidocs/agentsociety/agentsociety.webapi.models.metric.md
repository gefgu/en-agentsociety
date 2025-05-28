# {py:mod}`agentsociety.webapi.models.metric`

```{py:module} agentsociety.webapi.models.metric
```

```{autodoc2-docstring} agentsociety.webapi.models.metric
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`MLflowRun <agentsociety.webapi.models.metric.MLflowRun>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun
    :summary:
    ```
* - {py:obj}`MLflowMetric <agentsociety.webapi.models.metric.MLflowMetric>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric
    :summary:
    ```
* - {py:obj}`ApiMLflowMetric <agentsociety.webapi.models.metric.ApiMLflowMetric>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.models.metric.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.metric.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.models.metric.__all__
:value: >
   ['MLflowRun', 'MLflowMetric', 'ApiMLflowMetric']

```{autodoc2-docstring} agentsociety.webapi.models.metric.__all__
```

````

`````{py:class} MLflowRun
:canonical: agentsociety.webapi.models.metric.MLflowRun

Bases: {py:obj}`agentsociety.webapi.models._base.BaseNoInit`

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun
```

````{py:attribute} __tablename__
:canonical: agentsociety.webapi.models.metric.MLflowRun.__tablename__
:value: >
   'runs'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.__tablename__
```

````

````{py:attribute} run_uuid
:canonical: agentsociety.webapi.models.metric.MLflowRun.run_uuid
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.run_uuid
```

````

````{py:attribute} name
:canonical: agentsociety.webapi.models.metric.MLflowRun.name
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.name
```

````

````{py:attribute} source_type
:canonical: agentsociety.webapi.models.metric.MLflowRun.source_type
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.source_type
```

````

````{py:attribute} source_name
:canonical: agentsociety.webapi.models.metric.MLflowRun.source_name
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.source_name
```

````

````{py:attribute} entry_point_name
:canonical: agentsociety.webapi.models.metric.MLflowRun.entry_point_name
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.entry_point_name
```

````

````{py:attribute} user_id
:canonical: agentsociety.webapi.models.metric.MLflowRun.user_id
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.user_id
```

````

````{py:attribute} status
:canonical: agentsociety.webapi.models.metric.MLflowRun.status
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.status
```

````

````{py:attribute} start_time
:canonical: agentsociety.webapi.models.metric.MLflowRun.start_time
:type: sqlalchemy.orm.Mapped[typing.Optional[int]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.start_time
```

````

````{py:attribute} end_time
:canonical: agentsociety.webapi.models.metric.MLflowRun.end_time
:type: sqlalchemy.orm.Mapped[typing.Optional[int]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.end_time
```

````

````{py:attribute} source_version
:canonical: agentsociety.webapi.models.metric.MLflowRun.source_version
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.source_version
```

````

````{py:attribute} lifecycle_stage
:canonical: agentsociety.webapi.models.metric.MLflowRun.lifecycle_stage
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.lifecycle_stage
```

````

````{py:attribute} artifact_uri
:canonical: agentsociety.webapi.models.metric.MLflowRun.artifact_uri
:type: sqlalchemy.orm.Mapped[typing.Optional[str]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.artifact_uri
```

````

````{py:attribute} experiment_id
:canonical: agentsociety.webapi.models.metric.MLflowRun.experiment_id
:type: sqlalchemy.orm.Mapped[typing.Optional[int]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.experiment_id
```

````

````{py:attribute} deleted_time
:canonical: agentsociety.webapi.models.metric.MLflowRun.deleted_time
:type: sqlalchemy.orm.Mapped[typing.Optional[int]]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.deleted_time
```

````

````{py:attribute} metrics
:canonical: agentsociety.webapi.models.metric.MLflowRun.metrics
:type: sqlalchemy.orm.Mapped[list[MLflowMetric]]
:value: >
   'relationship(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowRun.metrics
```

````

`````

`````{py:class} MLflowMetric
:canonical: agentsociety.webapi.models.metric.MLflowMetric

Bases: {py:obj}`agentsociety.webapi.models._base.BaseNoInit`

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric
```

````{py:attribute} __tablename__
:canonical: agentsociety.webapi.models.metric.MLflowMetric.__tablename__
:value: >
   'metrics'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.__tablename__
```

````

````{py:attribute} key
:canonical: agentsociety.webapi.models.metric.MLflowMetric.key
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.key
```

````

````{py:attribute} value
:canonical: agentsociety.webapi.models.metric.MLflowMetric.value
:type: sqlalchemy.orm.Mapped[float]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.value
```

````

````{py:attribute} timestamp
:canonical: agentsociety.webapi.models.metric.MLflowMetric.timestamp
:type: sqlalchemy.orm.Mapped[int]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.timestamp
```

````

````{py:attribute} run_uuid
:canonical: agentsociety.webapi.models.metric.MLflowMetric.run_uuid
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.run_uuid
```

````

````{py:attribute} step
:canonical: agentsociety.webapi.models.metric.MLflowMetric.step
:type: sqlalchemy.orm.Mapped[int]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.step
```

````

````{py:attribute} is_nan
:canonical: agentsociety.webapi.models.metric.MLflowMetric.is_nan
:type: sqlalchemy.orm.Mapped[bool]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.is_nan
```

````

````{py:attribute} run
:canonical: agentsociety.webapi.models.metric.MLflowMetric.run
:type: sqlalchemy.orm.Mapped[agentsociety.webapi.models.metric.MLflowRun]
:value: >
   'relationship(...)'

```{autodoc2-docstring} agentsociety.webapi.models.metric.MLflowMetric.run
```

````

`````

``````{py:class} ApiMLflowMetric(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.metric.ApiMLflowMetric

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric.__init__
```

````{py:attribute} key
:canonical: agentsociety.webapi.models.metric.ApiMLflowMetric.key
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric.key
```

````

````{py:attribute} value
:canonical: agentsociety.webapi.models.metric.ApiMLflowMetric.value
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric.value
```

````

````{py:attribute} step
:canonical: agentsociety.webapi.models.metric.ApiMLflowMetric.step
:type: int
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric.step
```

````

````{py:attribute} is_nan
:canonical: agentsociety.webapi.models.metric.ApiMLflowMetric.is_nan
:type: bool
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric.is_nan
```

````

`````{py:class} Config
:canonical: agentsociety.webapi.models.metric.ApiMLflowMetric.Config

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric.Config
```

````{py:attribute} from_attributes
:canonical: agentsociety.webapi.models.metric.ApiMLflowMetric.Config.from_attributes
:value: >
   True

```{autodoc2-docstring} agentsociety.webapi.models.metric.ApiMLflowMetric.Config.from_attributes
```

````

`````

``````
