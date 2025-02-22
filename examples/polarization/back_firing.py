import asyncio
import json
import logging
import os
import random

import ray
from message_agent import AgreeAgent, DisagreeAgent

from agentsociety import AgentSimulation
from agentsociety.cityagent import memory_config_societyagent
from agentsociety.cityagent.societyagent import SocietyAgent
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=True)


async def update_attitude(simulation: AgentSimulation):
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    agree_agent_uuid = await simulation.filter(types=[AgreeAgent])
    agree_agent_uuid = agree_agent_uuid[0]
    disagree_agent_uuid = await simulation.filter(types=[DisagreeAgent])
    disagree_agent_uuid = disagree_agent_uuid[0]
    agree_friends = []
    disagree_friends = []
    for agent in citizen_uuids:
        if random.random() < 0.5:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 3}
            )
            disagree_friends.append(agent)
        else:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 7}
            )
            agree_friends.append(agent)
        # remove original social network
        await simulation.update(agent, "friends", [])
    await simulation.update(agree_agent_uuid, "friends", disagree_friends)
    await simulation.update(disagree_agent_uuid, "friends", agree_friends)
    attitudes = await simulation.gather("attitude", citizen_uuids)
    with open(f"exp3/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)


async def gather_attitude(simulation: AgentSimulation):
    print("gather attitude")
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    attitudes = await simulation.gather("attitude", citizen_uuids)

    with open(f"exp3/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    chat_histories = await simulation.gather("chat_histories", citizen_uuids)
    with open(f"exp3/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)


sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest()
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
)
exp_config = (
    ExpConfig(exp_name="cognition_exp3", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
        extra_agent_class={DisagreeAgent: 1, AgreeAgent: 1},
        memory_config_func={
            DisagreeAgent: memory_config_societyagent,
            AgreeAgent: memory_config_societyagent,
        },
    )
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_attitude,
                description="update attitude",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=2),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_attitude,
                description="gather attitude",
            ),
        ]
    )
)


async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    os.makedirs("exp3", exist_ok=True)
    asyncio.run(main())
