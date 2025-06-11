# Configurations

This guide helps you to learn about the configuration for our simulation framework.

The overall configuration for the simulation is managed through the `Config` class. We use the same configuration for both the simulation and the web UI.

## Configuration Structure

The overall configuration consists of several key components:

### LLM Configuration

The `llm` field (required) contains a list of LLM configurations. At least one LLM configuration must be provided.

Example:

```yaml
llm:
- api_key: <API-KEY> # LLM API key
  base_url: <BASE-URL> # LLM base URL, used for VLLM
  model: <YOUR-MODEL> # LLM model
  provider: <PROVIDER> # LLM provider
  semaphore: 200 # Semaphore for LLM requests, control the max number of concurrent requests
```

```{admonition} Note
:class: note
If your LLM does not support high-performance inference, you can set the `semaphore` to a smaller value.
```

The `LLMConfig` class contains the following fields:

- `api_key` (str, required): The API key for the LLM
- `base_url` (str, optional): The base URL for the LLM, used for VLLM
- `model` (str, required): The model name for the LLM
- `provider` (str,  required): The provider for the LLM. Currently, we support `openai`, `deepseek`, `qwen`, `zhipuai`, `siliconflow` and `vllm`.
- `semaphore` (int, optional): The semaphore for the LLM requests, control the max number of concurrent requests

### Map Configuration
The `map` field (required) defines the map configuration using the `MapConfig` class. Map specifies the simulation area.

Example:

```yaml
map:
  file_path: <MAP-FILE-PATH> # Path to the map file
```

The `MapConfig` class contains the following fields:

- `file_path` (str, required): The path to the map file

### Other Configurations

There are some other configuration fields, which we will introduce in the following sections.

- **Environment Configuration**:
The `env` field (required) specifies the environment configuration through the `EnvConfig` class. Check [Environment Configuration](./02-environment-config.md) for more details.

- **Agent Configuration**:
The `agents` field (required) manages configurations for different types of agents through the `AgentsConfig` class. Check [Agent Configuration](./03-agent-config.md) for more details.

- **Experiment Configuration**:
The `exp` field (required) contains the experiment configuration using the `ExpConfig` class. Check [Experiment Configuration](./02-experiment-config.md) for more details.

- **Advanced Configuration**:
The `advanced` field (optional) allows for advanced simulation settings through the `AdvancedConfig` class. This can be left empty if not needed. Check [Advanced Configuration](./04-advanced-config.md) for more details.

## Example Configuration

Here's an example of the overall configuration:

```yaml

llm:
- api_key: <API-KEY> # LLM API key
  base_url: <BASE-URL> # LLM base URL, used for VLLM
  model: <YOUR-MODEL> # LLM model
  provider: <PROVIDER> # LLM provider
  semaphore: 200 # Semaphore for LLM requests, control the max number of concurrent requests
map:
  file_path: <MAP-FILE-PATH> # Path to the map file
env:
  db:
    enabled: true # Whether to enable database
    db_type: sqlite | postgresql
    pg_dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres # PostgreSQL connection string
agents:
  citizens:
  - agent_class: citizen # The class of the agent
    number: 100 # The number of the agents
exp:
  name: test # Experiment name
  environment:
    start_tick: 28800 # Start time in seconds
    total_tick: 7200 # Total time in seconds
  workflow:
  - day: 1 # The day of the workflow step
    type: run # The type of the workflow step
```


```{toctree}
:maxdepth: 2

01-environment-config
02-experiment-config
03-agent-config
04-advanced-config
```
