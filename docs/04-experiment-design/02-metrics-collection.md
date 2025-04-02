# Metrics Collection

The metrics management system, encapsulated within the `MlflowClient` class is designed to streamline the process of connecting to, logging data with, and managing experiments in [MLflow](https://mlflow.org/).

```{admonition} Caution
:class: caution
To integrate with `MLflow`, you have to deploy it first.
Check [prerequisites](./01-quick-start/01-prerequisites.md) for details.
```

## Metric Extractor

We provide a flexible way to collect metrics during experiments, just need to specify your metric extractor in the experiment config.
There are two main types of metric extractors:

1. **Function-based metrics**: Custom functions that extract metrics from the simulation
2. **State-based metrics**: Metrics collected directly from agent states, `target_agent` is required.

Check `agentsociety.cityagent.metrics` for pre-defined metrics.

You can also define your own metric extractor, an example is as follows.

```python
from agentsociety.cityagent import SocietyAgent
from agentsociety.simulation import AgentSociety

async def gather_ids(simulation: AgentSociety):
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    ids = await simulation.gather("id", citizen_ids)
    return ids

config = Config(
    ...
    exp=ExpConfig(
        ...
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=gather_ids, step_interval=12
            ),
        ],
    ),
)

```

## Agent and MLflow Integration

The `MlflowClient` is the main class to manage experiment tracking.

### Usage Example 

We have implemented pre-defined tools (`agentsociety.tools.ExportMlflowMetrics`) for MLflow integration. The example is as follows.

```python
import asyncio
from typing import Literal, Union, cast

import ray

from agentsociety.agent import CitizenAgentBase
from agentsociety.agent.agent_base import AgentToolbox
from agentsociety.agent.distribution import Distribution, DistributionConfig
from agentsociety.agent.prompt import FormatPrompt
from agentsociety.cityagent import (
    DEFAULT_DISTRIBUTIONS,
    default,
    memory_config_societyagent,
)
from agentsociety.cityagent.metrics import mobility_metric
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.configs.agent import AgentClassType, AgentConfig
from agentsociety.configs.exp import (
    MetricExtractorConfig,
    MetricType,
    WorkflowStepConfig,
    WorkflowType,
)
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.memory import Memory
from agentsociety.message import RedisConfig
from agentsociety.metrics import MlflowConfig
from agentsociety.simulation import AgentSociety
from agentsociety.storage import AvroConfig, PostgreSQLConfig
from agentsociety.tools import ExportMlflowMetrics
from agentsociety.tools.tool import UpdateWithSimulator


class ToMlFlowAgent(CitizenAgentBase):
    export_metric = ExportMlflowMetrics()
    update_with_sim = UpdateWithSimulator()

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

    async def forward(self):
        # sync agent status with simulator
        await self.update_with_sim()
        # Export metric to MLflow
        # ------------------------------------------------------------------------#
        await self.export_metric({"key": self.environment.get_tick()}, clear_cache=True)
        # ------------------------------------------------------------------------#


config = Config(
    llm=[
        LLMConfig(
            provider=LLMProviderType.Qwen,
            base_url=None,
            api_key="<YOUR-API-KEY>",
            model="<YOUR-MODEL>",
            semaphore=200,
        )
    ],
    env=EnvConfig(
        redis=RedisConfig(
            server="<SERVER-ADDRESS>",
            port=6379,
            password="<PASSWORD>",
        ),  # type: ignore
        pgsql=PostgreSQLConfig(
            enabled=True,
            dsn="<PGSQL-DSN>",
            num_workers="auto",
        ),
        avro=AvroConfig(
            path="<SAVE-PATH>",
            enabled=True,
        ),
        mlflow=MlflowConfig(
            enabled=True,
            mlflow_uri="<MLFLOW-URI>",
            username="<USERNAME>",
            password="<PASSWORD>",
        ),
    ),
    map=MapConfig(
        file_path="<MAP-FILE-PATH>",
        cache_path="<CACHE-FILE-PATH>",
    ),
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class=ToMlFlowAgent,
                number=1,
                memory_config_func=memory_config_societyagent,
                memory_distributions=cast(
                    dict[str, Union[Distribution, DistributionConfig]],
                    DEFAULT_DISTRIBUTIONS,
                ),
            ),
        ]
    ),  # type: ignore
    exp=ExpConfig(
        name="mlflow_test",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.STEP,
                steps=5,
            ),
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
    ),
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
