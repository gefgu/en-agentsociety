# Economy Simulator

The Economy Client serves as a centralized economic settlement system that manages monetary flows between company entities and citizen entities in the simulation environment.  

## Usage Example

```python
from agentsociety import Agent, AgentType
from agentsociety.environment import EconomyClient


class CustomAgent(Agent):
    def __init__(self, name: str, economy_client: EconomyClient, **kwargs):
        super().__init__(
            name=name, economy_client=economy_client, type=AgentType.Citizen, **kwargs
        )

    async def forward(
        self,
    ):
        economy_client = self.economy_client
        # update currency
        await economy_client.update(AGENT_ID, "currency", 200.0)
        # consumption
        real_consumption = await economy_client.calculate_consumption(
            FIRM_ID,
            AGENT_ID,
            DEMAND_EACH_FIRM,
        )
        # bank interest
        await economy_client.calculate_interest(
            BANK_ID,
            AGENT_ID,
        )
```
