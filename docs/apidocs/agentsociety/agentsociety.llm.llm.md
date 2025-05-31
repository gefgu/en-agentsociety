# {py:mod}`agentsociety.llm.llm`

```{py:module} agentsociety.llm.llm
```

```{autodoc2-docstring} agentsociety.llm.llm
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`LLMProviderType <agentsociety.llm.llm.LLMProviderType>`
  - ```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType
    :summary:
    ```
* - {py:obj}`LLMConfig <agentsociety.llm.llm.LLMConfig>`
  - ```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig
    :summary:
    ```
* - {py:obj}`LLM <agentsociety.llm.llm.LLM>`
  - ```{autodoc2-docstring} agentsociety.llm.llm.LLM
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`record_active_request <agentsociety.llm.llm.record_active_request>`
  - ```{autodoc2-docstring} agentsociety.llm.llm.record_active_request
    :summary:
    ```
* - {py:obj}`monitor_requests <agentsociety.llm.llm.monitor_requests>`
  - ```{autodoc2-docstring} agentsociety.llm.llm.monitor_requests
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.llm.llm.__all__>`
  - ```{autodoc2-docstring} agentsociety.llm.llm.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.llm.llm.__all__
:value: >
   ['LLM', 'LLMConfig', 'monitor_requests']

```{autodoc2-docstring} agentsociety.llm.llm.__all__
```

````

`````{py:class} LLMProviderType()
:canonical: agentsociety.llm.llm.LLMProviderType

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType.__init__
```

````{py:attribute} OpenAI
:canonical: agentsociety.llm.llm.LLMProviderType.OpenAI
:value: >
   'openai'

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType.OpenAI
```

````

````{py:attribute} DeepSeek
:canonical: agentsociety.llm.llm.LLMProviderType.DeepSeek
:value: >
   'deepseek'

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType.DeepSeek
```

````

````{py:attribute} Qwen
:canonical: agentsociety.llm.llm.LLMProviderType.Qwen
:value: >
   'qwen'

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType.Qwen
```

````

````{py:attribute} ZhipuAI
:canonical: agentsociety.llm.llm.LLMProviderType.ZhipuAI
:value: >
   'zhipuai'

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType.ZhipuAI
```

````

````{py:attribute} SiliconFlow
:canonical: agentsociety.llm.llm.LLMProviderType.SiliconFlow
:value: >
   'siliconflow'

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType.SiliconFlow
```

````

````{py:attribute} VLLM
:canonical: agentsociety.llm.llm.LLMProviderType.VLLM
:value: >
   'vllm'

```{autodoc2-docstring} agentsociety.llm.llm.LLMProviderType.VLLM
```

````

`````

`````{py:class} LLMConfig(/, **data: typing.Any)
:canonical: agentsociety.llm.llm.LLMConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.__init__
```

````{py:attribute} provider
:canonical: agentsociety.llm.llm.LLMConfig.provider
:type: agentsociety.llm.llm.LLMProviderType
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.provider
```

````

````{py:attribute} base_url
:canonical: agentsociety.llm.llm.LLMConfig.base_url
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.base_url
```

````

````{py:attribute} api_key
:canonical: agentsociety.llm.llm.LLMConfig.api_key
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.api_key
```

````

````{py:attribute} model
:canonical: agentsociety.llm.llm.LLMConfig.model
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.model
```

````

````{py:attribute} semaphore
:canonical: agentsociety.llm.llm.LLMConfig.semaphore
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.semaphore
```

````

````{py:method} serialize_provider(provider: agentsociety.llm.llm.LLMProviderType, info)
:canonical: agentsociety.llm.llm.LLMConfig.serialize_provider

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.serialize_provider
```

````

````{py:method} validate_configuration()
:canonical: agentsociety.llm.llm.LLMConfig.validate_configuration

```{autodoc2-docstring} agentsociety.llm.llm.LLMConfig.validate_configuration
```

````

`````

````{py:function} record_active_request(func: collections.abc.Callable)
:canonical: agentsociety.llm.llm.record_active_request

```{autodoc2-docstring} agentsociety.llm.llm.record_active_request
```
````

`````{py:class} LLM(configs: typing.List[agentsociety.llm.llm.LLMConfig])
:canonical: agentsociety.llm.llm.LLM

```{autodoc2-docstring} agentsociety.llm.llm.LLM
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.llm.llm.LLM.__init__
```

````{py:method} check_active_requests(timeout_threshold: float = 300)
:canonical: agentsociety.llm.llm.LLM.check_active_requests

```{autodoc2-docstring} agentsociety.llm.llm.LLM.check_active_requests
```

````

````{py:method} close()
:canonical: agentsociety.llm.llm.LLM.close
:async:

```{autodoc2-docstring} agentsociety.llm.llm.LLM.close
```

````

````{py:method} get_log_list()
:canonical: agentsociety.llm.llm.LLM.get_log_list

```{autodoc2-docstring} agentsociety.llm.llm.LLM.get_log_list
```

````

````{py:method} clear_log_list()
:canonical: agentsociety.llm.llm.LLM.clear_log_list

```{autodoc2-docstring} agentsociety.llm.llm.LLM.clear_log_list
```

````

````{py:method} clear_used()
:canonical: agentsociety.llm.llm.LLM.clear_used

```{autodoc2-docstring} agentsociety.llm.llm.LLM.clear_used
```

````

````{py:method} get_consumption()
:canonical: agentsociety.llm.llm.LLM.get_consumption

```{autodoc2-docstring} agentsociety.llm.llm.LLM.get_consumption
```

````

````{py:method} show_consumption(input_price: typing.Optional[float] = None, output_price: typing.Optional[float] = None)
:canonical: agentsociety.llm.llm.LLM.show_consumption

```{autodoc2-docstring} agentsociety.llm.llm.LLM.show_consumption
```

````

````{py:method} _get_next_client()
:canonical: agentsociety.llm.llm.LLM._get_next_client

```{autodoc2-docstring} agentsociety.llm.llm.LLM._get_next_client
```

````

````{py:method} atext_request(dialog: list[openai.types.chat.ChatCompletionMessageParam], response_format: typing.Union[openai.types.chat.completion_create_params.ResponseFormat, openai.NotGiven] = NOT_GIVEN, temperature: float = 1, max_tokens: typing.Optional[int] = None, top_p: typing.Optional[float] = None, frequency_penalty: typing.Optional[float] = None, presence_penalty: typing.Optional[float] = None, timeout: int = 300, retries: int = 10, tools: typing.Union[typing.List[openai.types.chat.ChatCompletionToolParam], openai.NotGiven] = NOT_GIVEN, tool_choice: typing.Union[openai.types.chat.ChatCompletionToolChoiceOptionParam, openai.NotGiven] = NOT_GIVEN)
:canonical: agentsociety.llm.llm.LLM.atext_request
:async:

```{autodoc2-docstring} agentsociety.llm.llm.LLM.atext_request
```

````

````{py:method} get_error_statistics()
:canonical: agentsociety.llm.llm.LLM.get_error_statistics

```{autodoc2-docstring} agentsociety.llm.llm.LLM.get_error_statistics
```

````

`````

````{py:function} monitor_requests(llm_instance: agentsociety.llm.llm.LLM, interval: float = 60, timeout_threshold: float = 300)
:canonical: agentsociety.llm.llm.monitor_requests
:async:

```{autodoc2-docstring} agentsociety.llm.llm.monitor_requests
```
````
