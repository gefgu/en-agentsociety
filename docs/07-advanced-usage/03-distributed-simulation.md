# Distributed Simulation

Here is a simple example to run simulation in the same LAN.

```python
import asyncio
import logging

import ray

from agentsociety import AgentSimulation
from agentsociety.cityagent import (BankAgent, FirmAgent, GovernmentAgent,
                                   NBSAgent, SocietyAgent)
from agentsociety.cityagent.initial import (bind_agent_info,
                                           initialize_social_network)
from agentsociety.configs import SimConfig
from agentsociety.simulation import AgentSimulation

sim_config = (
    SimConfig()
    .SetLLMRequest(request_type="zhipuai", api_key="", model="GLM-4-Flash")
    .SetSimulatorRequest(min_step_time=1, primary_node_ip="<YOUR-PRIMARY-IP>")
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    .SetMapRequest(file_path="./ignore/map.pb")
    .SetMetricRequest(
        username="mlflow_user", password="mlflow_pass", mlflow_uri="http://mlflow:5000"
    )
)


async def run_simulation():
    simulation = AgentSimulation(
        config=sim_config,
        exp_name="system_log",
        logging_level=logging.INFO,
    )
    await simulation.init_agents(
        agent_count={
            SocietyAgent: 50,
            FirmAgent: 1,
            GovernmentAgent: 1,
            BankAgent: 1,
            NBSAgent: 1,
        },
    )
    await bind_agent_info(simulation)
    await initialize_social_network(simulation)


async def run_experiments():
    ray.init(address="auto")
    await run_simulation()


if __name__ == "__main__":
    asyncio.run(run_experiments())

```

```{admonition} Caution
:class: caution
- `SetMQTT`: `server` should be accessible for all nodes.
- `SetMetricRequest`: `mlflow_uri` should be accessible for all nodes. 
- `SetSimulatorRequest`: `primary_node_ip` should be accessible for all nodes. 
- `SetMapRequest`: the `file_path` is for the primary node.
```

## AgentGroup Configuration

In our framework, agents are grouped into several `AgentGroup`s, and each `AgentGroup` works as a `Ray` actor.

## `ExpConfig.AgentConfig`

- `group_size`: controls the agent num for each `AgentGroup`, directly affect the computing pressure for a `Ray` actor.
