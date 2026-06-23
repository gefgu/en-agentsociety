# {py:mod}`en_agentsociety.simulation.type`

```{py:module} en_agentsociety.simulation.type
```

```{autodoc2-docstring} en_agentsociety.simulation.type
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ExperimentStatus <en_agentsociety.simulation.type.ExperimentStatus>`
  - ```{autodoc2-docstring} en_agentsociety.simulation.type.ExperimentStatus
    :summary:
    ```
* - {py:obj}`Logs <en_agentsociety.simulation.type.Logs>`
  - ```{autodoc2-docstring} en_agentsociety.simulation.type.Logs
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.simulation.type.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.simulation.type.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.simulation.type.__all__
:value: >
   ['ExperimentStatus', 'Logs']

```{autodoc2-docstring} en_agentsociety.simulation.type.__all__
```

````

`````{py:class} ExperimentStatus()
:canonical: en_agentsociety.simulation.type.ExperimentStatus

Bases: {py:obj}`enum.IntEnum`

```{autodoc2-docstring} en_agentsociety.simulation.type.ExperimentStatus
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.simulation.type.ExperimentStatus.__init__
```

````{py:attribute} NOT_STARTED
:canonical: en_agentsociety.simulation.type.ExperimentStatus.NOT_STARTED
:value: >
   0

```{autodoc2-docstring} en_agentsociety.simulation.type.ExperimentStatus.NOT_STARTED
```

````

````{py:attribute} RUNNING
:canonical: en_agentsociety.simulation.type.ExperimentStatus.RUNNING
:value: >
   1

```{autodoc2-docstring} en_agentsociety.simulation.type.ExperimentStatus.RUNNING
```

````

````{py:attribute} FINISHED
:canonical: en_agentsociety.simulation.type.ExperimentStatus.FINISHED
:value: >
   2

```{autodoc2-docstring} en_agentsociety.simulation.type.ExperimentStatus.FINISHED
```

````

````{py:attribute} ERROR
:canonical: en_agentsociety.simulation.type.ExperimentStatus.ERROR
:value: >
   3

```{autodoc2-docstring} en_agentsociety.simulation.type.ExperimentStatus.ERROR
```

````

`````

`````{py:class} Logs
:canonical: en_agentsociety.simulation.type.Logs

```{autodoc2-docstring} en_agentsociety.simulation.type.Logs
```

````{py:attribute} llm_log
:canonical: en_agentsociety.simulation.type.Logs.llm_log
:type: list[typing.Any]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.simulation.type.Logs.llm_log
```

````

````{py:attribute} simulator_log
:canonical: en_agentsociety.simulation.type.Logs.simulator_log
:type: list[typing.Any]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.simulation.type.Logs.simulator_log
```

````

````{py:attribute} agent_time_log
:canonical: en_agentsociety.simulation.type.Logs.agent_time_log
:type: list[typing.Any]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.simulation.type.Logs.agent_time_log
```

````

````{py:method} append(other: en_agentsociety.simulation.type.Logs)
:canonical: en_agentsociety.simulation.type.Logs.append

```{autodoc2-docstring} en_agentsociety.simulation.type.Logs.append
```

````

`````
