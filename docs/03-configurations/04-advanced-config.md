# Advanced Configurations

In this section, we will introduce some advanced configurations that control the simulation more flexibly.

## Agent Group Modification

You can modify the number of agent in each group for simulation. In our framework, we have a default configuration (auto-set based on the number of available cores) for the number of agent in each group.

```python
config = Config(
    ...
    advanced=AdvancedConfig(
        group_size=10,
    )
)
```

## Logging Level

You can modify the logging level for the simulation.

```python
config = Config(
    ...
    advanced=AdvancedConfig(
        logging_level=logging.INFO,
    )
)
```

## Urban Space (Simulator) Control

You can modify the urban space (simulator) for the simulation.

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
- `log_dir`: The directory to save the log file of the simulator, not the framework.
- `max_process`: The maximum number of processes to run in parallel, only controls the simulator (urban space).
- `logging_level`: The logging level for the simulator.
