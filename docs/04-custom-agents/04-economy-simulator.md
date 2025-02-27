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

## Core APIs

- Agent & Organization Management
  - `add_agents`: Creates new economic actors with configurable financial attributes.
  - `add_orgs`: Establishes economic institutions (banks, firms, governments, etc.) with specified initial states.
  - `get_agent`/`get_org`: Retrieves details about economic entities by ID.
  - `remove_agents`/`remove_orgs`: Removes entities from the economic system.
  
- Economic Operations
  - `calculate_taxes_due`: Computes tax obligations based on income and government tax brackets.
  - `calculate_consumption`: Processes consumer purchases, updating inventory and currency for both buyers and sellers.
  - `calculate_interest`: Applies bank interest rates to account balances for specified agents.
  - `calculate_real_gdp`: Generates macroeconomic indicators for the simulation economy.

- Data Access & Modification
  - `get`: Retrieves specific attribute values from economic entities.
  - `update`: Modifies entity attributes using either "replace" or "merge" modes.
  - `add_delta_value`: Incrementally adjusts numeric values (currency, inventory, price, etc.).

- Persistence
  - `save`: Serializes the current economic state to a file.
  - `load`: Reconstructs the economic system from a saved state file.
  - `get_org_entity_ids`: Retrieves IDs for all organizations of a specified type.

- Monitoring
  - `get_log_list`/`clear_log_list`: Provides access to performance and operation logs.
