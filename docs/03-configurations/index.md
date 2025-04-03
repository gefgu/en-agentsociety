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

### Map Configuration
The `map` field (required) defines the map configuration using the `MapConfig` class. Map specifies the simulation area.

Example:

```yaml
map:
  file_path: <MAP-FILE-PATH> # Path to the map file
  cache_path: <CACHE-FILE-PATH> # Cache path for accelerating map file loading
```

### Environment Configuration 
The `env` field (required) specifies the environment configuration through the `EnvConfig` class. Check [Environment Configuration](./02-environment-config.md) for more details.

### Agent Configuration
The `agents` field (required) manages configurations for different types of agents through the `AgentsConfig` class. Check [Agent Configuration](./03-agent-config.md) for more details.

### Experiment Configuration
The `exp` field (required) contains the experiment configuration using the `ExpConfig` class. Check [Experiment Configuration](./02-experiment-config.md) for more details.

### Advanced Configuration
The `advanced` field (optional) allows for advanced simulation settings through the `AdvancedConfig` class. This can be left empty if not needed. Check [Advanced Configuration](./04-advanced-config.md) for more details.

## Auto-scaling Feature

The configuration includes an automatic worker scaling feature:

1. Calculates optimal group sizes based on:
   - Available system memory (reserves 8GB for simulator, 1GB for message interceptor, 1GB for PostgreSQL)
   - CPU count
   - Minimum group size of 100 agents
   
2. Adjusts PostgreSQL workers (if enabled) to:
   - Scale between 1-4 workers
   - Optimize based on the number of agent groups

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
  cache_path: <CACHE-FILE-PATH> # Cache path for accelerating map file loading
env:
  avro:
    enabled: false # Whether to enable Avro
    path: <AVRO-OUTPUT-PATH> # Path to the Avro output file
  mlflow:
    enabled: false # Whether to enable MLflow
    mlflow_uri: http://localhost:59000 # MLflow server URI``
    username: <CHANGE_ME> # MLflow server username
    password: <CHANGE_ME> # MLflow server password
  pgsql:
    enabled: true # Whether to enable PostgreSQL
    dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres # PostgreSQL connection string
  redis:
    server: <REDIS-SERVER> # Redis server address
    port: 6379 # Redis port
    password: <CHANGE_ME> # Redis password
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
