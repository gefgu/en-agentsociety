# {py:mod}`en_agentsociety.webapi.app`

```{py:module} en_agentsociety.webapi.app
```

```{autodoc2-docstring} en_agentsociety.webapi.app
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`empty_get_tenant_id <en_agentsociety.webapi.app.empty_get_tenant_id>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.app.empty_get_tenant_id
    :summary:
    ```
* - {py:obj}`_try_load_commercial_features <en_agentsociety.webapi.app._try_load_commercial_features>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.app._try_load_commercial_features
    :summary:
    ```
* - {py:obj}`create_app <en_agentsociety.webapi.app.create_app>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.app.create_app
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.webapi.app.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.app.__all__
    :summary:
    ```
* - {py:obj}`_script_dir <en_agentsociety.webapi.app._script_dir>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.app._script_dir
    :summary:
    ```
* - {py:obj}`_parent_dir <en_agentsociety.webapi.app._parent_dir>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.app._parent_dir
    :summary:
    ```
* - {py:obj}`logger <en_agentsociety.webapi.app.logger>`
  - ```{autodoc2-docstring} en_agentsociety.webapi.app.logger
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.webapi.app.__all__
:value: >
   ['create_app', 'empty_get_tenant_id']

```{autodoc2-docstring} en_agentsociety.webapi.app.__all__
```

````

````{py:data} _script_dir
:canonical: en_agentsociety.webapi.app._script_dir
:value: >
   'dirname(...)'

```{autodoc2-docstring} en_agentsociety.webapi.app._script_dir
```

````

````{py:data} _parent_dir
:canonical: en_agentsociety.webapi.app._parent_dir
:value: >
   'dirname(...)'

```{autodoc2-docstring} en_agentsociety.webapi.app._parent_dir
```

````

````{py:data} logger
:canonical: en_agentsociety.webapi.app.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} en_agentsociety.webapi.app.logger
```

````

````{py:function} empty_get_tenant_id(_: fastapi.Request) -> str
:canonical: en_agentsociety.webapi.app.empty_get_tenant_id
:async:

```{autodoc2-docstring} en_agentsociety.webapi.app.empty_get_tenant_id
```
````

````{py:function} _try_load_commercial_features(app: fastapi.FastAPI, commercial: typing.Dict[str, typing.Any]) -> None
:canonical: en_agentsociety.webapi.app._try_load_commercial_features

```{autodoc2-docstring} en_agentsociety.webapi.app._try_load_commercial_features
```
````

````{py:function} create_app(db_dsn: str, read_only: bool, env: en_agentsociety.configs.EnvConfig, more_state: typing.Dict[str, typing.Any] = {}, commercial: typing.Dict[str, typing.Any] = {})
:canonical: en_agentsociety.webapi.app.create_app

```{autodoc2-docstring} en_agentsociety.webapi.app.create_app
```
````
