# {py:mod}`agentsociety.simulation.agentgroup`

```{py:module} agentsociety.simulation.agentgroup
```

```{autodoc2-docstring} agentsociety.simulation.agentgroup
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AgentGroup <agentsociety.simulation.agentgroup.AgentGroup>`
  - ```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.simulation.agentgroup.__all__>`
  - ```{autodoc2-docstring} agentsociety.simulation.agentgroup.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.simulation.agentgroup.__all__
:value: >
   ['AgentGroup']

```{autodoc2-docstring} agentsociety.simulation.agentgroup.__all__
```

````

`````{py:class} AgentGroup(tenant_id: str, exp_name: str, exp_id: str, group_id: str, config: agentsociety.configs.Config, agent_inits: list[tuple[int, type[typing.Union[agentsociety.agent.CitizenAgentBase, agentsociety.agent.FirmAgentBase, agentsociety.agent.BankAgentBase, agentsociety.agent.NBSAgentBase, agentsociety.agent.GovernmentAgentBase]], agentsociety.agent.memory_config_generator.MemoryConfigGenerator, int, agentsociety.agent.AgentParams, dict[type[agentsociety.agent.Block], agentsociety.agent.BlockParams]]], environment_init: dict, pgsql_writer: typing.Optional[ray.ObjectRef], message_interceptor: ray.ObjectRef, mlflow_run_id: typing.Optional[str], agent_config_file: typing.Optional[dict[type[agentsociety.agent.Agent], typing.Any]] = None)
:canonical: agentsociety.simulation.agentgroup.AgentGroup

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup
```

```{rubric} Initialization
```

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.__init__
```

````{py:property} config
:canonical: agentsociety.simulation.agentgroup.AgentGroup.config

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.config
```

````

````{py:property} embedding_model
:canonical: agentsociety.simulation.agentgroup.AgentGroup.embedding_model

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.embedding_model
```

````

````{py:property} faiss_query
:canonical: agentsociety.simulation.agentgroup.AgentGroup.faiss_query

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.faiss_query
```

````

````{py:property} llm
:canonical: agentsociety.simulation.agentgroup.AgentGroup.llm

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.llm
```

````

````{py:property} environment
:canonical: agentsociety.simulation.agentgroup.AgentGroup.environment

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.environment
```

````

````{py:property} messager
:canonical: agentsociety.simulation.agentgroup.AgentGroup.messager

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.messager
```

````

````{py:property} agent_count
:canonical: agentsociety.simulation.agentgroup.AgentGroup.agent_count

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.agent_count
```

````

````{py:property} agent_ids
:canonical: agentsociety.simulation.agentgroup.AgentGroup.agent_ids

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.agent_ids
```

````

````{py:method} init()
:canonical: agentsociety.simulation.agentgroup.AgentGroup.init
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.init
```

````

````{py:method} close()
:canonical: agentsociety.simulation.agentgroup.AgentGroup.close
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.close
```

````

````{py:method} reset()
:canonical: agentsociety.simulation.agentgroup.AgentGroup.reset
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.reset
```

````

````{py:method} step(tick: int)
:canonical: agentsociety.simulation.agentgroup.AgentGroup.step
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.step
```

````

````{py:method} react_to_intervention(intervention_message: str, agent_ids: list[int])
:canonical: agentsociety.simulation.agentgroup.AgentGroup.react_to_intervention
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.react_to_intervention
```

````

````{py:method} _message_dispatch()
:canonical: agentsociety.simulation.agentgroup.AgentGroup._message_dispatch
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup._message_dispatch
```

````

````{py:method} save(day: int, t: int)
:canonical: agentsociety.simulation.agentgroup.AgentGroup.save
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.save
```

````

````{py:method} save_status(day: int, t: int)
:canonical: agentsociety.simulation.agentgroup.AgentGroup.save_status
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.save_status
```

````

````{py:method} update_environment(key: str, value: str)
:canonical: agentsociety.simulation.agentgroup.AgentGroup.update_environment
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.update_environment
```

````

````{py:method} update(target_agent_id: int, target_key: str, content: typing.Any)
:canonical: agentsociety.simulation.agentgroup.AgentGroup.update
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.update
```

````

````{py:method} get_llm_consumption()
:canonical: agentsociety.simulation.agentgroup.AgentGroup.get_llm_consumption

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.get_llm_consumption
```

````

````{py:method} get_llm_error_statistics()
:canonical: agentsociety.simulation.agentgroup.AgentGroup.get_llm_error_statistics
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.get_llm_error_statistics
```

````

````{py:method} filter(types: typing.Optional[tuple[type[agentsociety.agent.Agent]]] = None, memory_kv: typing.Optional[dict[str, typing.Any]] = None) -> list[int]
:canonical: agentsociety.simulation.agentgroup.AgentGroup.filter
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.filter
```

````

````{py:method} final()
:canonical: agentsociety.simulation.agentgroup.AgentGroup.final
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.final
```

````

````{py:method} gather(content: str, target_agent_ids: typing.Optional[list[int]] = None)
:canonical: agentsociety.simulation.agentgroup.AgentGroup.gather
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.gather
```

````

````{py:method} delete_agents(target_agent_ids: list[int])
:canonical: agentsociety.simulation.agentgroup.AgentGroup.delete_agents
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.delete_agents
```

````

````{py:method} forward_message(validation_dict: agentsociety.message.MessageIdentifier)
:canonical: agentsociety.simulation.agentgroup.AgentGroup.forward_message
:async:

```{autodoc2-docstring} agentsociety.simulation.agentgroup.AgentGroup.forward_message
```

````

`````
