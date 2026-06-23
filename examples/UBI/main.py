import asyncio

from en_agentsociety.cityagent import (
    MobilityBlock,
    MobilityBlockParams,
    SocialBlock,
    SocialBlockParams,
    EconomyBlock,
    EconomyBlockParams,
    OtherBlock,
    OtherBlockParams,
    SocietyAgent,
    default,
)
from en_agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from en_agentsociety.configs.agent import AgentConfig
from en_agentsociety.configs.exp import (
    AgentFilterConfig,
    WorkflowStepConfig,
    WorkflowType,
)
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
                blocks={
                    MobilityBlock: MobilityBlockParams(),
                    SocialBlock: SocialBlockParams(),
                    EconomyBlock: EconomyBlockParams(
                        UBI=1000, num_labor_hours=168, productivity_per_labor=1
                    ),
                    OtherBlock: OtherBlockParams(),
                },
            ),
        ],
    ),  # type: ignore
    exp=ExpConfig(
        name="ubi_experiment",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=10,
            ),
            WorkflowStepConfig(
                type=WorkflowType.SAVE_CONTEXT,
                target_agent=AgentFilterConfig(
                    agent_class=(SocietyAgent,),
                ),
                key="ubi_opinion",
                save_as="ubi_opinion",
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
