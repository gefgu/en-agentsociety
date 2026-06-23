# {py:mod}`en_agentsociety.message.messager`

```{py:module} en_agentsociety.message.messager
```

```{autodoc2-docstring} en_agentsociety.message.messager
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`MessageKind <en_agentsociety.message.messager.MessageKind>`
  -
* - {py:obj}`Message <en_agentsociety.message.messager.Message>`
  -
* - {py:obj}`Messager <en_agentsociety.message.messager.Messager>`
  - ```{autodoc2-docstring} en_agentsociety.message.messager.Messager
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.message.messager.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.message.messager.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.message.messager.__all__
:value: >
   ['MessageKind', 'Message', 'Messager']

```{autodoc2-docstring} en_agentsociety.message.messager.__all__
```

````

`````{py:class} MessageKind()
:canonical: en_agentsociety.message.messager.MessageKind

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

````{py:attribute} AGENT_CHAT
:canonical: en_agentsociety.message.messager.MessageKind.AGENT_CHAT
:value: >
   'agent-chat'

```{autodoc2-docstring} en_agentsociety.message.messager.MessageKind.AGENT_CHAT
```

````

````{py:attribute} USER_CHAT
:canonical: en_agentsociety.message.messager.MessageKind.USER_CHAT
:value: >
   'user-chat'

```{autodoc2-docstring} en_agentsociety.message.messager.MessageKind.USER_CHAT
```

````

````{py:attribute} AOI_MESSAGE_REGISTER
:canonical: en_agentsociety.message.messager.MessageKind.AOI_MESSAGE_REGISTER
:value: >
   'aoi-message-register'

```{autodoc2-docstring} en_agentsociety.message.messager.MessageKind.AOI_MESSAGE_REGISTER
```

````

````{py:attribute} AOI_MESSAGE_CANCEL
:canonical: en_agentsociety.message.messager.MessageKind.AOI_MESSAGE_CANCEL
:value: >
   'aoi-message-cancel'

```{autodoc2-docstring} en_agentsociety.message.messager.MessageKind.AOI_MESSAGE_CANCEL
```

````

`````

`````{py:class} Message(/, **data: typing.Any)
:canonical: en_agentsociety.message.messager.Message

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} from_id
:canonical: en_agentsociety.message.messager.Message.from_id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.message.messager.Message.from_id
```

````

````{py:attribute} to_id
:canonical: en_agentsociety.message.messager.Message.to_id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.message.messager.Message.to_id
```

````

````{py:attribute} day
:canonical: en_agentsociety.message.messager.Message.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.message.messager.Message.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.message.messager.Message.t
:type: float
:value: >
   None

```{autodoc2-docstring} en_agentsociety.message.messager.Message.t
```

````

````{py:attribute} kind
:canonical: en_agentsociety.message.messager.Message.kind
:type: en_agentsociety.message.messager.MessageKind
:value: >
   None

```{autodoc2-docstring} en_agentsociety.message.messager.Message.kind
```

````

````{py:attribute} payload
:canonical: en_agentsociety.message.messager.Message.payload
:type: dict
:value: >
   None

```{autodoc2-docstring} en_agentsociety.message.messager.Message.payload
```

````

````{py:attribute} created_at
:canonical: en_agentsociety.message.messager.Message.created_at
:type: datetime.datetime
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.message.messager.Message.created_at
```

````

````{py:attribute} extra
:canonical: en_agentsociety.message.messager.Message.extra
:type: typing.Optional[dict]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.message.messager.Message.extra
```

````

````{py:method} __hash__()
:canonical: en_agentsociety.message.messager.Message.__hash__

````

`````

`````{py:class} Messager(exp_id: str)
:canonical: en_agentsociety.message.messager.Messager

```{autodoc2-docstring} en_agentsociety.message.messager.Messager
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.__init__
```

````{py:property} message_interceptor
:canonical: en_agentsociety.message.messager.Messager.message_interceptor
:type: typing.Optional[ray.ObjectRef]

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.message_interceptor
```

````

````{py:method} set_message_interceptor(message_interceptor: ray.ObjectRef)
:canonical: en_agentsociety.message.messager.Messager.set_message_interceptor

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.set_message_interceptor
```

````

````{py:method} send_message(message: en_agentsociety.message.messager.Message)
:canonical: en_agentsociety.message.messager.Messager.send_message
:async:

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.send_message
```

````

````{py:method} fetch_pending_messages()
:canonical: en_agentsociety.message.messager.Messager.fetch_pending_messages
:async:

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.fetch_pending_messages
```

````

````{py:method} set_received_messages(messages: list[en_agentsociety.message.messager.Message])
:canonical: en_agentsociety.message.messager.Messager.set_received_messages
:async:

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.set_received_messages
```

````

````{py:method} fetch_received_messages()
:canonical: en_agentsociety.message.messager.Messager.fetch_received_messages
:async:

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.fetch_received_messages
```

````

````{py:method} get_subtopic_channel(agent_id: int, subtopic: str)
:canonical: en_agentsociety.message.messager.Messager.get_subtopic_channel

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.get_subtopic_channel
```

````

````{py:method} get_aoi_channel(aoi_id: int)
:canonical: en_agentsociety.message.messager.Messager.get_aoi_channel

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.get_aoi_channel
```

````

````{py:method} get_user_survey_channel(agent_id: int)
:canonical: en_agentsociety.message.messager.Messager.get_user_survey_channel

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.get_user_survey_channel
```

````

````{py:method} get_user_chat_channel(agent_id: int)
:canonical: en_agentsociety.message.messager.Messager.get_user_chat_channel

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.get_user_chat_channel
```

````

````{py:method} get_agent_chat_channel(agent_id: int)
:canonical: en_agentsociety.message.messager.Messager.get_agent_chat_channel

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.get_agent_chat_channel
```

````

````{py:method} get_user_payback_channel()
:canonical: en_agentsociety.message.messager.Messager.get_user_payback_channel

```{autodoc2-docstring} en_agentsociety.message.messager.Messager.get_user_payback_channel
```

````

`````
