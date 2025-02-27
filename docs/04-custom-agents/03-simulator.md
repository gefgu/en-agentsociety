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

## Core APIs

- Environment Control
  - `get_time`: Retrieves the current simulation time, either as seconds since midnight or formatted as a string.
  - `get_simulator_day`: Returns the current day number in the simulation.
  - `get_simulator_second_from_start_of_day`: Returns seconds elapsed since the beginning of the current simulation day.

- Environmental Parameters
  - `set_environment`: Sets global environmental conditions that affect all agents.
  - `update_environment`: Updates a specific environmental parameter (weather, crime rate, etc.).
  - `sence`: Retrieves a specific environmental parameter value.

- Spatial Navigation
  - `get_poi_categories`: Retrieves unique categories of points of interest within a specified radius.
  - `get_around_poi`: Finds points of interest of specific types within a given radius.
  
- Agent Management
  - `get_person`: Retrieves detailed information about a specific person/agent.
  - `add_person`: Adds a new person to the simulation environment.
  - `set_aoi_schedules`: Programs movement schedules for an agent to visit 
  - `reset_person_position`: Immediately repositions an agent to a specified location.
  
- Simulation Control
  - `step`: Advances the simulation by `n` steps (primary node only).
  
- Monitoring
  - `get_log_list`/`clear_log_list`: Provides access to performance and operation logs.
