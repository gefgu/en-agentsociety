# {py:mod}`agentsociety.message.messager`

```{py:module} agentsociety.message.messager
```

```{autodoc2-docstring} agentsociety.message.messager
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`RedisConfig <agentsociety.message.messager.RedisConfig>`
  - ```{autodoc2-docstring} agentsociety.message.messager.RedisConfig
    :summary:
    ```
* - {py:obj}`Messager <agentsociety.message.messager.Messager>`
  - ```{autodoc2-docstring} agentsociety.message.messager.Messager
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.message.messager.__all__>`
  - ```{autodoc2-docstring} agentsociety.message.messager.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.message.messager.__all__
:value: >
   ['Messager', 'RedisConfig']

```{autodoc2-docstring} agentsociety.message.messager.__all__
```

````

`````{py:class} RedisConfig(/, **data: typing.Any)
:canonical: agentsociety.message.messager.RedisConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} agentsociety.message.messager.RedisConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.message.messager.RedisConfig.__init__
```

````{py:attribute} server
:canonical: agentsociety.message.messager.RedisConfig.server
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.message.messager.RedisConfig.server
```

````

````{py:attribute} port
:canonical: agentsociety.message.messager.RedisConfig.port
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.message.messager.RedisConfig.port
```

````

````{py:attribute} password
:canonical: agentsociety.message.messager.RedisConfig.password
:type: typing.Optional[str]
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.message.messager.RedisConfig.password
```

````

````{py:attribute} db
:canonical: agentsociety.message.messager.RedisConfig.db
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.message.messager.RedisConfig.db
```

````

````{py:attribute} timeout
:canonical: agentsociety.message.messager.RedisConfig.timeout
:type: float
:value: >
   'Field(...)'

```{autodoc2-docstring} agentsociety.message.messager.RedisConfig.timeout
```

````

`````

`````{py:class} Messager(config: agentsociety.message.messager.RedisConfig, exp_id: str, message_interceptor: typing.Optional[ray.ObjectRef] = None, forward_strategy: typing.Literal[outer_control, inner_control] = 'inner_control')
:canonical: agentsociety.message.messager.Messager

```{autodoc2-docstring} agentsociety.message.messager.Messager
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.message.messager.Messager.__init__
```

````{py:property} message_interceptor
:canonical: agentsociety.message.messager.Messager.message_interceptor
:type: typing.Optional[ray.ObjectRef]

```{autodoc2-docstring} agentsociety.message.messager.Messager.message_interceptor
```

````

````{py:method} get_log_list()
:canonical: agentsociety.message.messager.Messager.get_log_list

```{autodoc2-docstring} agentsociety.message.messager.Messager.get_log_list
```

````

````{py:method} clear_log_list()
:canonical: agentsociety.message.messager.Messager.clear_log_list

```{autodoc2-docstring} agentsociety.message.messager.Messager.clear_log_list
```

````

````{py:method} set_message_interceptor(message_interceptor: ray.ObjectRef)
:canonical: agentsociety.message.messager.Messager.set_message_interceptor

```{autodoc2-docstring} agentsociety.message.messager.Messager.set_message_interceptor
```

````

````{py:method} init()
:canonical: agentsociety.message.messager.Messager.init
:async:

```{autodoc2-docstring} agentsociety.message.messager.Messager.init
```

````

````{py:method} close()
:canonical: agentsociety.message.messager.Messager.close
:async:

```{autodoc2-docstring} agentsociety.message.messager.Messager.close
```

````

````{py:method} subscribe_and_start_listening(channels: typing.List[str])
:canonical: agentsociety.message.messager.Messager.subscribe_and_start_listening
:async:

```{autodoc2-docstring} agentsociety.message.messager.Messager.subscribe_and_start_listening
```

````

````{py:method} fetch_messages()
:canonical: agentsociety.message.messager.Messager.fetch_messages
:async:

```{autodoc2-docstring} agentsociety.message.messager.Messager.fetch_messages
```

````

````{py:method} send_message(channel: str, payload: dict, from_id: typing.Optional[int] = None, to_id: typing.Optional[int] = None)
:canonical: agentsociety.message.messager.Messager.send_message
:async:

```{autodoc2-docstring} agentsociety.message.messager.Messager.send_message
```

````

````{py:method} _listen_for_messages(pubsub: redis.asyncio.client.PubSub, channels: typing.List[str])
:canonical: agentsociety.message.messager.Messager._listen_for_messages
:async:

```{autodoc2-docstring} agentsociety.message.messager.Messager._listen_for_messages
```

````

````{py:method} forward(validation_dict: typing.Optional[agentsociety.message.message_interceptor.MessageIdentifier] = None, persuasion_messages: typing.Optional[list[dict[str, typing.Any]]] = None)
:canonical: agentsociety.message.messager.Messager.forward
:async:

```{autodoc2-docstring} agentsociety.message.messager.Messager.forward
```

````

````{py:method} get_subtopic_channel(agent_id: int, subtopic: str)
:canonical: agentsociety.message.messager.Messager.get_subtopic_channel

```{autodoc2-docstring} agentsociety.message.messager.Messager.get_subtopic_channel
```

````

````{py:method} get_aoi_channel(aoi_id: int)
:canonical: agentsociety.message.messager.Messager.get_aoi_channel

```{autodoc2-docstring} agentsociety.message.messager.Messager.get_aoi_channel
```

````

````{py:method} get_user_survey_channel(agent_id: int)
:canonical: agentsociety.message.messager.Messager.get_user_survey_channel

```{autodoc2-docstring} agentsociety.message.messager.Messager.get_user_survey_channel
```

````

````{py:method} get_user_chat_channel(agent_id: int)
:canonical: agentsociety.message.messager.Messager.get_user_chat_channel

```{autodoc2-docstring} agentsociety.message.messager.Messager.get_user_chat_channel
```

````

````{py:method} get_agent_chat_channel(agent_id: int)
:canonical: agentsociety.message.messager.Messager.get_agent_chat_channel

```{autodoc2-docstring} agentsociety.message.messager.Messager.get_agent_chat_channel
```

````

````{py:method} get_user_payback_channel()
:canonical: agentsociety.message.messager.Messager.get_user_payback_channel

```{autodoc2-docstring} agentsociety.message.messager.Messager.get_user_payback_channel
```

````

`````
