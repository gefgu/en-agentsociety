import asyncio
import logging
import pickle as pkl

import ray

from agentsociety.cityagent import (
    SocietyAgent,
    default,
)
from agentsociety.cityagent.metrics import economy_metric
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.configs.agent import AgentConfig, InstitutionAgentClass
from agentsociety.configs.exp import (
    MetricExtractorConfig,
    MetricType,
    WorkflowStepConfig,
    WorkflowType,
)
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.metrics import MlflowConfig, MlflowConfig
from agentsociety.simulation import AgentSociety
from agentsociety.storage import AvroConfig, PostgreSQLConfig

ray.init(logging_level=logging.INFO)


async def gather_ubi_opinions(simulation: AgentSociety):
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    opinions = await simulation.gather(
        "ubi_opinion", citizen_ids, flatten=True, keep_id=True
    )
    with open("opinions.pkl", "wb") as f:
        pkl.dump(opinions, f)


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
                number=1,
            ),
        ],
    ),  # type: ignore
    exp=ExpConfig(
        name="ubi_experiment",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=10,
            )
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
        ),
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=economy_metric, step_interval=1
            ),
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=gather_ubi_opinions, step_interval=12
            ),
        ],
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
    asyncio.run(main())
