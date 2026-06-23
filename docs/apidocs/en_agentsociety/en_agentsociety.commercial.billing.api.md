# {py:mod}`en_agentsociety.commercial.billing.api`

```{py:module} en_agentsociety.commercial.billing.api
```

```{autodoc2-docstring} en_agentsociety.commercial.billing.api
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_account <en_agentsociety.commercial.billing.api.get_account>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.billing.api.get_account
    :summary:
    ```
* - {py:obj}`list_bills <en_agentsociety.commercial.billing.api.list_bills>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.billing.api.list_bills
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.commercial.billing.api.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.billing.api.__all__
    :summary:
    ```
* - {py:obj}`router <en_agentsociety.commercial.billing.api.router>`
  - ```{autodoc2-docstring} en_agentsociety.commercial.billing.api.router
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.commercial.billing.api.__all__
:value: >
   ['router']

```{autodoc2-docstring} en_agentsociety.commercial.billing.api.__all__
```

````

````{py:data} router
:canonical: en_agentsociety.commercial.billing.api.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} en_agentsociety.commercial.billing.api.router
```

````

````{py:function} get_account(request: fastapi.Request) -> en_agentsociety.webapi.models.ApiResponseWrapper[en_agentsociety.commercial.billing.models.ApiAccount]
:canonical: en_agentsociety.commercial.billing.api.get_account
:async:

```{autodoc2-docstring} en_agentsociety.commercial.billing.api.get_account
```
````

````{py:function} list_bills(request: fastapi.Request, item: typing.Optional[str] = None, skip: int = 0, limit: int = 100) -> en_agentsociety.webapi.models.ApiPaginatedResponseWrapper[en_agentsociety.commercial.billing.models.ApiBill]
:canonical: en_agentsociety.commercial.billing.api.list_bills
:async:

```{autodoc2-docstring} en_agentsociety.commercial.billing.api.list_bills
```
````
