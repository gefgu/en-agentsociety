# {py:mod}`agentsociety.executor.kubernetes`

```{py:module} agentsociety.executor.kubernetes
```

```{autodoc2-docstring} agentsociety.executor.kubernetes
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`KubernetesExecutor <agentsociety.executor.kubernetes.KubernetesExecutor>`
  - ```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.executor.kubernetes.__all__>`
  - ```{autodoc2-docstring} agentsociety.executor.kubernetes.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.executor.kubernetes.__all__
:value: >
   ['KubernetesExecutor']

```{autodoc2-docstring} agentsociety.executor.kubernetes.__all__
```

````

`````{py:class} KubernetesExecutor(kube_config_search_paths: list[str])
:canonical: agentsociety.executor.kubernetes.KubernetesExecutor

```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor.__init__
```

````{py:method} init()
:canonical: agentsociety.executor.kubernetes.KubernetesExecutor.init
:async:

```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor.init
```

````

````{py:method} create(config_base64: typing.Optional[str] = None, config_path: typing.Optional[str] = None, callback_url: str = '', callback_auth_token: str = '', tenant_id: str = '')
:canonical: agentsociety.executor.kubernetes.KubernetesExecutor.create
:async:

```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor.create
```

````

````{py:method} delete(tenant_id: str, exp_id: str) -> None
:canonical: agentsociety.executor.kubernetes.KubernetesExecutor.delete
:async:

```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor.delete
```

````

````{py:method} get_logs(tenant_id: str, exp_id: str) -> str
:canonical: agentsociety.executor.kubernetes.KubernetesExecutor.get_logs
:async:

```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor.get_logs
```

````

````{py:method} get_status(tenant_id: str, exp_id: str) -> str
:canonical: agentsociety.executor.kubernetes.KubernetesExecutor.get_status
:async:

```{autodoc2-docstring} agentsociety.executor.kubernetes.KubernetesExecutor.get_status
```

````

`````
