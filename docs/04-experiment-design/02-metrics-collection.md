# Metrics Collection

The metrics management system, encapsulated within the `MlflowClient` class is designed to streamline the process of connecting to, logging data with, and managing experiments in [MLflow](https://mlflow.org/).

```{admonition} Caution
:class: caution
To integrate with `MLflow`, you have to deploy it first.
Check [prerequisites](./01-quick-start/01-prerequisites.md) for details.
```

## Metric Extractor

We provide a flexible way to collect metrics during experiments, just need to specify your metric extractor in the experiment config.
There are two main types of metric extractors:

1. **Function-based metrics**: Custom functions that extract metrics from the simulation
2. **State-based metrics**: Metrics collected directly from agent states, `target_agent` is required.

Check `agentsociety.cityagent.metrics` for pre-defined metrics.

You can also define your own metric extractor, an example is as follows.

```python
from agentsociety.cityagent import SocietyAgent
from agentsociety.simulation import AgentSociety

async def gather_ids(simulation: AgentSociety):
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    ids = await simulation.gather("id", citizen_ids)
    return ids

config = Config(
    ...
    exp=ExpConfig(
        ...
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=gather_ids, step_interval=12
            ),
        ],
    ),
)

```
