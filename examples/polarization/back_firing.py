import asyncio
import json
import logging
import os
import random
from typing import Union, cast

import ray
from message_agent import AgreeAgent, DisagreeAgent

from agentsociety.agent.distribution import Distribution, DistributionConfig
from agentsociety.cityagent import (
    DEFAULT_DISTRIBUTIONS,
    SocietyAgent,
    default,
    memory_config_societyagent,
)
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.configs.agent import AgentClassType, AgentConfig
from agentsociety.configs.exp import WorkflowStepConfig, WorkflowType
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.message import RedisConfig
from agentsociety.metrics import MlflowConfig
from agentsociety.simulation import AgentSociety
from agentsociety.storage import AvroConfig, PostgreSQLConfig

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
    await simulation.update([agree_agent_id], "friends", disagree_friends)
    await simulation.update([disagree_agent_id], "friends", agree_friends)
    attitudes = await simulation.gather("attitude", citizen_ids)
    with open(f"exp3/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)


async def gather_attitude(simulation: AgentSociety):
    print("gather attitude")
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    attitudes = await simulation.gather("attitude", citizen_ids)

    with open(f"exp3/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    chat_histories = await simulation.gather("chat_histories", citizen_ids)
    with open(f"exp3/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)


distributions = cast(
    dict[str, Union[Distribution, DistributionConfig]],
    DEFAULT_DISTRIBUTIONS,
)


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
                agent_class=AgentClassType.CITIZEN,
                number=100,
            ),
            AgentConfig(
                agent_class=AgreeAgent,
                number=1,
                memory_config_func=memory_config_societyagent,
                memory_distributions=distributions,
            ),
            AgentConfig(
                agent_class=DisagreeAgent,
                number=1,
                memory_config_func=memory_config_societyagent,
                memory_distributions=distributions,
            ),
        ]
    ),  # type: ignore
    exp=ExpConfig(
        name="polarization_back_firing",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.FUNCTION,
                func=update_attitude,
            ),
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=3,
            ),
            WorkflowStepConfig(
                type=WorkflowType.FUNCTION,
                func=gather_attitude,
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
    os.makedirs("exp3", exist_ok=True)
    asyncio.run(main())
