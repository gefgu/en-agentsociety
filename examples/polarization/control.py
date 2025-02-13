import asyncio
import json
import logging
import os
import random

import ray

from agentsociety import AgentSimulation
from agentsociety.cityagent.societyagent import SocietyAgent
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=True)

async def update_attitude(simulation: AgentSimulation):
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    for agent in citizen_uuids:
        if random.random() < 0.5:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 3}
            )
        else:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 7}
            )
    attitudes = await simulation.gather("attitude", citizen_uuids)
    with open(f"exp1/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)


async def gather_attitude(simulation: AgentSimulation):
    print("gather attitude")
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    attitudes = await simulation.gather("attitude", citizen_uuids)

    with open(f"exp1/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    chat_histories = await simulation.gather("chat_histories", citizen_uuids)
    with open(f"exp1/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)



sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
)
exp_config = (
    ExpConfig(exp_name="cognition_exp1", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(number_of_citizen=100, group_size=50)
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_attitude,
                description="update attitude",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_attitude,
                description="gather attitude",
            ),
        ]
    )
)


async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"exp1/llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"exp1/mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"exp1/simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"exp1/agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    os.makedirs("exp1", exist_ok=True)
    asyncio.run(main())
