# {py:mod}`agentsociety.message.message_interceptor`

```{py:module} agentsociety.message.message_interceptor
```

```{autodoc2-docstring} agentsociety.message.message_interceptor
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`MessageInterceptor <agentsociety.message.message_interceptor.MessageInterceptor>`
  - ```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DEFAULT_ERROR_STRING <agentsociety.message.message_interceptor.DEFAULT_ERROR_STRING>`
  - ```{autodoc2-docstring} agentsociety.message.message_interceptor.DEFAULT_ERROR_STRING
    :summary:
    ```
* - {py:obj}`logger <agentsociety.message.message_interceptor.logger>`
  - ```{autodoc2-docstring} agentsociety.message.message_interceptor.logger
    :summary:
    ```
* - {py:obj}`__all__ <agentsociety.message.message_interceptor.__all__>`
  - ```{autodoc2-docstring} agentsociety.message.message_interceptor.__all__
    :summary:
    ```
````

### API

````{py:data} DEFAULT_ERROR_STRING
:canonical: agentsociety.message.message_interceptor.DEFAULT_ERROR_STRING
:value: <Multiline-String>

```{autodoc2-docstring} agentsociety.message.message_interceptor.DEFAULT_ERROR_STRING
```

````

````{py:data} logger
:canonical: agentsociety.message.message_interceptor.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} agentsociety.message.message_interceptor.logger
```

````

````{py:data} __all__
:canonical: agentsociety.message.message_interceptor.__all__
:value: >
   ['MessageInterceptor']

```{autodoc2-docstring} agentsociety.message.message_interceptor.__all__
```

````

`````{py:class} MessageInterceptor(llm_config: list[agentsociety.llm.LLMConfig])
:canonical: agentsociety.message.message_interceptor.MessageInterceptor

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.__init__
```

````{py:method} init()
:canonical: agentsociety.message.message_interceptor.MessageInterceptor.init
:async:

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.init
```

````

````{py:method} close()
:canonical: agentsociety.message.message_interceptor.MessageInterceptor.close
:async:

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.close
```

````

````{py:method} set_supervisor(supervisor)
:canonical: agentsociety.message.message_interceptor.MessageInterceptor.set_supervisor
:async:

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.set_supervisor
```

````

````{py:property} supervisor
:canonical: agentsociety.message.message_interceptor.MessageInterceptor.supervisor

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.supervisor
```

````

````{py:property} llm
:canonical: agentsociety.message.message_interceptor.MessageInterceptor.llm
:type: agentsociety.llm.LLM

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.llm
```

````

````{py:method} violation_counts() -> dict[int, int]
:canonical: agentsociety.message.message_interceptor.MessageInterceptor.violation_counts
:async:

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.violation_counts
```

````

````{py:method} forward(messages: list[agentsociety.message.messager.Message]) -> list[agentsociety.message.messager.Message]
:canonical: agentsociety.message.message_interceptor.MessageInterceptor.forward
:async:

```{autodoc2-docstring} agentsociety.message.message_interceptor.MessageInterceptor.forward
```

````

`````
