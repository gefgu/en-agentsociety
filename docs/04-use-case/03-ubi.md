# Universal Basic Income (UBI)

Our experiment simulates the impact of a Universal Basic Income (UBI) policy, granting each agent $1,000 monthly, on the socio-economic environment of Texas, USA, comparing macroeconomic outcomes such as real GDP and consumption levels with and without UBI intervention.

Codes are available at [UBI](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/UBI).

## Run the Codes

```bash
cd examples/UBI
python main.py
```

## Step-by-Step Code Explanation

## `main.py`

### Tool Functions

`economy_metric` extracts econmoy metrics, including `'price', 'working_hours', 'depression', 'consumption', 'income'` from simulation and exports them to the MLflow.
```python
async def economy_metric(simulation):
    if not hasattr(economy_metric, 'nbs_id'):
        economy_metric.nbs_id = None
    if not hasattr(economy_metric, 'nbs_uuid'):
        economy_metric.nbs_uuid = None

    if economy_metric.nbs_id is None:
        nbs_id = await simulation.economy_client.get_org_entity_ids(economyv2.ORG_TYPE_NBS)
        nbs_id = nbs_id[0]
        economy_metric.nbs_id = nbs_id
    if economy_metric.nbs_uuid is None:
        nbs_uuids = await simulation.filter(types=[NBSAgent])
        economy_metric.nbs_uuid = nbs_uuids[0]
    
    try:
        real_gdp = await simulation.economy_client.get(economy_metric.nbs_id, 'real_gdp')
    except:
        real_gdp = []
    if len(real_gdp) > 0:
        real_gdp = real_gdp[-1]
        forward_times_info = await simulation.gather("forward_times", [economy_metric.nbs_uuid])
        step_count = 0
        for group_gather in forward_times_info:
            for agent_uuid, forward_times in group_gather.items():
                if agent_uuid == economy_metric.nbs_uuid:
                    step_count = forward_times
        await simulation.mlflow_client.log_metric(key="real_gdp", value=real_gdp, step=step_count)
        other_metrics = ['prices', 'working_hours', 'depression', 'consumption_currency', 'income_currency']
        other_metrics_names = ['price', 'working_hours', 'depression', 'consumption', 'income']
        for metric, metric_name in zip(other_metrics, other_metrics_names):
            metric_value = (await simulation.economy_client.get(economy_metric.nbs_id, metric))[-1]
            await simulation.mlflow_client.log_metric(key=metric_name, value=metric_value, step=step_count)

```

`gather_ubi_opinions` gathers the opinions of all citizens for Universal Basic Income.

```python
import asyncio
import json
import logging
import pickle as pkl

import ray

from agentsociety import AgentSimulation
from agentsociety.cityagent import memory_config_societyagent
from agentsociety.cityagent.initial import (bind_agent_info,
                                            initialize_social_network)
from agentsociety.cityagent.metrics import economy_metric
from agentsociety.cityagent.societyagent import SocietyAgent
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=False)


async def gather_ubi_opinions(simulation: AgentSimulation):
    citizen_agents = await simulation.filter(types=[SocietyAgent])
    opinions = await simulation.gather("ubi_opinion", citizen_agents)
    with open("opinions.pkl", "wb") as f:
        pkl.dump(opinions, f)
```

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=1)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
    .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
    .SetMetricRequest(
        username="mlflow_user", password="mlflow_pass", mlflow_uri="http://mlflow:5000"
    )
)
exp_config = (
    ExpConfig(
        exp_name="allinone_economy", llm_semaphore=200, logging_level=logging.INFO
    )
    .SetAgentConfig(
        number_of_citizen=100,
        number_of_firm=5,
        memory_config_func={SocietyAgent: memory_config_societyagent},
        agent_class_configs={
            SocietyAgent: json.load(open("society_agent_config.json"))
        },
        init_func=[bind_agent_info, initialize_social_network],
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=10, times=1, description=""),
        ]
    )
    .SetMetricExtractors(
        metric_extractors=[(1, economy_metric), (12, gather_ubi_opinions)]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`, and 5 firms with `number_of_firm=5`.

The workflow has one step and is to simulate for 10 days, providing enough time for agents to evolve their opinions.

Two metric extractors are set here. Constantly export metric to the MLflow with `economy_metric` and gather opinions on UBI every 12 steps with `gather_ubi_opinions`.

### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.
