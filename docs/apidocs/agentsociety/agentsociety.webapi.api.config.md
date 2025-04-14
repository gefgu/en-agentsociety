# {py:mod}`agentsociety.webapi.api.config`

```{py:module} agentsociety.webapi.api.config
```

```{autodoc2-docstring} agentsociety.webapi.api.config
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`list_llm_configs <agentsociety.webapi.api.config.list_llm_configs>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.list_llm_configs
    :summary:
    ```
* - {py:obj}`get_llm_config_by_id <agentsociety.webapi.api.config.get_llm_config_by_id>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.get_llm_config_by_id
    :summary:
    ```
* - {py:obj}`create_llm_config <agentsociety.webapi.api.config.create_llm_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.create_llm_config
    :summary:
    ```
* - {py:obj}`update_llm_config <agentsociety.webapi.api.config.update_llm_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.update_llm_config
    :summary:
    ```
* - {py:obj}`delete_llm_config <agentsociety.webapi.api.config.delete_llm_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.delete_llm_config
    :summary:
    ```
* - {py:obj}`list_map_configs <agentsociety.webapi.api.config.list_map_configs>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.list_map_configs
    :summary:
    ```
* - {py:obj}`get_map_config_by_id <agentsociety.webapi.api.config.get_map_config_by_id>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.get_map_config_by_id
    :summary:
    ```
* - {py:obj}`create_map_config <agentsociety.webapi.api.config.create_map_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.create_map_config
    :summary:
    ```
* - {py:obj}`update_map_config <agentsociety.webapi.api.config.update_map_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.update_map_config
    :summary:
    ```
* - {py:obj}`delete_map_config <agentsociety.webapi.api.config.delete_map_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.delete_map_config
    :summary:
    ```
* - {py:obj}`list_agent_configs <agentsociety.webapi.api.config.list_agent_configs>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.list_agent_configs
    :summary:
    ```
* - {py:obj}`get_agent_config_by_id <agentsociety.webapi.api.config.get_agent_config_by_id>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.get_agent_config_by_id
    :summary:
    ```
* - {py:obj}`create_agent_config <agentsociety.webapi.api.config.create_agent_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.create_agent_config
    :summary:
    ```
* - {py:obj}`update_agent_config <agentsociety.webapi.api.config.update_agent_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.update_agent_config
    :summary:
    ```
* - {py:obj}`delete_agent_config <agentsociety.webapi.api.config.delete_agent_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.delete_agent_config
    :summary:
    ```
* - {py:obj}`list_workflow_configs <agentsociety.webapi.api.config.list_workflow_configs>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.list_workflow_configs
    :summary:
    ```
* - {py:obj}`get_workflow_config_by_id <agentsociety.webapi.api.config.get_workflow_config_by_id>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.get_workflow_config_by_id
    :summary:
    ```
* - {py:obj}`create_workflow_config <agentsociety.webapi.api.config.create_workflow_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.create_workflow_config
    :summary:
    ```
* - {py:obj}`update_workflow_config <agentsociety.webapi.api.config.update_workflow_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.update_workflow_config
    :summary:
    ```
* - {py:obj}`delete_workflow_config <agentsociety.webapi.api.config.delete_workflow_config>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.delete_workflow_config
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.webapi.api.config.__all__>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.__all__
    :summary:
    ```
* - {py:obj}`router <agentsociety.webapi.api.config.router>`
  - ```{autodoc2-docstring} agentsociety.webapi.api.config.router
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.webapi.api.config.__all__
:value: >
   ['router']

```{autodoc2-docstring} agentsociety.webapi.api.config.__all__
```

````

````{py:data} router
:canonical: agentsociety.webapi.api.config.router
:value: >
   'APIRouter(...)'

```{autodoc2-docstring} agentsociety.webapi.api.config.router
```

````

````{py:function} list_llm_configs(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[typing.List[agentsociety.webapi.models.config.ApiLLMConfig]]
:canonical: agentsociety.webapi.api.config.list_llm_configs
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.list_llm_configs
```
````

````{py:function} get_llm_config_by_id(request: fastapi.Request, config_id: uuid.UUID) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.config.ApiLLMConfig]
:canonical: agentsociety.webapi.api.config.get_llm_config_by_id
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.get_llm_config_by_id
```
````

````{py:function} create_llm_config(request: fastapi.Request, config_data: agentsociety.webapi.models.config.ApiLLMConfig = Body(...))
:canonical: agentsociety.webapi.api.config.create_llm_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.create_llm_config
```
````

````{py:function} update_llm_config(request: fastapi.Request, config_id: uuid.UUID, config_data: agentsociety.webapi.models.config.ApiLLMConfig = Body(...))
:canonical: agentsociety.webapi.api.config.update_llm_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.update_llm_config
```
````

````{py:function} delete_llm_config(request: fastapi.Request, config_id: uuid.UUID)
:canonical: agentsociety.webapi.api.config.delete_llm_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.delete_llm_config
```
````

````{py:function} list_map_configs(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[typing.List[agentsociety.webapi.models.config.ApiMapConfig]]
:canonical: agentsociety.webapi.api.config.list_map_configs
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.list_map_configs
```
````

````{py:function} get_map_config_by_id(request: fastapi.Request, config_id: uuid.UUID) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.config.ApiMapConfig]
:canonical: agentsociety.webapi.api.config.get_map_config_by_id
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.get_map_config_by_id
```
````

````{py:function} create_map_config(request: fastapi.Request, config_data: agentsociety.webapi.models.config.ApiMapConfig = Body(...))
:canonical: agentsociety.webapi.api.config.create_map_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.create_map_config
```
````

````{py:function} update_map_config(request: fastapi.Request, config_id: uuid.UUID, config_data: agentsociety.webapi.models.config.ApiMapConfig = Body(...))
:canonical: agentsociety.webapi.api.config.update_map_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.update_map_config
```
````

````{py:function} delete_map_config(request: fastapi.Request, config_id: uuid.UUID)
:canonical: agentsociety.webapi.api.config.delete_map_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.delete_map_config
```
````

````{py:function} list_agent_configs(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[typing.List[agentsociety.webapi.models.config.ApiAgentConfig]]
:canonical: agentsociety.webapi.api.config.list_agent_configs
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.list_agent_configs
```
````

````{py:function} get_agent_config_by_id(request: fastapi.Request, config_id: uuid.UUID) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.config.ApiAgentConfig]
:canonical: agentsociety.webapi.api.config.get_agent_config_by_id
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.get_agent_config_by_id
```
````

````{py:function} create_agent_config(request: fastapi.Request, config_data: agentsociety.webapi.models.config.ApiAgentConfig = Body(...))
:canonical: agentsociety.webapi.api.config.create_agent_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.create_agent_config
```
````

````{py:function} update_agent_config(request: fastapi.Request, config_id: uuid.UUID, config_data: agentsociety.webapi.models.config.ApiAgentConfig = Body(...))
:canonical: agentsociety.webapi.api.config.update_agent_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.update_agent_config
```
````

````{py:function} delete_agent_config(request: fastapi.Request, config_id: uuid.UUID)
:canonical: agentsociety.webapi.api.config.delete_agent_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.delete_agent_config
```
````

````{py:function} list_workflow_configs(request: fastapi.Request) -> agentsociety.webapi.models.ApiResponseWrapper[typing.List[agentsociety.webapi.models.config.ApiWorkflowConfig]]
:canonical: agentsociety.webapi.api.config.list_workflow_configs
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.list_workflow_configs
```
````

````{py:function} get_workflow_config_by_id(request: fastapi.Request, config_id: uuid.UUID) -> agentsociety.webapi.models.ApiResponseWrapper[agentsociety.webapi.models.config.ApiWorkflowConfig]
:canonical: agentsociety.webapi.api.config.get_workflow_config_by_id
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.get_workflow_config_by_id
```
````

````{py:function} create_workflow_config(request: fastapi.Request, config_data: agentsociety.webapi.models.config.ApiWorkflowConfig = Body(...))
:canonical: agentsociety.webapi.api.config.create_workflow_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.create_workflow_config
```
````

````{py:function} update_workflow_config(request: fastapi.Request, config_id: uuid.UUID, config_data: agentsociety.webapi.models.config.ApiWorkflowConfig = Body(...))
:canonical: agentsociety.webapi.api.config.update_workflow_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.update_workflow_config
```
````

````{py:function} delete_workflow_config(request: fastapi.Request, config_id: uuid.UUID)
:canonical: agentsociety.webapi.api.config.delete_workflow_config
:async:

```{autodoc2-docstring} agentsociety.webapi.api.config.delete_workflow_config
```
````
