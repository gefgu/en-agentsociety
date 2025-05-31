# Distributed Simulation

Here is a simple example to run simulation in the same LAN.
```python
import asyncio
from typing import Any, Literal, Union, cast

import ray
from agentsociety.configs import (AgentsConfig, Config, EnvConfig, ExpConfig,AdvancedConfig,
                                  LLMConfig, MapConfig)
from agentsociety.configs.agent import AgentClassType, AgentConfig
from agentsociety.configs.exp import WorkflowStepConfig, WorkflowType
from agentsociety.environment import EnvironmentConfig, SimulatorConfig
from agentsociety.metrics import MlflowConfig
from agentsociety.simulation import AgentSociety
from agentsociety.cityagent import default

ray.init(address="auto")


config = Config(
    ...
    advanced=AdvancedConfig(
        simulator=SimulatorConfig(
            primary_node_ip="127.0.0.1",
            log_dir="./log",
            max_process=1,
            logging_level="INFO",
        ), 
        group_size=1,
        logging_level="INFO",
    ), # type: ignore
)
config = default(config)


async def main():
    agentsociety = AgentSociety(config)
    await agentsociety.init()
    await agentsociety.run()
    await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

```

```{admonition} Caution
:class: caution
- mlflow server should be accessible for all nodes.
- primary node ip should be accessible for all nodes.
- map file path should be accessible for main node.
```
