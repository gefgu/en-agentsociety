# Metrics Collection

The metrics management system, encapsulated within the `MlflowClient` class is designed to streamline the process of connecting to, logging data with, and managing experiments in [MLflow](https://mlflow.org/).

## MLflow Integration

```{admonition} Caution
:class: caution
To use `MlflowClient`, you have to deploy MLflow first.
Check [prerequisites](../01-quick-start.md/#prerequisites) for details.
```

The `MlflowClient` is the main class to manage experiment tracking.

### Usage Example 

We have implemented pre-defined tools (`agentsociety.tools.ExportMlflowMetrics`) for MLflow integration. The example is as follows.

```python
from agentsociety import Agent, AgentType
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.simulation import AgentSimulation
from agentsociety.tools import ExportMlflowMetrics


class CustomAgent(Agent):
    export_metric = ExportMlflowMetrics()

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, type=AgentType.Citizen, **kwargs)

    async def forward(
        self,
    ):
        # Export metric to MLflow
        # ------------------------------------------------------------------------#
        await self.export_metric(
            {"key": await self.simulator.get_time()}, clear_cache=True
        )
        # ------------------------------------------------------------------------#


sim_config = (
    SimConfig()
    .SetLLMRequest(request_type="zhipuai", api_key="", model="GLM-4-Flash")
    .SetSimulatorRequest(min_step_time=1)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    .SetMapRequest(file_path="./ignore/map.pb")
    .SetMetricRequest(
        username="mlflow_user", password="mlflow_pass", mlflow_uri="http://mlflow:5000"
    )
    .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="test", llm_semaphore=201)
    .SetAgentConfig(
        number_of_citizen=50,
        extra_agent_class={CustomAgent: 1},
    )
    .SetWorkFlow([WorkflowStep(type="run", days=1)])
    .SetMessageIntercept(mode="point", max_violation_time=3)
)


async def main():
    simulation = AgentSimulation.run_from_config(
        config=exp_config,
        sim_config=sim_config,
    )
    await simulation


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

```
