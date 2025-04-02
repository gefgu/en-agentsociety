# {py:mod}`agentsociety.webapi.app`

```{py:module} agentsociety.webapi.app
```

```{autodoc2-docstring} agentsociety.webapi.app
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`create_app <agentsociety.webapi.app.create_app>`
  - ```{autodoc2-docstring} agentsociety.webapi.app.create_app
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.app.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.app.__all__
    :summary:
    ```
* - {py:obj}`_script_dir <agentsociety.webapi.app._script_dir>`
  - ```{autodoc2-docstring} agentsociety.webapi.app._script_dir
    :summary:
    ```
* - {py:obj}`_parent_dir <agentsociety.webapi.app._parent_dir>`
  - ```{autodoc2-docstring} agentsociety.webapi.app._parent_dir
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.app.__all__
:value: >
   ['create_app']

```{autodoc2-docstring} agentsociety.webapi.app.__all__
```

````

````{py:data} _script_dir
:canonical: agentsociety.webapi.app._script_dir
:value: >
   'dirname(...)'

```{autodoc2-docstring} agentsociety.webapi.app._script_dir
```

````

````{py:data} _parent_dir
:canonical: agentsociety.webapi.app._parent_dir
:value: >
   'dirname(...)'

```{autodoc2-docstring} agentsociety.webapi.app._parent_dir
```

````

````{py:function} create_app(pg_dsn: str, mlflow_url: str, read_only: bool, env: typing.Dict[str, typing.Any], get_tenant_id: typing.Callable[[fastapi.Request], str] = lambda _: '', more_router: typing.Optional[fastapi.APIRouter] = None, session_secret_key: str = 'agentsociety-session')
:canonical: agentsociety.webapi.app.create_app

```{autodoc2-docstring} agentsociety.webapi.app.create_app
```
````
