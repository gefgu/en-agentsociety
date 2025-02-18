# Message Interception

The message interception system provides control over Agent communications.
This part provides control tools for message propagation. We have pre-implemented two types of control policies. Among them, node intervention involves detecting and banning accounts that repeatedly spread incendiary content to reduce the source of information. Edge intervention, on the other hand, severs social connections upon discovering the spread of incendiary content to curb its diffusion. 

Our platform also supports user-defined control policies.

## Pre-defined Message Control

We have implemented two message control modes in our framework, edge mode and point mode.

To activate the message control system, simply use `ExpConfig.SetMessageIntercept`, e.g. `ExpConfig().SetMessageIntercept(mode="point", max_violation_time=3)`.

### Edge Mode

In this mode, when a message is deemed invalid (emotionally provocative), and the sender has exceeded the maximum allowed violations (`max_violation_time`), this block adds the exact sender-receiver pair (from_uuid, to_uuid) to the blacklist.

#### Usage Example

```python
import asyncio
import logging

from agentsociety import AgentSimulation
from agentsociety.cityagent.message_intercept import (EdgeMessageBlock,
                                                      MessageBlockListener)
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_edge", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
    )
    .SetMessageIntercept(
        message_interceptor_blocks=[EdgeMessageBlock()],
        message_listener=MessageBlockListener(),
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=5),
        ]
    )
)


async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)


if __name__ == "__main__":
    asyncio.run(main())

```

### Point Mode

In this mode, the framework checks if messages are emotionally provocative and evaluates whether the sender has exceeded the violation limit, this block adds the exact sender-receiver pair (from_uuid, None) to the blacklist. (from_uuid, None) in a blacklist means the sender can no longer send out any messages.

#### Usage Example

```python
import asyncio
import logging

from agentsociety import AgentSimulation
from agentsociety.cityagent.message_intercept import (PointMessageBlock,
                                                      MessageBlockListener)
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_point", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
    )
    .SetMessageIntercept(
        message_interceptor_blocks=[PointMessageBlock()],
        message_listener=MessageBlockListener(),
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=5),
        ]
    )
)


async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)


if __name__ == "__main__":
    asyncio.run(main())

```

## Self-define Message Control

We also support to define your own interception logic.

There are two types of base classes:

- `agentsociety.message.MessageBlockBase`: checks if the message is from/to any blacklisted entities
- `agentsociety.message.MessageBlockListenerBase`: a listener class that processes values from the blocked message queue asynchronously.

To define your own interception logic, you need to inherit these two classes and rewrite their `forward` methods, which are their workflows. 

### Usage Example

```python
import asyncio

from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.message import MessageBlockBase, MessageBlockListenerBase


class CustomMessageBlock(MessageBlockBase):
    def __init__(self, name: str = "", max_violation_time: int = 3) -> None:
        super().__init__(name)
        self.max_violation_time = max_violation_time

    async def forward(  # type:ignore
        self,
        from_uuid: str,
        to_uuid: str,
        msg: str,
        violation_counts: dict[str, int],
        black_list: list[tuple[str, str]],
    ):
        if (
            (from_uuid, to_uuid) in set(black_list)
            or (None, to_uuid) in set(black_list)
            or (from_uuid, None) in set(black_list)
        ):
            return False
        else:
            is_valid = False
            if (
                not is_valid
                and violation_counts[from_uuid] >= self.max_violation_time - 1
            ):
                black_list.append((from_uuid, to_uuid))
            return is_valid


class CustomMessageBlockListener(MessageBlockListenerBase):
    def __init__(
        self, save_queue_values: bool = False, get_queue_period: float = 0.1
    ) -> None:
        super().__init__(save_queue_values, get_queue_period)

    async def forward(
        self,
    ):
        while True:
            if self.has_queue:
                value = await self.queue.get_async()  # type: ignore
                if self._save_queue_values:
                    self._values_from_queue.append(value)
                print(f"get `{value}` from queue")
                # do something with the value
            await asyncio.sleep(self._get_queue_period)


# use self-defined message control logic
# ------------------------------------------------------------------------#
ExpConfig().SetMessageIntercept(
    message_interceptor_blocks=[CustomMessageBlock()],
    message_listener=CustomMessageBlockListener(),
)
# ------------------------------------------------------------------------#

```
