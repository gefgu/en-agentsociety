import asyncio
import json
import logging
import os
import random

import ray

from agentsociety.cityagent import SocietyAgent, default
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.configs.agent import AgentConfig
from agentsociety.configs.exp import WorkflowStepConfig, WorkflowType
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.metrics import MlflowConfig
from agentsociety.simulation import AgentSociety
from agentsociety.storage import AvroConfig, PostgreSQLConfig

ray.init(logging_level=logging.INFO)


async def update_attitude(simulation: AgentSociety):
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    for agent_id in citizen_ids:
        if random.random() < 0.5:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 3}
            )
        else:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 7}
            )
    attitudes = await simulation.gather("attitude", citizen_ids)
    with open(f"exp1/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)


async def gather_attitude(simulation: AgentSociety):
    print("gather attitude")
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    attitudes = await simulation.gather("attitude", citizen_ids)

    with open(f"exp1/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    group_chat_histories: list[dict[int, dict[str, str]]] = await simulation.gather(
        "chat_histories", citizen_ids
    )
    chat_histories: dict[int, dict[str, str]] = {}
    for group_history in group_chat_histories:
        for agent_id in group_history.keys():
            chat_histories[agent_id] = group_history[agent_id]
    with open(f"exp1/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)


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
        pgsql=PostgreSQLConfig(
            enabled=True,
            dsn="<PGSQL-DSN>",
            num_workers="auto",
        ),
        avro=AvroConfig(
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
                agent_class="citizen",
                number=100,
            )
        ]
    ),  # type: ignore
    exp=ExpConfig(
        name="polarization_control",
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
    os.makedirs("exp1", exist_ok=True)
    asyncio.run(main())
