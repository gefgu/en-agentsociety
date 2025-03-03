# Conduct Your First Experiment with Interventions

This guide will help you conduct a simple experiment involving interventions and data collection. We'll walk through how to introduce interventions such as weather changes, collect relevant data, and store it using MLflow.

## Step 1: Adding Interventions

Interventions can be introduced by modifying the environment or agent properties within the simulation code. In this example, we will change the weather conditions during the simulation.

### Example of Setting Weather Interventions

Here’s how you can modify the global weather condition in your Python code:

```python
import asyncio
from functools import partial
from agentsociety import AgentSimulation
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep, load_config_from_file
from agentsociety.utils import WorkflowType

async def update_weather_and_temperature(
    weather: Union[Literal["wind"], Literal["no-wind"]], simulation: AgentSimulation
):
    if weather == "wind":
        await simulation.update_environment(
            "weather",
            "Hurricane Dorian has made landfall in other cities, travel is slightly affected, and winds can be felt",
        )
    elif weather == "no-wind":
        await simulation.update_environment(
            "weather", "The weather is normal and does not affect travel"
        )
    else:
        raise ValueError(f"Invalid weather {weather}")
```

For more details on agent properties and configurations, refer to the [Agent Description Documentation](../04-custom-agents/01-concept.md).

### Add Intervention to Workflow

Add the weather intervention to your workflow configuration:

```python
exp_config = (
    ExpConfig(exp_name="hurrican", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=1000,
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=partial(update_weather_and_temperature, "wind"),
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=partial(update_weather_and_temperature, "no-wind"),
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
        ]
    )
    .SetMetricExtractors(metric_extractors=[(1, mobility_metric)])
)
```

## Step 2: Storing Data with MLflow

Collect relevant data during the simulation. This could include numerical data such as population movement patterns or resource usage.

### Example of Collecting Data

Use the following code snippet to extract metrics and send them to MLflow:

```python
from agentsociety.cityagent.metrics import mobility_metric

exp_config.SetMetricExtractors(metric_extractors=[(1, mobility_metric)])
```

For more information on data collection APIs and methods, refer to the [Metric Collection Documentation](../03-experiment-design/02-metrics-collection.md).

### Example of Storing Data in MLflow

Ensure that your MLflow setup is correctly configured in your simulation environment configuration file (`example_sim_config.yaml`):

```yaml
metric_request:
  mlflow: 
      username: <USER-NAME> # Username for MLflow authentication.
      password: <PASSWORD> # Password for MLflow authentication.
      mlflow_uri: <MLFLOW-URI> # URI pointing to the MLflow tracking server.
```


## Step 3: Running the Simulation

To run the simulation, use the following script:

```python
import ray
import asyncio
from agentsociety import AgentSimulation
from agentsociety.configs import load_config_from_file

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=False)

sim_config = load_config_from_file(
    "examples/config_templates/example_sim_config.yaml", SimConfig
)

async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 4: Analyzing Experiment Results

After completing the first experiment, analyze the results to understand the impact of the interventions and data collected.

### Example of Analyzing Results

Review the logs and visualizations provided by MLflow to interpret the outcomes of your experiment. Based on these insights, you can plan and execute larger and more complex experiments.

## Next Steps

Congratulations! You have successfully completed your first experiment. To expand your research, consider implementing custom agents with richer functionalities. Refer to the [Design Experiment](../03-experiment-design/index.md) and [Custom Agent](../04-custom-agents/index.md) for guidance on creating advanced agents and integrating them into your simulations.
