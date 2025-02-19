# Experiment Config

```{admonition} Caution
:class: caution
This document is currently under active development. The complete version will be available soon. Stay tuned!
```

`ExpConfig` serves as a central configuration point for setting up experiments within our simulation framework. 
It includes configurations for agents, workflows, environment settings, message interception, metric extractors, logging levels, experiment names, and semaphore limits for language model requests.

## Key Components

1. AgentConfig

Represents the configuration for different types of agents participating in the simulation. It allows specifying numbers, sizes, models, additional classes, configurations, and functions related to memory and initialization.

2. EnvironmentConfig

Allows setting the environmental conditions under which the simulation will run. This includes weather, crime rate, pollution, temperature, and day type.

3. MessageInterceptConfig

Provides configurations for intercepting messages within the simulation. It supports defining the mode ('point' or 'edge'), maximum violation times, interceptor blocks, and listeners.

4. WorkflowStep

Defines individual steps within a workflow, including the type, function to execute, duration in days, repetition times, and a description.

## Configuration Methods

Chainable builder pattern for fluent configuration:

```python
from your_project.exp_config import ExpConfig, WorkflowStep, WorkflowType

# Create a new experiment configuration
exp_config = (
    ExpConfig()
    .SetAgentConfig(number_of_citizen=10, enable_institution=True)
    .SetEnvironment(weather="Sunny", crime="Low")
    .SetMessageIntercept(mode="point", max_violation_time=5)
    .SetMetricExtractors([(1, lambda x: print(x))])
)

print(exp_config.prop_agent_config.number_of_citizen)  # Outputs: 10
```
