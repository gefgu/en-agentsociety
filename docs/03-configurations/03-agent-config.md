# Agent Configuration

The agent configuration defines the settings for different types of agents in the simulation. This configuration is managed through the `AgentConfig` class, which handles various components essential for agent initialization and behavior.

## Configuration Structure

The agent configuration consists of several key components:

### Agent Class Type
The `agent_class` field specifies the type of agent to create. It can be either:
- A custom Agent class that inherits from the base `Agent` class
  - One of the predefined `AgentClassType` enum values:
    - `citizen`: For citizen agents
    - `firm`: For company/firm agents  
    - `government`: For government agents
    - `bank`: For bank agents
    - `nbs`: For national bureau of statistics agents
- A `AgentClassType` enum value, e.g. `citizen`. This will create a citizen agent we have predefined in the framework.


### Agent Count
The `number` field (required) specifies how many agents of this type to create. Must be greater than 0.

### Agent Parameters
The `agent_params` field (optional) allows passing configuration parameters to the agent class as a dictionary to modify the working behavior of target agents. A use case is as follows:

```yaml
agent_class: citizen
number: 100
agent_params:
  enable_cognition: true
  UBI: 1000
  num_labor_hours: 168
  productivity_per_labor: 1
  time_diff: 30 * 24 * 60 * 60
  max_plan_steps: 6
```

Each agent class has its own parameter configurations. You can find the parameter configurations through `AgentClassType.ParamsType`, in which the parameters are defined with default values and descriptions.

### Blocks Configuration
The `blocks` field (optional) allows passing additional blocks to the agent as you need to endow the agent with more capabilities. A use case is as follows:

```yaml
blocks:
  mobilityblock:
    search_limit: 50
  otherblock:
    block_parameter_01: value_01
    block_parameter_02: value_02
```

You can find usable blocks in the [agentsociety-community](https://github.com/tsinghua-fib-lab/agentsociety-community) with its description and usablitity. Note that each kinds of blocks have their own parameters, please refer to the documentation of the specific block you want to use.

### Memory Configuration
The memory configuration can be specified in one of three mutually exclusive ways:

1. **Function-based Configuration**
   - `memory_config_func` (optional): A callable function that generates memory configurations

2. **File-based Configuration** 
   - `memory_from_file` (optional): Path to a file containing memory configurations

3. **Distribution-based Configuration**
   - `memory_distributions` (optional): A dictionary mapping memory attributes to either:
     - Distribution objects
     - DistributionConfig objects defining statistical distributions
