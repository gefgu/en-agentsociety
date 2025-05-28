# Customize the Agent

To customize the behavior of an agent, you need to modify the `forward` method. 

The `forward` method is where the agent's logic is defined and executed in each simulation step. 
Here are two ways to customize the `forward` methods.

## 1. Directly Implement Your Logic

A simple example is as follows. Simply rewrite the `forward` method in the subclass of `Agent`. The `forward` method is the workflow of an agent.

```python
import asyncio

import ray

from agentsociety.agent import CitizenAgentBase
from agentsociety.agent.agent_base import AgentToolbox
from agentsociety.memory import Memory
from agentsociety.simulation import AgentSociety


class CustomAgent(CitizenAgentBase):

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
        agent_params: Optional[Any] = None,
        blocks: Optional[list[Block]] = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
            agent_params=agent_params,
            blocks=blocks,
        )

    async def before_forward(self):
        # If your agent has some specific logic before forward, you can implement it here.
        await super().before_forward()
        print(f"CustomAgent before forward at {self.environment.get_tick()}")

    async def after_forward(self):
        # If your agent has some specific logic after forward, you can implement it here.
        await super().after_forward()
        print(f"CustomAgent after forward at {self.environment.get_tick()}")

    async def forward(self):
        await self.update_motion()
        tick = self.environment.get_tick()
        print(f"CustomAgent forward at {tick}")

    async def reset(self):
        # You should implement your own reset logic here.
        # For example, you can reset the position of the agent, as we return home at the end of each day.
        # like we did in the `societyagent` file.
        # """Reset the agent."""
        # # reset position to home
        # await self.reset_position()

        # # reset needs
        # await self.memory.status.update("current_need", "none")

        # # reset plans and actions
        # await self.memory.status.update("current_plan", {})
        # await self.memory.status.update("execution_context", {})

        # # reset initial flag
        # await self.plan_and_action_block.reset()
        pass


config = Config(
    ...
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class=CustomAgent,
                number=1,
                memory_config_func=memory_config_societyagent,
                memory_distributions=cast(
                    dict[str, Union[Distribution, DistributionConfig]],
                    DEFAULT_DISTRIBUTIONS,
                ),
            ),
        ]
    ),
    ...
)


async def main():
    agentsociety = AgentSociety(config)
    await agentsociety.init()
    await agentsociety.run()
    await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

## 2. Enhance Your Agent with `Block`

For complex behaviors, you can use `Block` to organize logic.

### What is a `Block`?

A `Block` is a foundational component that encapsulates modular functionality, idealy represents a specific functional behavior. Each Block has:

- Configurable fields with default values and descriptions
- Access to core tools like LLM, Memory, and Environment
- A standardized interface through the `forward` method
- Support for hierarchical composition through nested sub-blocks

### Key Features

- **Configurable Parameters**: Define adjustable fields through `configurable_fields`, `default_values`, and `fields_description`
- **Configuration Management**: Methods to export/import block configurations
- **Hierarchical Design**: Support for nested blocks to build complex behaviors
- **Event-Driven Control**: Optional trigger-based execution flow

### Block Workflow

The core logic of a Block is defined in its `forward` method, which:

- Takes simulation step and context parameters
- Performs the block's specific reasoning or processing tasks
- Can call other blocks' forward methods asynchronously
- Must be implemented by subclasses

### Execution Control

Blocks support event-driven execution through the `EventTrigger` system:

- Pass an `EventTrigger` during Block initialization
- The trigger monitors conditions before block execution
- Block's forward method only runs after trigger conditions are met
- Ensures dependencies and prerequisites are satisfied

This modular architecture promotes:
- Code reusability
- Systematic behavior composition  
- Clear separation of concerns
- Flexible execution control

### Implementation Example

```python
import asyncio

import ray

from agentsociety.agent import CitizenAgentBase
from agentsociety.agent.agent_base import AgentToolbox
from agentsociety.agent.block import Block
from agentsociety.configs import Config
from agentsociety.memory import Memory
from agentsociety.simulation import AgentSociety


class SecondCustomBlock(Block):

    def __init__(
        self,
    ):
        super().__init__(
            name="SecondCustomBlock",
        )

    async def forward(self):
        return f"SecondCustomBlock forward!"

    async def reset(self):
        # Reset the block, if there is any state in the block.
        # Based on your own logic.
        pass


class FirstCustomBlock(Block):
    second_block: SecondCustomBlock

    def __init__(
        self,
    ):
        super().__init__(
            name="FirstCustomBlock",
        )
        self.second_block = SecondCustomBlock()

    async def forward(self):
        first_log = f"FirstCustomBlock forward!"
        second_log = await self.second_block.forward()
        print(first_log)
        print(second_log)

    async def reset(self):        
        # Reset the block, if there is any state in the block.
        # Based on your own logic.
        pass


class CustomAgent(CitizenAgentBase):
    first_block: FirstCustomBlock
    second_block: SecondCustomBlock

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
        )
        self.first_block = FirstCustomBlock()
        self.second_block = SecondCustomBlock()

    async def forward(self):
        await self.first_block.forward()
        await self.second_block.forward()

    async def reset(self):
        # You should implement your own reset logic here.
        pass

config = Config(
    ...
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class=CustomAgent,
                number=1,
                memory_config_func=memory_config_societyagent,
                memory_distributions=cast(
                    dict[str, Union[Distribution, DistributionConfig]],
                    DEFAULT_DISTRIBUTIONS,
                ),
            ),
        ],
    ),
)


async def main():
    agentsociety = AgentSociety(config)
    await agentsociety.init()
    await agentsociety.run()
    await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```


## 3. Using Self-defined Agents in Your Experiment

Set your agent classes and their count with `AgentsConfig` in `Config`.

Each of the `AgentConfig` should contain:

- `agent_class`: The class of the agent
- `number`: The number of agents
- `memory_config_func`: The function to configure the memory of the agent

Each input agent class should inherit from specific agent class.
For example, if you give a list of AgentConfig for `citizens`, each agent class should inherit from `CitizenAgentBase`.
Each agent class is as follows:
- citizens: `CitizenAgentBase`
- firms: `FirmAgentBase`
- banks: `BankAgentBase`
- nbs: `NBSAgentBase`
- governments: `GovernmentAgentBase`

```python
config = Config(
    ...
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class=CustomAgent,
                number=1,
                memory_config_func=memory_config_societyagent,
            ),
        ],
    ),
)
``` 
