# Customize Your Own Simulation

## Agent Number and Profile Configuration

Check the [Agent Configuration](../03-configurations/03-agent-config.md) for more details.

## Custom Agent Logics

To implement custom agent behaviors and logic, refer to the [Custom Agents Guide](../05-custom-agents/04-agent-customization.md).

## City Environment Configuration

## Simulation Configuration

### Change to Other Cities

We use `Map` as the simulation environment.

To use a different city map:
1. Follow the map building guide at [MOSS Documentation](https://python-moss.readthedocs.io/en/latest/02-quick-start/index.html)
2. Configure the map in your simulation:

```python
config = Config(
    ...
    map=MapConfig(
        file_path="path/to_your_city_map.pb"
    )
)
```

## Global Environment Configuration

Set environment parameters with `EnvironmentConfig`.

```python
config = Config(
    ...
    exp=ExpConfig(
        environment=EnvironmentConfig(
            weather="The weather is normal",
        )
    )
)
```

## Utilize Advanced Configuration

### Distributed Simulation

To run simulation in a distributed manner, refer to the [Distributed Simulation Guide](03-distributed-simulation.md).

### Agent Group Modification

You can modify the number of agent in each group for simulation.

```python
config = Config(
    ...
    advanced=AdvancedConfig(
        group_size=10,
    )
)
```
```{admonition} Note
:class: note
The default configuration is auto-set based on the number of available cores.
```

### Logging Level

You can modify the logging level for the simulation.

```python
config = Config(
    ...
    advanced=AdvancedConfig(
        logging_level="INFO"
    )
)
```

### Simulator Configuration

You can modify the simulator configuration.

```python
config = Config(
    ...
    advanced=AdvancedConfig(
        simulator=SimulatorConfig(
            primary_node_ip="127.0.0.1",
            log_dir="./log",
            max_process=1,
            logging_level="INFO",
        ), 
    )
)
```

Each configuration item is optional, and the default value will be used if not specified.
The meaning of each configuration item is as follows:
- `primary_node_ip`: The IP address of the primary node. Only used in distributed simulation.
- `log_dir`: The directory to save the log file of the simulator, not our framework.
- `max_process`: The maximum number of processes to run in parallel, only controls the simulator (urban space).
- `logging_level`: The logging level for the simulator.
