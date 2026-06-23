# {py:mod}`en_agentsociety.storage.model`

```{py:module} en_agentsociety.storage.model
```

```{autodoc2-docstring} en_agentsociety.storage.model
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Experiment <en_agentsociety.storage.model.Experiment>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.Experiment
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`agent_profile <en_agentsociety.storage.model.agent_profile>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.agent_profile
    :summary:
    ```
* - {py:obj}`agent_status <en_agentsociety.storage.model.agent_status>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.agent_status
    :summary:
    ```
* - {py:obj}`agent_survey <en_agentsociety.storage.model.agent_survey>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.agent_survey
    :summary:
    ```
* - {py:obj}`agent_dialog <en_agentsociety.storage.model.agent_dialog>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.agent_dialog
    :summary:
    ```
* - {py:obj}`global_prompt <en_agentsociety.storage.model.global_prompt>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.global_prompt
    :summary:
    ```
* - {py:obj}`pending_dialog <en_agentsociety.storage.model.pending_dialog>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.pending_dialog
    :summary:
    ```
* - {py:obj}`pending_survey <en_agentsociety.storage.model.pending_survey>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.pending_survey
    :summary:
    ```
* - {py:obj}`task_result <en_agentsociety.storage.model.task_result>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.task_result
    :summary:
    ```
* - {py:obj}`metric <en_agentsociety.storage.model.metric>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.metric
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.storage.model.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.storage.model.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.storage.model.__all__
:value: >
   ['agent_profile', 'agent_status', 'agent_survey', 'agent_dialog', 'global_prompt', 'pending_dialog',...

```{autodoc2-docstring} en_agentsociety.storage.model.__all__
```

````

````{py:function} agent_profile(table_name: str)
:canonical: en_agentsociety.storage.model.agent_profile

```{autodoc2-docstring} en_agentsociety.storage.model.agent_profile
```
````

````{py:function} agent_status(table_name: str)
:canonical: en_agentsociety.storage.model.agent_status

```{autodoc2-docstring} en_agentsociety.storage.model.agent_status
```
````

````{py:function} agent_survey(table_name: str)
:canonical: en_agentsociety.storage.model.agent_survey

```{autodoc2-docstring} en_agentsociety.storage.model.agent_survey
```
````

````{py:function} agent_dialog(table_name: str)
:canonical: en_agentsociety.storage.model.agent_dialog

```{autodoc2-docstring} en_agentsociety.storage.model.agent_dialog
```
````

````{py:function} global_prompt(table_name: str)
:canonical: en_agentsociety.storage.model.global_prompt

```{autodoc2-docstring} en_agentsociety.storage.model.global_prompt
```
````

````{py:function} pending_dialog(table_name: str)
:canonical: en_agentsociety.storage.model.pending_dialog

```{autodoc2-docstring} en_agentsociety.storage.model.pending_dialog
```
````

````{py:function} pending_survey(table_name: str)
:canonical: en_agentsociety.storage.model.pending_survey

```{autodoc2-docstring} en_agentsociety.storage.model.pending_survey
```
````

````{py:function} task_result(table_name: str)
:canonical: en_agentsociety.storage.model.task_result

```{autodoc2-docstring} en_agentsociety.storage.model.task_result
```
````

````{py:function} metric(table_name: str)
:canonical: en_agentsociety.storage.model.metric

```{autodoc2-docstring} en_agentsociety.storage.model.metric
```
````

`````{py:class} Experiment
:canonical: en_agentsociety.storage.model.Experiment

Bases: {py:obj}`en_agentsociety.storage._base.Base`

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment
```

````{py:attribute} __tablename__
:canonical: en_agentsociety.storage.model.Experiment.__tablename__
:value: >
   None

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.__tablename__
```

````

````{py:attribute} tenant_id
:canonical: en_agentsociety.storage.model.Experiment.tenant_id
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.tenant_id
```

````

````{py:attribute} id
:canonical: en_agentsociety.storage.model.Experiment.id
:type: sqlalchemy.orm.Mapped[uuid.UUID]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.id
```

````

````{py:attribute} name
:canonical: en_agentsociety.storage.model.Experiment.name
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.name
```

````

````{py:attribute} num_day
:canonical: en_agentsociety.storage.model.Experiment.num_day
:type: sqlalchemy.orm.Mapped[int]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.num_day
```

````

````{py:attribute} status
:canonical: en_agentsociety.storage.model.Experiment.status
:type: sqlalchemy.orm.Mapped[int]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.status
```

````

````{py:attribute} cur_day
:canonical: en_agentsociety.storage.model.Experiment.cur_day
:type: sqlalchemy.orm.Mapped[int]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.cur_day
```

````

````{py:attribute} cur_t
:canonical: en_agentsociety.storage.model.Experiment.cur_t
:type: sqlalchemy.orm.Mapped[float]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.cur_t
```

````

````{py:attribute} config
:canonical: en_agentsociety.storage.model.Experiment.config
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.config
```

````

````{py:attribute} error
:canonical: en_agentsociety.storage.model.Experiment.error
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.error
```

````

````{py:attribute} input_tokens
:canonical: en_agentsociety.storage.model.Experiment.input_tokens
:type: sqlalchemy.orm.Mapped[int]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.input_tokens
```

````

````{py:attribute} output_tokens
:canonical: en_agentsociety.storage.model.Experiment.output_tokens
:type: sqlalchemy.orm.Mapped[int]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.output_tokens
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.storage.model.Experiment.created_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.created_at
```

````

````{py:attribute} updated_at
:canonical: en_agentsociety.storage.model.Experiment.updated_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.updated_at
```

````

````{py:property} agent_profile_tablename
:canonical: en_agentsociety.storage.model.Experiment.agent_profile_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.agent_profile_tablename
```

````

````{py:property} agent_status_tablename
:canonical: en_agentsociety.storage.model.Experiment.agent_status_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.agent_status_tablename
```

````

````{py:property} agent_dialog_tablename
:canonical: en_agentsociety.storage.model.Experiment.agent_dialog_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.agent_dialog_tablename
```

````

````{py:property} agent_survey_tablename
:canonical: en_agentsociety.storage.model.Experiment.agent_survey_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.agent_survey_tablename
```

````

````{py:property} global_prompt_tablename
:canonical: en_agentsociety.storage.model.Experiment.global_prompt_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.global_prompt_tablename
```

````

````{py:property} pending_dialog_tablename
:canonical: en_agentsociety.storage.model.Experiment.pending_dialog_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.pending_dialog_tablename
```

````

````{py:property} pending_survey_tablename
:canonical: en_agentsociety.storage.model.Experiment.pending_survey_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.pending_survey_tablename
```

````

````{py:property} task_result_tablename
:canonical: en_agentsociety.storage.model.Experiment.task_result_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.task_result_tablename
```

````

````{py:property} metric_tablename
:canonical: en_agentsociety.storage.model.Experiment.metric_tablename

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.metric_tablename
```

````

````{py:method} to_dict()
:canonical: en_agentsociety.storage.model.Experiment.to_dict

```{autodoc2-docstring} en_agentsociety.storage.model.Experiment.to_dict
```

````

`````
