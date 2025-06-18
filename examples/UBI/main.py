import asyncio

from agentsociety.cityagent import (
    MobilityBlock,
    MobilityBlockParams,
    SocialBlock,
    SocialBlockParams,
    EconomyBlock,
    EconomyBlockParams,
    OtherBlock,
    OtherBlockParams,
    SocietyAgent,
    NBSAgent,
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
    MetricExtractorConfig,
    MetricType,
    WorkflowStepConfig,
    WorkflowType,
)
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.simulation import AgentSociety
from agentsociety.storage import DatabaseConfig


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
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.STATE,
                step_interval=10,
                target_agent=AgentFilterConfig(agent_class=(NBSAgent,)),
                key="real_gdp_metric",
                description="Extract real GDP metric value from NBSAgent",
            ),
            MetricExtractorConfig(
                type=MetricType.STATE,
                step_interval=10,
                target_agent=AgentFilterConfig(agent_class=(NBSAgent,)),
                key="price_metric",
                description="Extract price metric value from NBSAgent",
            ),
            MetricExtractorConfig(
                type=MetricType.STATE,
                step_interval=10,
                target_agent=AgentFilterConfig(agent_class=(NBSAgent,)),
                key="working_hours_metric",
                description="Extract working hours metric value from NBSAgent",
            ),
            MetricExtractorConfig(
                type=MetricType.STATE,
                step_interval=10,
                target_agent=AgentFilterConfig(agent_class=(NBSAgent,)),
                key="depression_metric",
                description="Extract depression metric value from NBSAgent",
            ),
            MetricExtractorConfig(
                type=MetricType.STATE,
                step_interval=10,
                target_agent=AgentFilterConfig(agent_class=(NBSAgent,)),
                key="consumption_currency_metric",
                description="Extract consumption currency metric value from NBSAgent",
            ),
            MetricExtractorConfig(
                type=MetricType.STATE,
                step_interval=10,
                target_agent=AgentFilterConfig(agent_class=(NBSAgent,)),
                key="income_currency_metric",
                description="Extract income currency metric value from NBSAgent",
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


if __name__ == "__main__":
    asyncio.run(main())
