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


async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
