# Customize the Agent logic

To customize the behavior of an agent, you can modify the `forward` method. 
This method is where the agent's logic is defined and executed in each simulation step. 
Here are two ways to customize the `forward` methods.

## Direct Implementation

A simple example is as follows.

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


## Block Based Implementation

For complex behaviors, use `Block` to organize logic.

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


## Using Tools
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

## Initialization within Your Experiment
Set your agent classes and their count with `configs.ExpConfig`.

```python
import logging

from agentsociety.cityagent import memory_config_societyagent
from agentsociety.configs import ExpConfig

exp_config = (
    ExpConfig(exp_name="cognition_exp3", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
        extra_agent_class={
            # your defined agent classes
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
