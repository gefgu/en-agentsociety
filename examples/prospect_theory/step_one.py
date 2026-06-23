import asyncio

from en_agentsociety.cityagent import (
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

from surveys import personality_survey


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
                memory_from_file="./profiles/citizen_profile.json",
            )
        ],
    ),  # type: ignore
    exp=ExpConfig(
        name="prospect_theory_step_one",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.SURVEY,
                survey=personality_survey(),
                target_agent=AgentFilterConfig(
                    agent_class=(SocietyAgent,)
                )
            )
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