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

from surveys import happiness_survey


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
                memory_from_file="./profiles/citizen_profile_with_winner.json",
            )
        ],
    ),  # type: ignore
    exp=ExpConfig(
        name="prospect_theory_step_two",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.SURVEY,
                survey=happiness_survey(),
                target_agent=AgentFilterConfig(
                    agent_class=(SocietyAgent,)
                )
            ),
            WorkflowStepConfig(
                type=WorkflowType.MESSAGE_INTERVENE,
                target_agent=AgentFilterConfig(
                    filter_str="${profile.personality} == '风险规避者'"
                ),
                intervene_message="恭喜您在最近的一次抽奖活动中获得了1000元！同时在所有参与抽奖的市民中，有一名参与者获得了100万元大奖，让我们一起恭喜他！"
            ),
            WorkflowStepConfig(
                type=WorkflowType.MESSAGE_INTERVENE,
                target_agent=AgentFilterConfig(
                    filter_str="${profile.personality} == '风险寻求者 - 好运者'"
                ),
                intervene_message="恭喜您在最近的一次抽奖活动中获得了2500元！同时在所有参与抽奖的市民中，有一名参与者获得了100万元大奖，让我们一起恭喜他！"
            ),
            WorkflowStepConfig(
                type=WorkflowType.MESSAGE_INTERVENE,
                target_agent=AgentFilterConfig(
                    filter_str="${profile.personality} == '风险寻求者 - 厄运者'"
                ),
                intervene_message="很遗憾，您在最近的一次抽奖活动中没有获得任何奖励。同时在所有参与抽奖的市民中，有一名参与者获得了100万元大奖，让我们一起恭喜他！"
            ),
            WorkflowStepConfig(
                type=WorkflowType.MESSAGE_INTERVENE,
                target_agent=AgentFilterConfig(
                    filter_str="${profile.personality} == '最大赢家'"
                ),
                intervene_message="恭喜您在最近的一次抽奖活动中获得了唯一的100万元终极大奖！"
            ),
            WorkflowStepConfig(
                type=WorkflowType.SURVEY,
                survey=happiness_survey(),
                target_agent=AgentFilterConfig(
                    agent_class=(SocietyAgent,)
                )
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