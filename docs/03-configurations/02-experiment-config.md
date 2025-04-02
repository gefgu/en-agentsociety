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
  - `target_agent`: List of agent IDs to interview
  - `interview_message`: The interview question/prompt

- `survey`: Send surveys to specific agents
  - `target_agent`: List of agent IDs to survey
  - `survey`: Survey object containing questions

- `environment`: Modify environment variables
  - `key`: Environment variable to modify
  - `value`: New value to set

- `update_state`: Update agent states directly
  - `target_agent`: List of agent IDs to update
  - `key`: State variable to modify
  - `value`: New value to set

- `message`: Send intervention messages to agents
  - `target_agent`: List of agent IDs to message
  - `intervene_message`: Message content

- `other`: Custom intervention via function
  - `func`: Function implementing the intervention

- `function`: Execute arbitrary function
  - `func`: Function to execute

### Environment Configuration

An example of the `environment` field is as follows:

```yaml
environment:
  start_tick: 28800 # Start time in seconds
  total_tick: 7200 # Total time in seconds
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
