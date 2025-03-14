import asyncio
import json
import logging
from functools import partial
from typing import Literal, Union

import ray
from hurrican_memory_config import memory_config_societyagent_hurrican

from agentsociety import AgentSimulation
from agentsociety.cityagent import SocietyAgent
from agentsociety.cityagent.metrics import mobility_metric
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=False)


async def update_weather_and_temperature(
    weather: Union[Literal["wind"], Literal["no-wind"]], simulation: AgentSimulation
):
    if weather == "wind":
        await simulation.update_environment(
            "weather",
            "Hurricane Dorian has made landfall in other cities, travel is slightly affected, and winds can be felt",
        )
    elif weather == "no-wind":
        await simulation.update_environment(
            "weather", "The weather is normal and does not affect travel"
        )
    else:
        raise ValueError(f"Invalid weather {weather}")


sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest()
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
    .SetPostgreSql(dsn="postgresql://user:pass@localhost:5432/db", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="hurrican", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=1000,
        group_size=50,
        memory_config_func={SocietyAgent: memory_config_societyagent_hurrican},
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=partial(update_weather_and_temperature, "wind"),
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=partial(update_weather_and_temperature, "no-wind"),
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
        ]
    )
    .SetMetricExtractors(metric_extractors=[(1, mobility_metric)])
)


async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
