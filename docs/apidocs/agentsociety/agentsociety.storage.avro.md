# {py:mod}`agentsociety.storage.avro`

```{py:module} agentsociety.storage.avro
```

```{autodoc2-docstring} agentsociety.storage.avro
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AvroConfig <agentsociety.storage.avro.AvroConfig>`
  -
* - {py:obj}`AvroSaver <agentsociety.storage.avro.AvroSaver>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.storage.avro.__all__>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.__all__
    :summary:
    ```
* - {py:obj}`PROFILE_SCHEMA <agentsociety.storage.avro.PROFILE_SCHEMA>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.PROFILE_SCHEMA
    :summary:
    ```
* - {py:obj}`DIALOG_SCHEMA <agentsociety.storage.avro.DIALOG_SCHEMA>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.DIALOG_SCHEMA
    :summary:
    ```
* - {py:obj}`GLOBAL_PROMPT_SCHEMA <agentsociety.storage.avro.GLOBAL_PROMPT_SCHEMA>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.GLOBAL_PROMPT_SCHEMA
    :summary:
    ```
* - {py:obj}`STATUS_SCHEMA <agentsociety.storage.avro.STATUS_SCHEMA>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.STATUS_SCHEMA
    :summary:
    ```
* - {py:obj}`SURVEY_SCHEMA <agentsociety.storage.avro.SURVEY_SCHEMA>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.SURVEY_SCHEMA
    :summary:
    ```
* - {py:obj}`SCHEMA_MAP <agentsociety.storage.avro.SCHEMA_MAP>`
  - ```{autodoc2-docstring} agentsociety.storage.avro.SCHEMA_MAP
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.storage.avro.__all__
:value: >
   ['AvroSaver', 'AvroConfig']

```{autodoc2-docstring} agentsociety.storage.avro.__all__
```

````

`````{py:class} AvroConfig(/, **data: typing.Any)
:canonical: agentsociety.storage.avro.AvroConfig

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} enabled
:canonical: agentsociety.storage.avro.AvroConfig.enabled
:type: bool
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.storage.avro.AvroConfig.enabled
```

````

`````

````{py:data} PROFILE_SCHEMA
:canonical: agentsociety.storage.avro.PROFILE_SCHEMA
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.avro.PROFILE_SCHEMA
```

````

````{py:data} DIALOG_SCHEMA
:canonical: agentsociety.storage.avro.DIALOG_SCHEMA
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.avro.DIALOG_SCHEMA
```

````

````{py:data} GLOBAL_PROMPT_SCHEMA
:canonical: agentsociety.storage.avro.GLOBAL_PROMPT_SCHEMA
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.avro.GLOBAL_PROMPT_SCHEMA
```

````

````{py:data} STATUS_SCHEMA
:canonical: agentsociety.storage.avro.STATUS_SCHEMA
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.avro.STATUS_SCHEMA
```

````

````{py:data} SURVEY_SCHEMA
:canonical: agentsociety.storage.avro.SURVEY_SCHEMA
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.avro.SURVEY_SCHEMA
```

````

````{py:data} SCHEMA_MAP
:canonical: agentsociety.storage.avro.SCHEMA_MAP
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.avro.SCHEMA_MAP
```

````

`````{py:class} AvroSaver(config: agentsociety.storage.avro.AvroConfig, home_dir: str, tenant_id: str, exp_id: str, group_id: typing.Optional[str])
:canonical: agentsociety.storage.avro.AvroSaver

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.__init__
```

````{py:property} enabled
:canonical: agentsociety.storage.avro.AvroSaver.enabled

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.enabled
```

````

````{py:property} exp_info_file
:canonical: agentsociety.storage.avro.AvroSaver.exp_info_file

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.exp_info_file
```

````

````{py:method} close()
:canonical: agentsociety.storage.avro.AvroSaver.close

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.close
```

````

````{py:method} _check(is_group: bool = True)
:canonical: agentsociety.storage.avro.AvroSaver._check

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver._check
```

````

````{py:method} append_surveys(surveys: typing.List[agentsociety.storage.type.StorageSurvey])
:canonical: agentsociety.storage.avro.AvroSaver.append_surveys

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.append_surveys
```

````

````{py:method} append_dialogs(dialogs: typing.List[agentsociety.storage.type.StorageDialog])
:canonical: agentsociety.storage.avro.AvroSaver.append_dialogs

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.append_dialogs
```

````

````{py:method} append_profiles(profiles: typing.List[agentsociety.storage.type.StorageProfile])
:canonical: agentsociety.storage.avro.AvroSaver.append_profiles

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.append_profiles
```

````

````{py:method} append_statuses(statuses: typing.List[agentsociety.storage.type.StorageStatus])
:canonical: agentsociety.storage.avro.AvroSaver.append_statuses

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.append_statuses
```

````

````{py:method} append_global_prompt(global_prompt: agentsociety.storage.type.StorageGlobalPrompt)
:canonical: agentsociety.storage.avro.AvroSaver.append_global_prompt

```{autodoc2-docstring} agentsociety.storage.avro.AvroSaver.append_global_prompt
```

````

`````
