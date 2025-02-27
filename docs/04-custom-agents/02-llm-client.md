# LLM Client

The LLM Client manages communications between agents and large language models, representing the agent's "soul". 

## Usage Example

```python
from agentsociety import Agent, AgentType
from agentsociety.llm import LLM


class CustomAgent(Agent):
    def __init__(self, name: str, llm_client: LLM, **kwargs):
        super().__init__(
            name=name, llm_client=llm_client, type=AgentType.Citizen, **kwargs
        )

    async def forward(
        self,
    ):
        llm_client = self.llm
        await llm_client.atext_request(dialog={"content": "Hello!"})

```

## Core APIs

- `atext_request`: Asynchronously sends requests to the LLM service with full parameter control and automatic retries with exponential backoff.
- `get_consumption, show_consumption`: Methods to track and report token usage statistics across API keys, with optional cost estimation.
