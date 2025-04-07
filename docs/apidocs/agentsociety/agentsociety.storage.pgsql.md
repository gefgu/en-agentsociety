# {py:mod}`agentsociety.storage.pgsql`

```{py:module} agentsociety.storage.pgsql
```

```{autodoc2-docstring} agentsociety.storage.pgsql
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`PostgreSQLConfig <agentsociety.storage.pgsql.PostgreSQLConfig>`
  - ```{autodoc2-docstring} agentsociety.storage.pgsql.PostgreSQLConfig
    :summary:
    ```
* - {py:obj}`PgWriter <agentsociety.storage.pgsql.PgWriter>`
  - ```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_migrate_experiment_table <agentsociety.storage.pgsql._migrate_experiment_table>`
  - ```{autodoc2-docstring} agentsociety.storage.pgsql._migrate_experiment_table
    :summary:
    ```
* - {py:obj}`_create_pg_tables <agentsociety.storage.pgsql._create_pg_tables>`
  - ```{autodoc2-docstring} agentsociety.storage.pgsql._create_pg_tables
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.storage.pgsql.__all__>`
  - ```{autodoc2-docstring} agentsociety.storage.pgsql.__all__
    :summary:
    ```
* - {py:obj}`TABLE_PREFIX <agentsociety.storage.pgsql.TABLE_PREFIX>`
  - ```{autodoc2-docstring} agentsociety.storage.pgsql.TABLE_PREFIX
    :summary:
    ```
* - {py:obj}`PGSQL_DICT <agentsociety.storage.pgsql.PGSQL_DICT>`
  - ```{autodoc2-docstring} agentsociety.storage.pgsql.PGSQL_DICT
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.storage.pgsql.__all__
:value: >
   ['PgWriter', 'PostgreSQLConfig']

```{autodoc2-docstring} agentsociety.storage.pgsql.__all__
```

````

````{py:data} TABLE_PREFIX
:canonical: agentsociety.storage.pgsql.TABLE_PREFIX
:value: >
   'as_'

```{autodoc2-docstring} agentsociety.storage.pgsql.TABLE_PREFIX
```

````

````{py:data} PGSQL_DICT
:canonical: agentsociety.storage.pgsql.PGSQL_DICT
:type: dict[str, list[typing.Any]]
:value: >
   None

```{autodoc2-docstring} agentsociety.storage.pgsql.PGSQL_DICT
```

````

````{py:function} _migrate_experiment_table(dsn: str)
:canonical: agentsociety.storage.pgsql._migrate_experiment_table

```{autodoc2-docstring} agentsociety.storage.pgsql._migrate_experiment_table
```
````

````{py:function} _create_pg_tables(exp_id: str, dsn: str)
:canonical: agentsociety.storage.pgsql._create_pg_tables

```{autodoc2-docstring} agentsociety.storage.pgsql._create_pg_tables
```
````

`````{py:class} PostgreSQLConfig(/, **data: typing.Any)
:canonical: agentsociety.storage.pgsql.PostgreSQLConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.storage.pgsql.PostgreSQLConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.storage.pgsql.PostgreSQLConfig.__init__
```

````{py:attribute} enabled
:canonical: agentsociety.storage.pgsql.PostgreSQLConfig.enabled
:type: bool
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.storage.pgsql.PostgreSQLConfig.enabled
```

````

````{py:attribute} dsn
:canonical: agentsociety.storage.pgsql.PostgreSQLConfig.dsn
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.storage.pgsql.PostgreSQLConfig.dsn
```

````

````{py:attribute} num_workers
:canonical: agentsociety.storage.pgsql.PostgreSQLConfig.num_workers
:type: typing.Union[int, typing.Literal[auto]]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.storage.pgsql.PostgreSQLConfig.num_workers
```

````

````{py:method} validate_dsn()
:canonical: agentsociety.storage.pgsql.PostgreSQLConfig.validate_dsn

```{autodoc2-docstring} agentsociety.storage.pgsql.PostgreSQLConfig.validate_dsn
```

````

`````

`````{py:class} PgWriter(tenant_id: str, exp_id: str, dsn: str, init: bool)
:canonical: agentsociety.storage.pgsql.PgWriter

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter.__init__
```

````{py:method} write_dialogs(rows: list[agentsociety.storage.type.StorageDialog])
:canonical: agentsociety.storage.pgsql.PgWriter.write_dialogs
:async:

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter.write_dialogs
```

````

````{py:method} write_statuses(rows: list[agentsociety.storage.type.StorageStatus])
:canonical: agentsociety.storage.pgsql.PgWriter.write_statuses
:async:

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter.write_statuses
```

````

````{py:method} write_profiles(rows: list[agentsociety.storage.type.StorageProfile])
:canonical: agentsociety.storage.pgsql.PgWriter.write_profiles
:async:

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter.write_profiles
```

````

````{py:method} write_surveys(rows: list[agentsociety.storage.type.StorageSurvey])
:canonical: agentsociety.storage.pgsql.PgWriter.write_surveys
:async:

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter.write_surveys
```

````

````{py:method} write_global_prompt(prompt_info: agentsociety.storage.type.StorageGlobalPrompt)
:canonical: agentsociety.storage.pgsql.PgWriter.write_global_prompt
:async:

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter.write_global_prompt
```

````

````{py:method} update_exp_info(exp_info: agentsociety.storage.type.StorageExpInfo)
:canonical: agentsociety.storage.pgsql.PgWriter.update_exp_info
:async:

```{autodoc2-docstring} agentsociety.storage.pgsql.PgWriter.update_exp_info
```

````

`````
