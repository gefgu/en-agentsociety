# Experiment Configuration

The experiment configuration defines the overall settings and workflow for running a simulation. This configuration is managed through the `ExpConfig` class.

## Configuration Structure

The experiment configuration consists of several key components.

The structure is as follows:

```yaml
exp:
  name:
  environment:
  workflow:
  message_intercept:
  metric_extractors:
```

### Basic Information
- `name` (str, required): Name identifier for the experiment. Defaults to "default_experiment".
- `id` (UUID): Unique identifier for the experiment. Auto-generated if not specified.

### Workflow Configuration

An example of the `workflow` field is as follows:

```yaml
workflow:
  - day: 1
    type: run
```

The `workflow` field (required) defines a sequence of workflow steps that control how the simulation runs. Each step is configured through `WorkflowStepConfig` with the following types:

- `step`: Execute simulation for a specified number of steps
  - `steps`: Number of steps to run
  - `ticks_per_step`: Number of ticks per step
  
- `run`: Execute simulation for a specified number of days
  - `days`: Number of days to run
  - `ticks_per_step`: Number of ticks per step

- `interview`: Send interview questions to specific agents
  - `target_agent`: List of agent IDs to interview or a filter configuration
  - `interview_message`: The interview question/prompt

- `survey`: Send surveys to specific agents
  - `target_agent`: List of agent IDs to survey or a filter configuration
  - `survey`: Survey object containing questions

- `environment`: Modify environment variables
  - `key`: Environment variable to modify
  - `value`: New value to set

- `update_state`: Update agent states directly
  - `target_agent`: List of agent IDs to update or a filter configuration
  - `key`: State variable to modify
  - `value`: New value to set

- `message`: Send intervention messages to agents
  - `target_agent`: List of agent IDs to message or a filter configuration
  - `intervene_message`: Message content

- `other`: Custom intervention via function
  - `func`: Function implementing the intervention

- `function`: Execute arbitrary function
  - `func`: Function to execute

- `next_round`: Proceed to the next round of the simulation

- `delete_agent`: Delete the specified agents
  - `target_agent`: List of agent IDs to delete or a filter configuration

The `target_agent` field can be a list of agent IDs or a filter configuration. The filter configuration is as follows:

```yaml
target_agent:
  agent_class: <CHANGE_ME> # The class of the agent to filter
  memory_kv: <CHANGE_ME> # The key-value pairs in agent's memory to filter
```

An use example is as follows:

```python
WorkflowStepConfig(
    type=WorkflowType.DELETE_AGENT,
    target_agent=AgentFilterConfig(
      agent_class=(<AgentClass>,),  # The class of the agent to filter
      memory_kv={"key": "value"}  # The key-value pairs in agent's memory to filter
    ),
    description="Delete target agents."
),
```

### Environment Configuration

An example of the `environment` field is as follows:

```yaml
environment:
  start_tick: 28800 # Start time of simulation in seconds
```
The `environment` field (required) contains environment settings through `EnvironmentConfig` that define the simulation environment parameters.

### Message Interception

An example of the `message_intercept` field is as follows:

```yaml
message_intercept:
  mode: point # Either "point" or "edge" interception mode
  max_violation_time: 3 # Maximum allowed violations, if exceeded, the message will be intercepted
```

The `message_intercept` field (optional) configures message interception through `MessageInterceptConfig`:

- `mode`: Either "point" or "edge" interception mode
- `max_violation_time`: Maximum allowed violations
- `blocks`: List of message block rules
- `listener`: Message block listener class

### Metric Collection

An example of the `metric_extractors` field is as follows:

```yaml
metric_extractors:
  - type: function
    func: <CHANGE_ME>
    step_interval: 10
```

- Function-based metrics:
  - `type`: "function"
  - `func`: Function that computes the metric
  - `step_interval`: How often to collect the metric
  - `description`: Description of what is being measured

- State-based metrics:
  - `type`: "state" 
  - `target_agent`: Agents to collect from
  - `key`: State variable to measure
  - `method`: Aggregation method ("mean", "sum", "max", "min")
  - `step_interval`: Collection frequency
  - `description`: Description of the metric

## Experiment Configuration in `config.yaml`

An example of the `exp` field in `config.yaml` is as follows:

```yaml
exp:
  name: test # Experiment name
  environment:
    start_tick: 28800 # Start time in seconds
    total_tick: 7200 # Total time in seconds
  workflow:
  - day: 1 # The day of the workflow step
    type: run # The type of the workflow step
  message_intercept:
    mode: point # Either "point" or "edge" interception mode
    max_violation_time: 3 # Maximum allowed violations, if exceeded, the message will be intercepted
```
