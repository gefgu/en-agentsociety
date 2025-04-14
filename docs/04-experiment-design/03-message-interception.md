# Message Interception

The message interception system provides control over agent communications in the simulation environment. This feature allows you to monitor, filter, and regulate messages exchanged between agents based on customizable rules.

## Overview

The message interception system consists of two main components:

1. **Message Blocks**: Classes that implement filtering logic to determine whether messages should be allowed or blocked
2. **Message Listeners**: Components that process notifications about blocked messages

## Message Listener

A listener class that processes values from the blocked message queue asynchronously. To implement a custom listener, you need to inherit from `MessageBlockListenerBase` and implement the `forward` method.

### Example of a Custom Listener

Here is an example of a custom listener that does nothing, you can implement your own logic in the `forward` method.

```python
from agentsociety.message import MessageBlockListenerBase
from ray.util.queue import Queue, Empty
from typing import Any

class DoNothingListener(MessageBlockListenerBase):
    def __init__(self, queue: Queue) -> None:
        super().__init__(queue)

    async def forward(self, msg: Any):
        # Do nothing
        pass
    async def reset(self):
        # Do nothing
        pass

```

## Pre-defined Message Control

We have implemented two message control modes in our framework:

### Edge Mode

In this mode, when a message is deemed invalid (e.g., emotionally provocative), and the sender has exceeded the maximum allowed violations (`max_violation_time`), the system adds the specific sender-recipient pair `(from_id, to_id)` to the blacklist, preventing further communication between these specific agents.

### Usage Example

We provide an example of using the edge mode in the [inflammatory messages](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/inflammatory_message) use case.

Simply set the `mode` to `edge` in the experiment configuration.

```python
config = Config(
    ...
    exp=ExpConfig(
        ...
        message_intercept=MessageInterceptConfig(
            mode="edge",
            listener=DoNothingListener,
        ),  # type: ignore
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
    ),
)

```

### Point Mode

In this mode, when a message is deemed invalid (e.g., emotionally provocative), and the sender has exceeded the maximum allowed violations (`max_violation_time`), the system adds the specific sender-recipient pair `(from_id, to_id)` to the blacklist, preventing further communication between these specific agents.

### Usage Example

We provide an example of using the point mode in the [inflammatory messages](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/inflammatory_message) use case.

Simply set the `mode` to `point` in the experiment configuration.

```python
config = Config(
    ...
    exp=ExpConfig(
        ...
        message_intercept=MessageInterceptConfig(
            mode="point",
            listener=DoNothingListener,
        ),  # type: ignore
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
    ),
)

```
