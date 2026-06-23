# {py:mod}`en_agentsociety.commercial`

```{py:module} en_agentsociety.commercial
```

```{autodoc2-docstring} en_agentsociety.commercial
:allowtitles:
```

## Subpackages

```{toctree}
:titlesonly:
:maxdepth: 3

en_agentsociety.commercial.auth
en_agentsociety.commercial.billing
en_agentsociety.commercial.executor
```

## Package Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`is_available <en_agentsociety.commercial.is_available>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.is_available
    :summary:
    ```
* - {py:obj}`get_auth_provider <en_agentsociety.commercial.get_auth_provider>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.get_auth_provider
    :summary:
    ```
* - {py:obj}`get_kubernetes_executor <en_agentsociety.commercial.get_kubernetes_executor>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.get_kubernetes_executor
    :summary:
    ```
* - {py:obj}`get_billing_system <en_agentsociety.commercial.get_billing_system>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.get_billing_system
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <en_agentsociety.commercial.logger>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: en_agentsociety.commercial.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} en_agentsociety.commercial.logger
```

````

````{py:function} is_available() -> bool
:canonical: en_agentsociety.commercial.is_available

```{autodoc2-docstring} en_agentsociety.commercial.is_available
```
````

````{py:function} get_auth_provider(config: typing.Dict[str, typing.Any])
:canonical: en_agentsociety.commercial.get_auth_provider

```{autodoc2-docstring} en_agentsociety.commercial.get_auth_provider
```
````

````{py:function} get_kubernetes_executor(config: typing.Dict[str, typing.Any])
:canonical: en_agentsociety.commercial.get_kubernetes_executor

```{autodoc2-docstring} en_agentsociety.commercial.get_kubernetes_executor
```
````

````{py:function} get_billing_system(config: typing.Dict[str, typing.Any])
:canonical: en_agentsociety.commercial.get_billing_system

```{autodoc2-docstring} en_agentsociety.commercial.get_billing_system
```
````
