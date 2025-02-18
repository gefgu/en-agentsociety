# Customize Your Own Simulation

## Agent Configuration

Customize your citizens and institutions for simulation.

## # of Agents
Configure the number of citizen agents using `ExpConfig.SetAgentConfig`.

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)

exp_config = (
    ExpConfig(exp_name="test")
    .SetAgentConfig(
        number_of_citizen=50,    # Specify number of citizen agents
        number_of_firm=5,        # Number of firms
        number_of_bank=2,        # Number of banks 
        number_of_government=1,  # Number of government entities
        number_of_nbs=3          # Number of neighborhood services
        enable_institution=True  # Enable/disable institutional agents
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

## Custom Agent Logics

To implement custom agent behaviors and logic, refer to the [Custom Agents Guide](02-custom-agents.md#customizing-the-agent-logic).

## City Environment Configuration

## Simulation Configuration

### Change to Other Cities

We use `Map` as the simulation environment.

To use a different city map:
1. Follow the map building guide at [MOSS Documentation](https://python-moss.readthedocs.io/en/latest/02-quick-start/index.html)
2. Configure the map in your simulation:

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)
sim_config = SimConfig(
    .SetMapRequest(file_path="path/to_your_city_map.pb")
)
```

### Simulation Time Configuration

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)
sim_config = (
    SimConfig()
    .SetSimulatorRequest(
        task_name="citysim",           # Simulation task name
        start_step=8 * 3600,           # Start time (8:00 AM)
        total_step=24 * 3600,          # Simulation Steps for One day
        max_day=2,                     # Run for 2 days
        min_step_time=1               # Minimum time (seconds) between steps
    ) 
)
```

## Global Environment Configuration

Set environment parameters with `ExpConfig.SetEnvironment`.

```python
from agentsociety.configs import (ExpConfig, SimConfig, WorkflowStep,
                                 load_config_from_file)

exp_config = (
    ExpConfig(exp_name="environment_test")
    .SetEnvironment(
        weather="The weather is normal",
        crime="The crime rate is low",
        pollution="The pollution level is low",
        temperature="The temperature is normal",
        day="Workday",
    )
)
```
