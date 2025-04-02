# Survey and Interview

Our platform offers a Sociology Research Toolbox, focusing on interviews and surveys:

- **Surveys**: Facilitates the distribution of structured questionnaires to multiple agents. Responses are collected according to preset rules, ensuring data consistency and facilitating trend analysis.
- **Interviews**: Researchers can pose questions to agents in real-time, receiving responses based on memory, current status, and environment without affecting their normal behavior.

## Surveys

We provide a comprehensive survey system for gathering structured feedback from agents using the `SurveyManager` class.

Surveys and interviews communicate with agents via Redis (the same underlying mechanism for dialogues with agents). 
Agents receive surveys or interviews from the message queue, generate responses, and send these responses to the sending message queue, where they are captured and saved by our framework.

### Create and Send A Survey

You can send a survey with code, or with our [WebUI](../_static/01-exp-status.jpg)


### Survey Components

A survey consists of the following components:

- **Survey**: The top-level container with:
  - Unique ID (UUID)
  - Title
  - Description 
  - List of pages
  - Response collection
  - Creation timestamp

- **Pages**: Each survey contains one or more pages with:
  - Name
  - List of questions (elements)

- **Questions**: Each page contains questions with:
  - Name
  - Title
  - Question type (one of):
    - Text
    - Radio group
    - Checkbox
    - Boolean
    - Rating
    - Matrix
  - Additional type-specific properties like:
    - Choices for radio/checkbox
    - Columns/rows for matrix
    - Min/max values for rating
  - Required flag

### Usage Example

Below is an example of how to create and send a survey.
In this example, we create a survey with a single page and a single question, and we send it to agents with ID 5, 10, 15, and 20.

```python
import asyncio
import logging
from typing import Literal, Union
from uuid import uuid4
import datetime
import ray

from agentsociety.cityagent import default
from agentsociety.cityagent.metrics import mobility_metric
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.survey import Survey
from agentsociety.survey.models import Page, Question, QuestionType
from agentsociety.configs.agent import AgentClassType, AgentConfig
from agentsociety.configs.exp import (
    MetricExtractorConfig,
    MetricType,
    WorkflowStepConfig,
    WorkflowType,
)
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.message import RedisConfig
from agentsociety.metrics import MlflowConfig
from agentsociety.simulation import AgentSociety
from agentsociety.storage import AvroConfig, PostgreSQLConfig

ray.init(logging_level=logging.INFO)

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
            )
        ]
    ),  # type: ignore
    exp=ExpConfig(
        name="survey_test",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=3,
            ),
            WorkflowStepConfig(
                type=WorkflowType.SURVEY,
                target_agent=[5, 10, 15, 20],
                survey=Survey(
                    id=uuid4(),
                    description="survey_1",
                    created_at=datetime.datetime.now(),
                    title="Survey Title",
                    pages=[
                        Page(
                            name="page_0",
                            elements=[
                                Question(
                                    name="question_0",
                                    title="How much do you like the weather?",
                                    type=QuestionType.RATING,
                                    min_rating=1,
                                    max_rating=5,
                                    required=True,
                                )
                            ],
                        )
                    ],
                ),
            ),
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.FUNCTION,
                func=mobility_metric,
                step_interval=1,
            )
        ],
    ),
)
config = default(config)

async def main():
    agentsociety = AgentSociety(config)
    await agentsociety.init()
    await agentsociety.run()
    await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

```
  
## Interviews

Interviews are similar to surveys, but they are used to gather unstructured feedback from agents.

### Send an Interview

In our framework, an interview is a message sent to an agent, the message here is modeled as a `string` object.
Similar to surveys, you can send an interview with code, or with our [UI Interface](../_static/01-exp-status.jpg)


### Usage Example

Below is an example of how to send an interview to an agent.
In this example, we send an interview to agent with ID 5.

```python
import asyncio
import logging
from typing import Literal, Union
from uuid import uuid4
import datetime
import ray

from agentsociety.cityagent import default
from agentsociety.cityagent.metrics import mobility_metric
from agentsociety.configs import (
    AgentsConfig,
    Config,
    EnvConfig,
    ExpConfig,
    LLMConfig,
    MapConfig,
)
from agentsociety.survey import Survey
from agentsociety.survey.models import Page, Question, QuestionType
from agentsociety.configs.agent import AgentClassType, AgentConfig
from agentsociety.configs.exp import (
    MetricExtractorConfig,
    MetricType,
    WorkflowStepConfig,
    WorkflowType,
)
from agentsociety.environment import EnvironmentConfig
from agentsociety.llm import LLMProviderType
from agentsociety.message import RedisConfig
from agentsociety.metrics import MlflowConfig
from agentsociety.simulation import AgentSociety
from agentsociety.storage import AvroConfig, PostgreSQLConfig

ray.init(logging_level=logging.INFO)

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
            )
        ]
    ),  # type: ignore
    exp=ExpConfig(
        name="interview_test",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=3,
            ),
            WorkflowStepConfig(
                type=WorkflowType.INTERVIEW,
                target_agent=[5, 10, 15, 20],
                interview_message="What is your favorite color?",
            ),
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.FUNCTION,
                func=mobility_metric,
                step_interval=1,
            )
        ],
    ),
)
config = default(config)

async def main():
    agentsociety = AgentSociety(config)
    await agentsociety.init()
    await agentsociety.run()
    await agentsociety.close()
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```
