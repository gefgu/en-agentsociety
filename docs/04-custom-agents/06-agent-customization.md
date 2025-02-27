# Customize the Agent

To customize the behavior of an agent, you need to modify the `forward` method. 

The `forward` method is where the agent's logic is defined and executed in each simulation step. 
Here are two ways to customize the `forward` methods.

## 1. Directly Implement Your Logic

A simple example is as follows. Simply rewrite the `forward` method in the subclass of `Agent`. The `forward` method is the workflow of an agent.

```python
import asyncio

from agentsociety import Agent, AgentType


class CustomAgent(Agent):
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, type=AgentType.Citizen, **kwargs)

    async def forward(
        self,
    ):
        print(f"type:{self._type}")


async def main():
    agent = CustomAgent("custom_agent")
    await agent.forward()


if __name__ == "__main__":
    asyncio.run(main())
```

## 2. Implement Your Logic with `Block`

For complex behaviors, you can use `Block` to organize logic.

### What is a `Block`?

A `Block` is a abstraction of agent logics, analogous to a layer in PyTorch. It encapsulates modular functionality and supports configurable fields.

`Blocks` enable hierarchical system design by allowing nested sub-Blocks and standardized configuration management. 
They abstract domain-specific tasks (e.g., reasoning, simulation) and promote reusability, scalability, and maintainability.

### Workflow of `Block`: The `forward` Method

The core workflow of a `Block` is defined by its `forward` method. 
This method encapsulates the block’s primary logic, such as reasoning, data processing, or interaction with external components (e.g., LLMs, memory, or simulators). 

Combine multiple blocks by calling `await object.forward()` within a parent block’s `forward` method.

To define a parent-child block relation, you can either write it in the agent config with `ExpConfig.SetAgentConfig(agent_class_configs=<YOUR-CONFIG-DICT>)` or define your own block class and set the child block as its variable.

A simple `agent_class_configs` example with parent and child block is as follows:

```json
{
    "agent_name": "SocietyAgent",
    "config": {
        "enable_cognition": true,
        "enable_mobility": true,
        "enable_social": true,
        "enable_economy": true
    },
    "blocks": [
        {
            "name": "mindBlock",
            "config": {},
            "description": {},
            "children": [
                {
                    "name": "cognitionBlock",
                    "config": {
                        "top_k": 20
                    },
                    "description": {
                        "top_k": "Number of most relevant memories to return, defaults to 20"
                    },
                    "children": []
                }
            ]
        }
      ]
}
```

### `Block` Execution Control

When a `Block` is initialized, you can pass an `EventTrigger` to `trigger`.

The `EventTrigger` class is a foundational component designed to monitor and react to specific conditions within a `Block`. 

This class integrates with `Block` instances to access dependencies (e.g., LLMs, memory, simulators) and ensures required components are available before activation.

The `Block` workflow is executed only after `EventTrigger.wait_for_trigger()` has completed.

### Implementation Example

```python
import asyncio
from typing import Optional

from agentsociety import Simulator
from agentsociety.agent import Agent
from agentsociety.llm import LLM
from agentsociety.memory import Memory
from agentsociety.workflow import Block


class SecondCustomBlock(Block):

    def __init__(
        self,
        agent: Agent,
        llm: LLM,
        memory: Memory,
        simulator: Simulator,
    ):
        super().__init__(
            name="SecondCustomBlock", llm=llm, memory=memory, simulator=simulator
        )
        self._agent = agent

    async def forward(self):
        return f"SecondCustomBlock forward!"


class FirstCustomBlock(Block):
    second_block: SecondCustomBlock

    def __init__(
        self,
        agent: Agent,
        llm: LLM,
        memory: Memory,
        simulator: Simulator,
    ):
        super().__init__(
            name="FirstCustomBlock", llm=llm, memory=memory, simulator=simulator
        )
        self._agent = agent
        self.second_block = SecondCustomBlock(agent, llm, memory, simulator)

    async def forward(self):
        first_log = f"FirstCustomBlock forward!"
        second_log = await self.second_block.forward()
        if self._agent.enable_print:
            print(first_log, second_log)


class CustomAgent(Agent):

    configurable_fields = [
        "enable_print",
    ]
    default_values = {
        "enable_print": True,
    }
    fields_description = {
        "enable_print": "Enable Print Message",
    }
    first_block: FirstCustomBlock

    def __init__(
        self,
        name: str,
        llm_client: Optional[LLM] = None,
        simulator: Optional[Simulator] = None,
        memory: Optional[Memory] = None,
    ) -> None:
        super().__init__(
            name=name,
            llm_client=llm_client,
            simulator=simulator,
            memory=memory,
        )
        self.enable_print = True
        self.first_block = FirstCustomBlock(self, llm_client, memory, simulator)

    # Main workflow
    async def forward(self):
        await self.first_block.forward()


async def main():
    agent = CustomAgent(name="CustomAgent")
    print(agent.export_class_config())
    await agent.forward()


if __name__ == "__main__":
    asyncio.run(main())

```

## 3. Using Tools in Your `Agent`

Tools provide reusable functionality that can be automatically bound to `Agent` or `Block`.

```python
from agentsociety.tools import Tool


class CustomTool(Tool):
    async def __call__(
        self,
    ):
        # Tool bound to agent
        agent = self.agent
        await agent.status.update("key", "value")
        # # Tool bound to block
        # block = self.block
        # await block.memory.status.update("key", "value")


class CustomAgent(Agent):
    my_tool = CustomTool()  # Tool automatically binds to agent instance

    async def forward(self):
        await self.my_tool()  # Use the tool

```

## 4. Using Self-defined Agents in Your Experiment

Set your agent classes and their count with `configs.ExpConfig.SetAgentConfig`.

```python
import logging

from agentsociety.cityagent import memory_config_societyagent
from agentsociety.configs import ExpConfig

exp_config = (
    ExpConfig(exp_name="exp", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
        extra_agent_class={
            # self-defined agent classes
            DisagreeAgent: 1,
            AgreeAgent: 1
        },
        memory_config_func={
            DisagreeAgent: memory_config_societyagent,
            AgreeAgent: memory_config_societyagent
        }
    )
)
```

With the config above, one `DisagreeAgent`, one `AgreeAgent` and 100 `SocietyAgent` will be initialized in our simulation environment.
