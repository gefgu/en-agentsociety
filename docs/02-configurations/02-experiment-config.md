# Experiment Config

`ExpConfig` serves as a central configuration point for setting up experiments within our simulation framework. 
It includes configurations for agents, workflows, environment settings, message interception, metric extractors, logging levels, experiment names, and semaphore limits for language model requests.

## Agent Control

Represents the configuration for different types of agents participating in the simulation. It allows specifying numbers, sizes, models, additional classes, configurations, and functions related to memory and initialization.

- Predefined Agent number control
    ```python
    number_of_citizen: int = Field(1, description="Number of citizens")
    number_of_firm: int = Field(1, description="Number of firms")
    number_of_government: int = Field(1, description="Number of governments")
    number_of_bank: int = Field(1, description="Number of banks")
    number_of_nbs: int = Field(1, description="Number of neighborhood-based services")
    ```
- Distributed Configuration
    The `group_size` controls the number of agents each Ray actor node is responsible for computing. 
    Please adjust this value flexibly according to the actual machine conditions to achieve the best simulation performance.
    ```python
    group_size: int = Field(100, description="Size of agent groups")    
    ```
- Self-Define Agent Classes
    The `extra_agent_class` defines your customized agents and the numbers to be generated in the simulation.
- Serialized (in `dict` form) Agent logic
    The `extra_agent_class` serves as the input control for the serialized logic.
    Check [Block Workflow](../04-custom-agents/06-agent-customization.md#workflow-of-block-the-forward-method) for detailed `extra_agent_class` example.
- Memory field Control
    The `memory_config_func` controls what fields the Agent memory have for each type of Agent. 
- Memory Initial State Control
    The `memory_config_init_func` controls the memory state (the value to each memory field) for each type of agent.
- Agent initialization Function
    `init_func`, Default to bounding to the Urban Space and Economy Simulator.

## Workflow Control

Defines individual steps within a workflow, including the type, function to execute, duration in days, repetition times, and a description.

- Type Selection (`type`)
    - `STEP`: forward the simulation time in steps.
    - `RUN`: forward the simulation time in days.
    - `INTERVIEW`: interview the agents in the simulation. 
    - `SURVEY`: send surveys to the agents. 
    - `INTERVENE`: pass in functions to intervene the simulation environment. For example, change the weather.
    - `FUNCTION`: pass in functions to do something. For example, simply collect some data from the environment without changing anything.

- Execution Function
    ```python
    func: Optional[Callable] = None  # Function to execute during this workflow step
    ```
    Custom function to be called at this step in the workflow. For `CUSTOM` workflow types, this field is required.

- Duration Control
    ```python
    days: int = 1  # How many simulation days this step runs
    times: int = 1  # How many times to repeat this step
    ```
    These parameters control the temporal scope of the workflow step, allowing for precise control over simulation timing.

## Global Environment Control

Allows setting the environmental conditions under which the simulation will run. This includes weather, crime rate, pollution, temperature, and day type.

- Weather Conditions
    ```python
    weather: str = Field(default="The weather is normal")
    ```
    Describes current atmospheric conditions which may affect agent mobility, activity choices, and interactions.

- Social Factors
    ```python
    crime: str = Field(default="The crime rate is low")
    ```
    Represents the safety level in the simulation environment, potentially affecting agent routing and business decisions.

- Environmental Quality
    ```python
    pollution: str = Field(default="The pollution level is low")
    temperature: str = Field(default="The temperature is normal")
    ```
    Environmental parameters that may influence agent comfort, health status, and behavioral patterns.

- Temporal Context
    ```python
    day: str = Field(default="Workday")
    ```
    Defines the type of day (workday, weekend, holiday) which may affect agent schedules and available activities.

## Message Interception

Provides configurations for intercepting messages within the simulation. It supports defining the mode ('point' or 'edge'), maximum violation times, interceptor blocks, and listeners.

- Interception Mode
    We provide two types of predefined interception mode. Check [Message Interception](../03-experiment-design/03-message-interception.md#message-interception) for details.
    ```python
    mode: Optional[Union[Literal["point"], Literal["edge"]]] = None
    ```
    Defines the interception strategy:
    - `point`: Intercept at specific agent nodes
    - `edge`: Intercept along communication paths between agents

- Violation Handling
    Valid only when using predefined interception mode.
    ```python
    max_violation_time: int = 3
    ```
    Specifies how many rule violations are permitted before taking corrective action.

- Self-Define Interception Logic
    ```python
    message_interceptor_blocks: Optional[list[Any]] = None
    ```
    Custom logic blocks that implement interception rules and actions.

- Event Monitoring
    ```python
    message_listener: Optional[Any] = None
    ```
    Observer component that receives notifications about message events without modifying them, useful for logging and analysis.

## Configuration Methods

Chainable builder pattern for fluent configuration:

```python

exp_config = (
    ExpConfig()
    .SetAgentConfig(number_of_citizen=10)
    .SetEnvironment(weather="Sunny", crime="Low")
    .SetMessageIntercept(mode="point", max_violation_time=5)
    .SetMetricExtractors([(1, lambda x: print(x))])
)
```
