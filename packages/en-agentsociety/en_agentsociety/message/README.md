# `message/` — Agent Message System

This package implements the inter-agent communication bus and message interception layer.

---

## Files

| File | Purpose |
|---|---|
| `messager.py` | `Messager` — message bus (send/receive) |
| `message_interceptor.py` | `MessageInterceptor` — supervisor-style message monitor |

---

## Overview

Agents communicate by passing `Message` objects through an async message bus (`Messager`). An optional `MessageInterceptor` (Ray actor) can inspect all messages and block/modify them using LLM-based rule checking.

```
Agent A ──send──► Messager ──► MessageInterceptor ──► Agent B
                                      │
                                  (optional) block/modify/log
```

---

## `Message`

```python
class Message(BaseModel):
    sender_id: int
    receiver_id: int
    kind: MessageKind
    content: str
    timestamp: float

class MessageKind(Enum):
    AGENT_CHAT    = "agent_chat"
    INTERVIEW     = "interview"
    SURVEY        = "survey"
    SYSTEM        = "system"
```

---

## `Messager` API

```python
# Send a message
await messager.send_message(
    sender_id=1,
    receiver_id=2,
    kind=MessageKind.AGENT_CHAT,
    content="Hi, want to grab lunch?",
)

# Receive all pending messages for this agent
messages = await messager.receive_messages(agent_id=2)
```

Internally, `Messager` is implemented as a Ray actor to support concurrent access across distributed agents.

---

## `MessageInterceptor`

The `MessageInterceptor` is a Ray-based supervisor that watches all messages in flight.

### Implementing a Custom Block

```python
from en_agentsociety.message import MessageBlockListener

class MyMessageBlock(MessageBlockListener):
    async def on_message(self, message: Message) -> bool:
        """Return True to block the message, False to allow it."""
        if "spam" in message.content.lower():
            return True   # block
        return False      # allow
```

### Registration

```python
interceptor = MessageInterceptor(llm=llm)
interceptor.register_block(MyMessageBlock())
```

---

## Usage in Agents

Inside any `Block` or `Agent`, messages are sent via the toolbox:

```python
await self.toolbox.messager.send_message(
    sender_id=self._id,
    receiver_id=target_id,
    kind=MessageKind.AGENT_CHAT,
    content="Hello, neighbor!",
)
```

Incoming messages are typically processed in the agent's `forward()` by reading from the messager:

```python
messages = await self.toolbox.messager.receive_messages(self._id)
for msg in messages:
    await self.memory.stream.add({"type": "received_message", "content": msg.content})
```
