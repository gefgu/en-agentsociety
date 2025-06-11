# {py:mod}`agentsociety.webapi.models.bill`

```{py:module} agentsociety.webapi.models.bill
```

```{autodoc2-docstring} agentsociety.webapi.models.bill
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ItemEnum <agentsociety.webapi.models.bill.ItemEnum>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.bill.ItemEnum
    :summary:
    ```
* - {py:obj}`Account <agentsociety.webapi.models.bill.Account>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.bill.Account
    :summary:
    ```
* - {py:obj}`Bill <agentsociety.webapi.models.bill.Bill>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill
    :summary:
    ```
* - {py:obj}`ApiAccount <agentsociety.webapi.models.bill.ApiAccount>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount
    :summary:
    ```
* - {py:obj}`ApiBill <agentsociety.webapi.models.bill.ApiBill>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.models.bill.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.models.bill.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.models.bill.__all__
:value: >
   ['Bill', 'ApiBill', 'Account', 'ApiAccount', 'ItemEnum']

```{autodoc2-docstring} agentsociety.webapi.models.bill.__all__
```

````

`````{py:class} ItemEnum()
:canonical: agentsociety.webapi.models.bill.ItemEnum

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

```{autodoc2-docstring} agentsociety.webapi.models.bill.ItemEnum
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.bill.ItemEnum.__init__
```

````{py:attribute} RECHARGE
:canonical: agentsociety.webapi.models.bill.ItemEnum.RECHARGE
:value: >
   'recharge'

```{autodoc2-docstring} agentsociety.webapi.models.bill.ItemEnum.RECHARGE
```

````

````{py:attribute} LLM_INPUT_TOKEN
:canonical: agentsociety.webapi.models.bill.ItemEnum.LLM_INPUT_TOKEN
:value: >
   'llm_input_token'

```{autodoc2-docstring} agentsociety.webapi.models.bill.ItemEnum.LLM_INPUT_TOKEN
```

````

````{py:attribute} LLM_OUTPUT_TOKEN
:canonical: agentsociety.webapi.models.bill.ItemEnum.LLM_OUTPUT_TOKEN
:value: >
   'llm_output_token'

```{autodoc2-docstring} agentsociety.webapi.models.bill.ItemEnum.LLM_OUTPUT_TOKEN
```

````

````{py:attribute} RUNTIME
:canonical: agentsociety.webapi.models.bill.ItemEnum.RUNTIME
:value: >
   'run_time'

```{autodoc2-docstring} agentsociety.webapi.models.bill.ItemEnum.RUNTIME
```

````

`````

`````{py:class} Account
:canonical: agentsociety.webapi.models.bill.Account

Bases: {py:obj}`agentsociety.webapi.models._base.Base`

```{autodoc2-docstring} agentsociety.webapi.models.bill.Account
```

````{py:attribute} __tablename__
:canonical: agentsociety.webapi.models.bill.Account.__tablename__
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.Account.__tablename__
```

````

````{py:attribute} tenant_id
:canonical: agentsociety.webapi.models.bill.Account.tenant_id
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Account.tenant_id
```

````

````{py:attribute} balance
:canonical: agentsociety.webapi.models.bill.Account.balance
:type: sqlalchemy.orm.Mapped[agentsociety.webapi.models._base.MoneyDecimal]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Account.balance
```

````

````{py:attribute} created_at
:canonical: agentsociety.webapi.models.bill.Account.created_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Account.created_at
```

````

````{py:attribute} updated_at
:canonical: agentsociety.webapi.models.bill.Account.updated_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Account.updated_at
```

````

`````

`````{py:class} Bill
:canonical: agentsociety.webapi.models.bill.Bill

Bases: {py:obj}`agentsociety.webapi.models._base.Base`

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill
```

````{py:attribute} __tablename__
:canonical: agentsociety.webapi.models.bill.Bill.__tablename__
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.__tablename__
```

````

````{py:attribute} tenant_id
:canonical: agentsociety.webapi.models.bill.Bill.tenant_id
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.tenant_id
```

````

````{py:attribute} id
:canonical: agentsociety.webapi.models.bill.Bill.id
:type: sqlalchemy.orm.Mapped[uuid.UUID]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.id
```

````

````{py:attribute} related_exp_id
:canonical: agentsociety.webapi.models.bill.Bill.related_exp_id
:type: sqlalchemy.orm.Mapped[uuid.UUID]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.related_exp_id
```

````

````{py:attribute} item
:canonical: agentsociety.webapi.models.bill.Bill.item
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.item
```

````

````{py:attribute} amount
:canonical: agentsociety.webapi.models.bill.Bill.amount
:type: sqlalchemy.orm.Mapped[agentsociety.webapi.models._base.MoneyDecimal]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.amount
```

````

````{py:attribute} unit_price
:canonical: agentsociety.webapi.models.bill.Bill.unit_price
:type: sqlalchemy.orm.Mapped[agentsociety.webapi.models._base.MoneyDecimal]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.unit_price
```

````

````{py:attribute} quantity
:canonical: agentsociety.webapi.models.bill.Bill.quantity
:type: sqlalchemy.orm.Mapped[float]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.quantity
```

````

````{py:attribute} description
:canonical: agentsociety.webapi.models.bill.Bill.description
:type: sqlalchemy.orm.Mapped[str]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.description
```

````

````{py:attribute} created_at
:canonical: agentsociety.webapi.models.bill.Bill.created_at
:type: sqlalchemy.orm.Mapped[datetime.datetime]
:value: >
   'mapped_column(...)'

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.created_at
```

````

````{py:attribute} __table_args__
:canonical: agentsociety.webapi.models.bill.Bill.__table_args__
:value: >
   ()

```{autodoc2-docstring} agentsociety.webapi.models.bill.Bill.__table_args__
```

````

`````

``````{py:class} ApiAccount(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.bill.ApiAccount

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount.__init__
```

````{py:attribute} balance
:canonical: agentsociety.webapi.models.bill.ApiAccount.balance
:type: decimal.Decimal
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount.balance
```

````

````{py:attribute} created_at
:canonical: agentsociety.webapi.models.bill.ApiAccount.created_at
:type: pydantic.AwareDatetime
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount.created_at
```

````

````{py:attribute} updated_at
:canonical: agentsociety.webapi.models.bill.ApiAccount.updated_at
:type: pydantic.AwareDatetime
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount.updated_at
```

````

`````{py:class} Config
:canonical: agentsociety.webapi.models.bill.ApiAccount.Config

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount.Config
```

````{py:attribute} from_attributes
:canonical: agentsociety.webapi.models.bill.ApiAccount.Config.from_attributes
:value: >
   True

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiAccount.Config.from_attributes
```

````

`````

``````

``````{py:class} ApiBill(/, **data: typing.Any)
:canonical: agentsociety.webapi.models.bill.ApiBill

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.__init__
```

````{py:attribute} id
:canonical: agentsociety.webapi.models.bill.ApiBill.id
:type: uuid.UUID
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.id
```

````

````{py:attribute} related_exp_id
:canonical: agentsociety.webapi.models.bill.ApiBill.related_exp_id
:type: typing.Optional[uuid.UUID]
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.related_exp_id
```

````

````{py:attribute} item
:canonical: agentsociety.webapi.models.bill.ApiBill.item
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.item
```

````

````{py:attribute} amount
:canonical: agentsociety.webapi.models.bill.ApiBill.amount
:type: decimal.Decimal
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.amount
```

````

````{py:attribute} unit_price
:canonical: agentsociety.webapi.models.bill.ApiBill.unit_price
:type: decimal.Decimal
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.unit_price
```

````

````{py:attribute} quantity
:canonical: agentsociety.webapi.models.bill.ApiBill.quantity
:type: float
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.quantity
```

````

````{py:attribute} description
:canonical: agentsociety.webapi.models.bill.ApiBill.description
:type: str
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.description
```

````

````{py:attribute} created_at
:canonical: agentsociety.webapi.models.bill.ApiBill.created_at
:type: pydantic.AwareDatetime
:value: >
   None

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.created_at
```

````

`````{py:class} Config
:canonical: agentsociety.webapi.models.bill.ApiBill.Config

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.Config
```

````{py:attribute} from_attributes
:canonical: agentsociety.webapi.models.bill.ApiBill.Config.from_attributes
:value: >
   True

```{autodoc2-docstring} agentsociety.webapi.models.bill.ApiBill.Config.from_attributes
```

````

`````

``````
