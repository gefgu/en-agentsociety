import asyncio

from message_agent import AgreeAgent, DisagreeAgent

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
                memory_from_file="./profiles/profiles.json",
            ),
            AgentConfig(
                agent_class=AgreeAgent,
                number=1,
                memory_from_file="./profiles/echo_chamber_profile_agree_agent.json",
            ),
            AgentConfig(
                agent_class=DisagreeAgent,
                number=1,
                memory_from_file="./profiles/echo_chamber_profile_disagree_agent.json",
            ),
        ],
    ),  # type: ignore
    exp=ExpConfig(
        name="polarization_echo_chamber",
        workflow=[
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
    agentsociety = AgentSociety.create(config)
    try:
        await en_agentsociety.init()
        await en_agentsociety.run()
    finally:
        await en_agentsociety.close()


if __name__ == "__main__":
    asyncio.run(main())
