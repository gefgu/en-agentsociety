# {py:mod}`agentsociety.webapi.api.agent_template`

```{py:module} agentsociety.webapi.api.agent_template
```

```{autodoc2-docstring} agentsociety.webapi.api.agent_template
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`list_agent_templates <agentsociety.webapi.api.agent_template.list_agent_templates>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.list_agent_templates
    :summary:
    ```
* - {py:obj}`get_agent_template <agentsociety.webapi.api.agent_template.get_agent_template>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_agent_template
    :summary:
    ```
* - {py:obj}`create_agent_template <agentsociety.webapi.api.agent_template.create_agent_template>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.create_agent_template
    :summary:
    ```
* - {py:obj}`update_agent_template <agentsociety.webapi.api.agent_template.update_agent_template>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.update_agent_template
    :summary:
    ```
* - {py:obj}`delete_agent_template <agentsociety.webapi.api.agent_template.delete_agent_template>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.delete_agent_template
    :summary:
    ```
* - {py:obj}`get_agent_blocks <agentsociety.webapi.api.agent_template.get_agent_blocks>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_agent_blocks
    :summary:
    ```
* - {py:obj}`simplify_type <agentsociety.webapi.api.agent_template.simplify_type>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.simplify_type
    :summary:
    ```
* - {py:obj}`get_field_info <agentsociety.webapi.api.agent_template.get_field_info>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_field_info
    :summary:
    ```
* - {py:obj}`get_agent_param <agentsociety.webapi.api.agent_template.get_agent_param>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_agent_param
    :summary:
    ```
* - {py:obj}`get_block_param <agentsociety.webapi.api.agent_template.get_block_param>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_block_param
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.api.agent_template.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.__all__
    :summary:
    ```
* - {py:obj}`router <agentsociety.webapi.api.agent_template.router>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.agent_template.router
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.api.agent_template.__all__
:value: >
   ['router']

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.__all__
```

````

````{py:data} router
:canonical: agentsociety.webapi.api.agent_template.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.router
```

````

````{py:function} list_agent_templates(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[typing.List[agentsociety.webapi.models.agent_template.ApiAgentTemplate]]
:canonical: agentsociety.webapi.api.agent_template.list_agent_templates
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.list_agent_templates
```
````

````{py:function} get_agent_template(request: fastapi.Request, template_id: str) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.agent_template.ApiAgentTemplate]
:canonical: agentsociety.webapi.api.agent_template.get_agent_template
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_agent_template
```
````

````{py:function} create_agent_template(request: fastapi.Request, template: agentsociety.webapi.models.agent_template.ApiAgentTemplate = Body(...)) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.agent_template.ApiAgentTemplate]
:canonical: agentsociety.webapi.api.agent_template.create_agent_template
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.create_agent_template
```
````

````{py:function} update_agent_template(request: fastapi.Request, template_id: str, template: agentsociety.webapi.models.agent_template.ApiAgentTemplate = Body(...)) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.agent_template.ApiAgentTemplate]
:canonical: agentsociety.webapi.api.agent_template.update_agent_template
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.update_agent_template
```
````

````{py:function} delete_agent_template(request: fastapi.Request, template_id: str) -> agentsociety.webapi.models.ApiResponseWrapper[typing.Dict[str, str]]
:canonical: agentsociety.webapi.api.agent_template.delete_agent_template
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.delete_agent_template
```
````

````{py:function} get_agent_blocks(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[typing.List[typing.Dict[str, typing.Any]]]
:canonical: agentsociety.webapi.api.agent_template.get_agent_blocks
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_agent_blocks
```
````

````{py:function} simplify_type(type_annotation)
:canonical: agentsociety.webapi.api.agent_template.simplify_type

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.simplify_type
```
````

````{py:function} get_field_info(field)
:canonical: agentsociety.webapi.api.agent_template.get_field_info

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_field_info
```
````

````{py:function} get_agent_param(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[typing.Dict[str, typing.Any]]
:canonical: agentsociety.webapi.api.agent_template.get_agent_param
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_agent_param
```
````

````{py:function} get_block_param(request: fastapi.Request, block_type: str) -> agentsociety.webapi.models.ApiResponseWrapper[typing.Dict[str, typing.Any]]
:canonical: agentsociety.webapi.api.agent_template.get_block_param
:async:

```{autodoc2-docstring} agentsociety.webapi.api.agent_template.get_block_param
```
````
