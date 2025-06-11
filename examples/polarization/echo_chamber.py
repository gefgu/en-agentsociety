import asyncio
import logging
import os
import random

import ray
from message_agent import AgreeAgent, DisagreeAgent

from agentsociety.cityagent import (
    SocietyAgent,
    default,
)
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.configs.agent import AgentConfig
from agentsociety.configs.exp import (
    AgentFilterConfig,
    WorkflowStepConfig,
    WorkflowType,
)
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.simulation import AgentSociety
from agentsociety.storage import DatabaseConfig

ray.init(logging_level=logging.INFO)


async def update_attitude(simulation: AgentSociety):
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    agree_agent_id = await simulation.filter(types=(AgreeAgent,))
    agree_agent_id = agree_agent_id[0]
    disagree_agent_id = await simulation.filter(types=(DisagreeAgent,))
    disagree_agent_id = disagree_agent_id[0]
    agree_friends = []
    disagree_friends = []
    for agent_id in citizen_ids:
        if random.random() < 0.5:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 3}
            )
            disagree_friends.append(agent_id)
        else:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 7}
            )
            agree_friends.append(agent_id)
        # remove original social network
        await simulation.update([agent_id], "friends", [])
    await simulation.update([agree_agent_id], "friends", agree_friends)
    await simulation.update([disagree_agent_id], "friends", disagree_friends)


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
        db=DatabaseConfig(
            enabled=True,
            db_type="sqlite",
            pg_dsn=None,
        ),
    ),
    map=MapConfig(
        file_path="<MAP-FILE-PATH>",
    ),
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class="citizen",
                number=100,
            ),
            AgentConfig(
                agent_class=AgreeAgent,
                number=1,
            ),
            AgentConfig(
                agent_class=DisagreeAgent,
                number=1,
            ),
        ],
    ),  # type: ignore
    exp=ExpConfig(
        name="polarization_echo_chamber",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.FUNCTION,
                func=update_attitude,
            ),
            WorkflowStepConfig(
                type=WorkflowType.SAVE_CONTEXT,
                target_agent=AgentFilterConfig(
                    agent_class=(SocietyAgent,),
                ),
                key="attitude",
                save_as="guncontrol_attitude_initial",
            ),
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=3,
            ),
            WorkflowStepConfig(
                type=WorkflowType.SAVE_CONTEXT,
                target_agent=AgentFilterConfig(
                    agent_class=(SocietyAgent,),
                ),
                key="attitude",
                save_as="guncontrol_attitude_final",
            ),
            WorkflowStepConfig(
                type=WorkflowType.SAVE_CONTEXT,
                target_agent=AgentFilterConfig(
                    agent_class=(SocietyAgent,),
                ),
                key="chat_histories",
                save_as="guncontrol_chat_histories",
            ),
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
        ),
    ),
)
config = default(config)


async def main():
    agentsociety = AgentSociety(config)
    try:
        await agentsociety.init()
        await agentsociety.run()
    finally:
        await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    os.makedirs("exp2", exist_ok=True)
    asyncio.run(main())
