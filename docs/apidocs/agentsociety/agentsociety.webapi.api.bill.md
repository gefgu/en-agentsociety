# {py:mod}`agentsociety.webapi.api.bill`

```{py:module} agentsociety.webapi.api.bill
```

```{autodoc2-docstring} agentsociety.webapi.api.bill
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_account <agentsociety.webapi.api.bill.get_account>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.bill.get_account
    :summary:
    ```
* - {py:obj}`list_bills <agentsociety.webapi.api.bill.list_bills>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.bill.list_bills
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.api.bill.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.bill.__all__
    :summary:
    ```
* - {py:obj}`router <agentsociety.webapi.api.bill.router>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.bill.router
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.api.bill.__all__
:value: >
   ['router']

```{autodoc2-docstring} agentsociety.webapi.api.bill.__all__
```

````

````{py:data} router
:canonical: agentsociety.webapi.api.bill.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} agentsociety.webapi.api.bill.router
```

````

````{py:function} get_account(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.bill.ApiAccount]
:canonical: agentsociety.webapi.api.bill.get_account
:async:

```{autodoc2-docstring} agentsociety.webapi.api.bill.get_account
```
````

````{py:function} list_bills(request: fastapi.Request, item: typing.Optional[str] = None, skip: int = 0, limit: int = 100) -> agentsociety.webapi.models.ApiPaginatedResponseWrapper[agentsociety.webapi.models.bill.ApiBill]
:canonical: agentsociety.webapi.api.bill.list_bills
:async:

```{autodoc2-docstring} agentsociety.webapi.api.bill.list_bills
```
````
