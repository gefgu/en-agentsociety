# {py:mod}`agentsociety.simulation.agentsociety`

```{py:module} agentsociety.simulation.agentsociety
```

```{autodoc2-docstring} agentsociety.simulation.agentsociety
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AgentSociety <agentsociety.simulation.agentsociety.AgentSociety>`
  - ```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_init_agent_class <agentsociety.simulation.agentsociety._init_agent_class>`
  - ```{autodoc2-docstring} agentsociety.simulation.agentsociety._init_agent_class
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.simulation.agentsociety.__all__>`
  - ```{autodoc2-docstring} agentsociety.simulation.agentsociety.__all__
    :summary:
    ```
* - {py:obj}`MIN_ID <agentsociety.simulation.agentsociety.MIN_ID>`
  - ```{autodoc2-docstring} agentsociety.simulation.agentsociety.MIN_ID
    :summary:
    ```
* - {py:obj}`MAX_ID <agentsociety.simulation.agentsociety.MAX_ID>`
  - ```{autodoc2-docstring} agentsociety.simulation.agentsociety.MAX_ID
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.simulation.agentsociety.__all__
:value: >
   ['AgentSociety']

```{autodoc2-docstring} agentsociety.simulation.agentsociety.__all__
```

````

````{py:data} MIN_ID
:canonical: agentsociety.simulation.agentsociety.MIN_ID
:value: >
   1

```{autodoc2-docstring} agentsociety.simulation.agentsociety.MIN_ID
```

````

````{py:data} MAX_ID
:canonical: agentsociety.simulation.agentsociety.MAX_ID
:value: >
   100000000

```{autodoc2-docstring} agentsociety.simulation.agentsociety.MAX_ID
```

````

````{py:function} _init_agent_class(agent_config: agentsociety.configs.AgentConfig, s3config: agentsociety.s3.S3Config)
:canonical: agentsociety.simulation.agentsociety._init_agent_class

```{autodoc2-docstring} agentsociety.simulation.agentsociety._init_agent_class
```
````

`````{py:class} AgentSociety(config: agentsociety.configs.Config, tenant_id: str = '')
:canonical: agentsociety.simulation.agentsociety.AgentSociety

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.__init__
```

````{py:method} init()
:canonical: agentsociety.simulation.agentsociety.AgentSociety.init
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.init
```

````

````{py:method} close()
:canonical: agentsociety.simulation.agentsociety.AgentSociety.close
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.close
```

````

````{py:property} name
:canonical: agentsociety.simulation.agentsociety.AgentSociety.name

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.name
```

````

````{py:property} config
:canonical: agentsociety.simulation.agentsociety.AgentSociety.config

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.config
```

````

````{py:property} enable_avro
:canonical: agentsociety.simulation.agentsociety.AgentSociety.enable_avro

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.enable_avro
```

````

````{py:property} enable_pgsql
:canonical: agentsociety.simulation.agentsociety.AgentSociety.enable_pgsql

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.enable_pgsql
```

````

````{py:property} environment
:canonical: agentsociety.simulation.agentsociety.AgentSociety.environment

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.environment
```

````

````{py:property} messager
:canonical: agentsociety.simulation.agentsociety.AgentSociety.messager

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.messager
```

````

````{py:property} mlflow_client
:canonical: agentsociety.simulation.agentsociety.AgentSociety.mlflow_client

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.mlflow_client
```

````

````{py:method} _extract_target_agent_ids(target_agent: typing.Optional[typing.Union[list[int], agentsociety.configs.AgentFilterConfig]] = None) -> list[int]
:canonical: agentsociety.simulation.agentsociety.AgentSociety._extract_target_agent_ids
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety._extract_target_agent_ids
```

````

````{py:method} gather(content: str, target_agent_ids: typing.Optional[list[int]] = None, flatten: bool = False, keep_id: bool = False) -> typing.Union[dict[int, typing.Any], list[typing.Any]]
:canonical: agentsociety.simulation.agentsociety.AgentSociety.gather
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.gather
```

````

````{py:method} filter(types: typing.Optional[tuple[type[agentsociety.agent.Agent]]] = None, memory_kv: typing.Optional[dict[str, typing.Any]] = None) -> list[int]
:canonical: agentsociety.simulation.agentsociety.AgentSociety.filter
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.filter
```

````

````{py:method} update_environment(key: str, value: str)
:canonical: agentsociety.simulation.agentsociety.AgentSociety.update_environment
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.update_environment
```

````

````{py:method} update(target_agent_ids: list[int], target_key: str, content: typing.Any)
:canonical: agentsociety.simulation.agentsociety.AgentSociety.update
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.update
```

````

````{py:method} economy_update(target_agent_id: int, target_key: str, content: typing.Any, mode: typing.Literal[replace, merge] = 'replace')
:canonical: agentsociety.simulation.agentsociety.AgentSociety.economy_update
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.economy_update
```

````

````{py:method} send_survey(survey: agentsociety.survey.models.Survey, agent_ids: list[int] = [], poll_interval: float = 3, timeout: float = -1)
:canonical: agentsociety.simulation.agentsociety.AgentSociety.send_survey
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.send_survey
```

````

````{py:method} send_interview_message(content: str, agent_ids: list[int], poll_interval: float = 3, timeout: float = -1)
:canonical: agentsociety.simulation.agentsociety.AgentSociety.send_interview_message
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.send_interview_message
```

````

````{py:method} send_intervention_message(intervention_message: str, agent_ids: list[int])
:canonical: agentsociety.simulation.agentsociety.AgentSociety.send_intervention_message
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.send_intervention_message
```

````

````{py:method} extract_metric(metric_extractors: list[agentsociety.configs.MetricExtractorConfig])
:canonical: agentsociety.simulation.agentsociety.AgentSociety.extract_metric
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.extract_metric
```

````

````{py:method} _save_exp_info() -> None
:canonical: agentsociety.simulation.agentsociety.AgentSociety._save_exp_info
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety._save_exp_info
```

````

````{py:method} _save_global_prompt(prompt: str, day: int, t: float)
:canonical: agentsociety.simulation.agentsociety.AgentSociety._save_global_prompt
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety._save_global_prompt
```

````

````{py:method} delete_agents(target_agent_ids: list[int])
:canonical: agentsociety.simulation.agentsociety.AgentSociety.delete_agents
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.delete_agents
```

````

````{py:method} next_round()
:canonical: agentsociety.simulation.agentsociety.AgentSociety.next_round
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.next_round
```

````

````{py:method} step(num_environment_ticks: int = 1) -> agentsociety.simulation.type.Logs
:canonical: agentsociety.simulation.agentsociety.AgentSociety.step
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.step
```

````

````{py:method} run_one_day(ticks_per_step: int)
:canonical: agentsociety.simulation.agentsociety.AgentSociety.run_one_day
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.run_one_day
```

````

````{py:method} run()
:canonical: agentsociety.simulation.agentsociety.AgentSociety.run
:async:

```{autodoc2-docstring} agentsociety.simulation.agentsociety.AgentSociety.run
```

````

`````
