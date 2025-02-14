# External Shocks of Hurricane

The experiment focuses on analyzing the impact of Hurricane Dorian on human mobility in Columbia, South Carolina, using SafeGraph and Census Block Group data to model the movement behaviors of 1,000 social agents.

Codes are available at [Hurricane](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/mobility).

## Run the Codes

```bash
cd examples/mobility
python hurricane.py
```

## Step-by-Step Code Explanation

## `hurrican.py`

### Tool Functions

`mobility_metric` extracts agent mobility metrics, including the average visited POI num and total vistied POI num for all agents from simulation and exports them to the MLflow.
```python
async def mobility_metric(simulation):
    if not hasattr(mobility_metric, 'step_count'):
        mobility_metric.step_count = 0
    citizen_agents = await simulation.filter(types = [SocietyAgent])
    poi_visited_info = await simulation.gather( "number_poi_visited", citizen_agents)
    poi_visited_sum = 0
    for group_gather in poi_visited_info:
        for agent_uuid, poi_visited in group_gather.items():
            poi_visited_sum += poi_visited
    average_poi_visited = float(poi_visited_sum / len(citizen_agents))
    print(f"Metric: Average POIs visited: {average_poi_visited}")
    await simulation.mlflow_client.log_metric(key="average_poi_visited", value=average_poi_visited, step=mobility_metric.step_count)
    await simulation.mlflow_client.log_metric(key="poi_visited_sum", value=poi_visited_sum, step=mobility_metric.step_count)
    mobility_metric.step_count += 1
```

`update_weather_and_temperature` sets the global environment statusfor the simulation. This function sets the environment as wind affected on the first calling, and no-wind affected on following callings. 

```python
import asyncio
import json
import logging

import ray
from hurrican_memory_config import memory_config_societyagent_hurrican

from agentsociety import AgentSimulation
from agentsociety.cityagent import SocietyAgent
from agentsociety.cityagent.metrics import mobility_metric
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=False)


async def update_weather_and_temperature(simulation: AgentSimulation):
    if not hasattr(update_weather_and_temperature, "trigger_time"):
        update_weather_and_temperature.trigger_time = 0
    if update_weather_and_temperature.trigger_time == 0:
        await simulation.update_environment(
            "weather",
            "Hurricane Dorian has made landfall in other cities, travel is slightly affected, and winds can be felt",
        )
        update_weather_and_temperature.trigger_time = 1
    if update_weather_and_temperature.trigger_time == 1:
        await simulation.update_environment(
            "weather", "The weather is normal and does not affect travel"
        )
```

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=100)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
    .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="hurrican", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=1000,
        number_of_firm=50,
        group_size=50,
        memory_config_func={SocietyAgent: memory_config_societyagent_hurrican},
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE, func=update_weather_and_temperature
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE, func=update_weather_and_temperature
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
        ]
    )
    .SetMetricExtractors(metric_extractors=[(1, mobility_metric)])
)
```
Initialize 100 agents with `number_of_citizen=100`.

The overall workflow contains five steps.
- Step1: simulate for 3 days.
- Step2: set the weather as wind-affected with `update_weather_and_temperature`.
- Step3: simulate for 3 days.
- Step4: set the weather as normal with `update_weather_and_temperature`.
- Step5: simulate for 3 days.

Only one metric extractor is set here. Constantly export metric to the MLflow with `mobility_metric`.

### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.
