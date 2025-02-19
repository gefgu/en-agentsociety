# Simulator

The Simulator serves as a bridge between agents and the physical entities in the simulation environment.  

## Usage Example

```python
from agentsociety import Agent, AgentType
from agentsociety.environment import Simulator


class CustomAgent(Agent):
    def __init__(self, name: str, simulator: Simulator, **kwargs):
        super().__init__(
            name=name, simulator=simulator, type=AgentType.Citizen, **kwargs
        )

    async def forward(
        self,
    ):
        simulator = self.simulator
        # clock time in the Urban Space
        print(await simulator.get_time())
        # the simulation day till now
        print(await simulator.get_simulator_day())
        # set the global environment prompt
        simulator.set_environment({"weather": "sunny"})
```
