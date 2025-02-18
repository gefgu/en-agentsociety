# Quick Start

This guide helps you quickly set up a social simulation scenario with our framework.

---

## Prerequisites

## Run Example Simulation

We give a simple example to run a social simulation with 50 citizens in Beijing City using predefined agent templates and provided Beijing City data.

To use this framework, you **need access to LLM APIs**. We support multiple providers:

- [DeepSeek](https://deepseek.com/)
- [OpenAI](https://openai.com/)
- [Qwen](https://tongyi.aliyun.com/)
- [SiliconFlow](https://siliconflow.cn/)
- [ZhipuAI](https://chatglm.cn/)

ZhipuAI API Acquisition (As Example)
1. Visit https://open.bigmodel.cn/
2. Register an account and authorize yourself at https://open.bigmodel.cn/usercenter/settings/auth/
3. Create an API key of `GLM-4-Flash` (free model) at https://open.bigmodel.cn/usercenter/apikeys/

### Configuration

We'll introduce the configuration of our framework in this section.

#### 1. File-based Configuration

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)
from agentsociety.simulation import AgentSimulation

sim_config = load_config_from_file("examples/config_templates/example_sim_config.yaml", SimConfig)
exp_config = load_config_from_file("examples/config_templates/example_exp_config.yaml", ExpConfig)
```
##### `example_sim_config.yaml`
```yaml
llm_request:
    request_type: zhipuai
    api_key: ""
    model: GLM-4-Flash

simulator_request:
    task_name: "citysim"              
    max_day: 1000                     
    start_step: 28800                 
    total_step: 31536000              
    log_dir: "./log"                  
    min_step_time: 1000               
    primary_node_ip: "localhost"      

mqtt:
    server: "mqtt.example.com"
    port: 1883 
    username: "username"
    password: "password"

map_request:
    file_path: "./ignore/map.pb"

metric_request:
    mlflow: 
        username: "username"
        password: "password"
        mlflow_uri: "localhost:59000"

pgsql:
    enabled: false     
    dsn: "postgresql://user:pass@localhost/db"         

avro:
    enabled: false
    path: "./cache"          

```
##### `example_exp_config.yaml`
```yaml
agent_config:
    number_of_citizen: 50  # Number of citizens
    enable_institution: false  # Whether institutions are enabled in the experiment

workflow: [
    {"type": "run", "days": 1}
]

environment:
    weather: "The weather is normal"
    crime: "The crime rate is low"
    pollution: "The pollution level is low"
    temperature: "The temperature is normal"
    day: "Workday"

message_intercept:
    mode: "point"  # Mode can be 'point' or 'edge'
    max_violation_time: 3  # Maximum violation time


exp_name: "my_experiment"  # Experiment name

llm_semaphore: 200  # Semaphore value for LLM operations

```

#### 2. Fluent API Configuration

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)
from agentsociety.simulation import AgentSimulation

sim_config = (
    SimConfig()
    .SetLLMRequest(request_type="zhipuai", api_key="", model="GLM-4-Flash")
    .SetSimulatorRequest(min_step_time=1)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    .SetMapRequest(file_path="./ignore/map.pb")
    .SetMetricRequest(
        username="mlflow_user", password="mlflow_pass", mlflow_uri="http://mlflow:5000"
    )
    .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="test", llm_semaphore=201)
    .SetAgentConfig(
        number_of_citizen=50,
        number_of_firm=0,
        number_of_government=0,
        number_of_bank=0,
        number_of_nbs=0,
        enable_institution=False,
    )
    .SetWorkFlow([WorkflowStep(type="run", days=1)])
    .SetEnvironment(
        weather="The weather is normal",
        crime="The crime rate is low",
        pollution="The pollution level is low",
        temperature="The temperature is normal",
        day="Workday",
    )
    .SetMessageIntercept(mode="point", max_violation_time=3)
)
```

### Minimum Example Codes

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)
from agentsociety.simulation import AgentSimulation

sim_config = (
    SimConfig()
    .SetLLMRequest(request_type="zhipuai", api_key="", model="GLM-4-Flash")
    .SetSimulatorRequest(min_step_time=1)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    .SetMapRequest(file_path="./ignore/map.pb")
    .SetMetricRequest(
        username="mlflow_user", password="mlflow_pass", mlflow_uri="http://mlflow:5000"
    )
    .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="test", llm_semaphore=201)
    .SetAgentConfig(
        number_of_citizen=50,
        number_of_firm=0,
        number_of_government=0,
        number_of_bank=0,
        number_of_nbs=0,
        enable_institution=False,
    )
    .SetWorkFlow([WorkflowStep(type="run", days=1)])
    .SetEnvironment(
        weather="The weather is normal",
        crime="The crime rate is low",
        pollution="The pollution level is low",
        temperature="The temperature is normal",
        day="Workday",
    )
    .SetMessageIntercept(mode="point", max_violation_time=3)
)


async def main():
    simulation = AgentSimulation.run_from_config(
        config=exp_config,
        sim_config=sim_config,
    )
    await simulation


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

This code creates 50 citizen agents within the framework and conducts a one-day simulation, where the agent interaction processes are inherently built in our framework.

## Simulation Observation

We'll give a brief introduction to the simulation observation methods.

To design your own experiment with interaction and intervene methods provided, please refer to [Experiment Design Guide](03-experiment-design/index.md).

### Visualization with Web Interface

We provide `agentsociety-ui` as our visualization tool within the python package.

You can either visualize a running simulation process in real-time or replay one completed simulation.

To activate the ui interface, you simply need to code these in your terminal. 
```bash
agentsociety-ui --pg-dsn=postgres://postgres:postgres@localhost:5432/socialcity?sslmode=disable --mqtt-broker=tcp://localhost:1883 --mqtt-username=username --mqtt-password=password --addr=localhost:8080 --mlflow-url=http://localhost:5000
```

- `--addr`: Address for the UI service (default: `localhost:8080`).
- `--mqtt-broker`: MQTT broker address (e.g., `"mqtt.example.com:1883`).
- `--mqtt-username`: Username for MQTT.
- `--mqtt-password`: Password for MQTT.
- `--pg-dsn`: PostgreSQL DSN for database connection.
- `--mlflow-url`: URL for MLflow server (e.g., `http://localhost:59000`).

```{admonition} Caution
:class: caution
To use this interface, you MUST deploy PostgreSQL, MLflow and MQTT first.
```
#### UI Home Page

The home page shown in the listening address lists all the simulation recorded in your deployed PostgreSQL DSN. 

![home-page](img/01-ui-home-page.jpg) 

There are several function buttons on the top left.

- `Experiment`: Display all conducted experiments. Click to jump to the detailed interaction page.
- `Survey`: Create and manage surveys to Agents within the simulation.
- `MLflow`: Direct you to the deployed MLflow web page.

#### Experiment Interaction

Click `Goto` shown in [UI Home Page](#ui-home-page) to interact with specific experiment.

In the experiment page, you can see the geographic position of each Agent.

- Mobility Trajectories.
- Chat messages among Agents.
- Economy activities.

![exp-page](img/01-exp-page.jpg)

Click one Agent avatar for detailed information.

- Interview specific Agents.
- Send surveys to Agents and collect their answers.
- Chat with Agents.

![exp-status](img/01-exp-status.jpg)


### Storage Experiment locally

Please check [Record Experiment with Avro](05-advanced-usage/02-record-with-avro.md) for details.

### Extract Specific Metrics

TODO
Please check [Metrics Collection](03-experiment-design) for details.

## Use Case

To see implemented examples of social experiments with our platform, please check [Use Case](04-use-case/index.md).

## Next Steps

For advanced usage of our framework, explore the following topics:

### Data Export and Analysis

- **Avro Data Export**
- **PostgreSQL Integration** 

### Customize Simulation Environment

Control the simulation environment, including simulation position, weather condition, etc.

### Distributed Simulation

Setup Ray for distributed simulation

### Advanced Usage Guidance

For detailed implementation of these features, refer to:
- [Record Experiment with PostgreSQL](05-advanced-usage/01-record-with-pgsql.md)
- [Record Experiment with Avro](05-advanced-usage/02-record-with-avro.md)
- [Customize Simulation Environment](05-advanced-usage/04-customize-your-simulation.md)
- [Distributed Simulation Setup](05-advanced-usage/03-distributed-simulation.md)
