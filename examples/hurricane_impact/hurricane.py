import asyncio

from en_agentsociety.cityagent import default
from en_agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from en_agentsociety.configs.agent import AgentConfig
from en_agentsociety.configs.exp import WorkflowStepConfig, WorkflowType
from en_agentsociety.environment import EnvironmentConfig
from en_agentsociety.llm import LLMProviderType
from en_agentsociety.simulation import AgentSociety
from en_agentsociety.storage import DatabaseConfig


config = Config(
    llm=[
        LLMConfig(
            provider=LLMProviderType.Qwen,
            base_url=None,
            api_key="<YOUR-API-KEY>",
            model="<YOUR-MODEL>",
            concurrency=200,
            timeout=60,
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
                memory_from_file="profiles_hurricane.json",
            )
        ],
    ),  # type: ignore
    exp=ExpConfig(
        name="hurricane_impact",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=3,
            ),
            WorkflowStepConfig(
                type=WorkflowType.ENVIRONMENT_INTERVENE,
                key="weather",
                value="Hurricane Dorian has made landfall in other cities, travel is slightly affected, and winds can be felt.",
            ),
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=3,
            ),
            WorkflowStepConfig(
                type=WorkflowType.ENVIRONMENT_INTERVENE,
                key="weather",
                value="The weather is normal and does not affect travel",
            ),
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=3,
            ),
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
        ),
    ),
)
config = default(config)


async def main():
    agentsociety = AgentSociety.create(config)
    try:
        await en_agentsociety.init()
        await en_agentsociety.run()
    finally:
        await en_agentsociety.close()


if __name__ == "__main__":
    asyncio.run(main())
