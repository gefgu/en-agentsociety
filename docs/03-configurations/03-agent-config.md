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

### Parameter Configuration
The `param_config` field (optional) allows passing additional configuration parameters to the agent class as a dictionary.

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
