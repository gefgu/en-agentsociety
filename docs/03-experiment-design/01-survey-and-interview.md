# Survey and Interview

Our platform offers a Sociology Research Toolbox, focusing on interviews and surveys:

- **Interviews**: Researchers can pose questions to agents in real-time, receiving responses based on memory, current status, and environment without affecting their normal behavior.
- **Surveys**: Facilitates the distribution of structured questionnaires to multiple agents. Responses are collected according to preset rules, ensuring data consistency and facilitating trend analysis.

## Surveys

We provides a comprehensive survey system for gathering structured feedback from agents.

Surveys and interviews communicate with agents via MQTT (the same underlying mechanism for dialogues with agents). 
Agents receive surveys or interviews from the message queue, generate responses, and send these responses to the sending message queue, where they are captured and saved by our framework.

## Usage Example

### Create and Send A Survey

You can send a survey with codes, or with our [UI Interface](../01-quick-start.md#ui-home-page).
Below is a simple example to create and send a simple survey to specific agents.

```python
import asyncio

from agentsociety import AgentSimulation
from agentsociety.configs import SimConfig
from agentsociety.survey import SurveyManager
from agentsociety.utils import LLMRequestType


async def main():
    sim_config = (
        SimConfig()
        .SetLLMRequest(
            request_type=LLMRequestType.ZhipuAI,
            api_key="YOUR-API-KEY",
            model="GLM-4-Flash",
        )
        .SetSimulatorRequest(min_step_time=50)
        .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
        # change to your file path
        .SetMapRequest(file_path="map.pb")
        .SetAvro(path="./__avro", enabled=True)
        .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
    )
    simulation = AgentSimulation(config=sim_config)
    survey_manager = SurveyManager()
    # Create a survey
    # ------------------------------------------------------------------------#
    survey = survey_manager.create_survey(
        title="Job Satisfaction Survey",
        description="Understanding agent job satisfaction",
        pages=[
            {
                "name": "page1",
                "elements": [
                    {
                        "name": "satisfaction",
                        "title": "How satisfied are you with your job?",
                        "type": "rating",
                        "min_rating": 1,
                        "max_rating": 5,
                    }
                ],
            }
        ],
    )
    # ------------------------------------------------------------------------#
    # Send survey to specific agents
    # ------------------------------------------------------------------------#
    await simulation.send_survey(survey, agent_uuids=["agent1", "agent2"])
    # ------------------------------------------------------------------------#


if __name__ == "__main__":
    asyncio.run(main())

```

### Collect Survey Results

With `SimConfig.SetAvro` and `SimConfig.SetPostgreSql`, the survey result will be automatically stored in local Avro files and PostgreSQL database.

Check [Avro Schema](../05-advanced-usage/02-record-with-avro.md#survey) and [PostgreSQL Table](../05-advanced-usage/01-record-with-pgsql.md#survey) definitions for data structure.

## Interviews

The interview system allows direct interaction with agents through messages.

### Conducting An Interview

```python
import asyncio

from agentsociety import AgentSimulation
from agentsociety.configs import SimConfig
from agentsociety.utils import LLMRequestType


async def main():
    sim_config = (
        SimConfig()
        .SetLLMRequest(
            request_type=LLMRequestType.ZhipuAI,
            api_key="YOUR-API-KEY",
            model="GLM-4-Flash",
        )
        .SetSimulatorRequest(min_step_time=50)
        .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
        # change to your file path
        .SetMapRequest(file_path="map.pb")
        .SetAvro(path="./__avro", enabled=True)
        .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
    )
    simulation = AgentSimulation(config=sim_config)
    # Send interview to specific agents
    # ------------------------------------------------------------------------#
    await simulation.send_interview_message(
        content="What are your career goals?", agent_uuids=["agent1"]
    )
    # ------------------------------------------------------------------------#


if __name__ == "__main__":
    asyncio.run(main())

```

### Collect Interview Results

With `SimConfig.SetAvro` and `SimConfig.SetPostgreSql`, the interview result will be automatically stored in local Avro files and PostgreSQL database.

Check [Avro Schema](../05-advanced-usage/02-record-with-avro.md#interview) and [PostgreSQL Table](../05-advanced-usage/01-record-with-pgsql.md#interview) definitions for data structure.
