# {py:mod}`agentsociety.agent.toolbox`

```{py:module} agentsociety.agent.toolbox
```

```{autodoc2-docstring} agentsociety.agent.toolbox
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AgentToolbox <agentsociety.agent.toolbox.AgentToolbox>`
  - ```{autodoc2-docstring} agentsociety.agent.toolbox.AgentToolbox
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <agentsociety.agent.toolbox.__all__>`
  - ```{autodoc2-docstring} agentsociety.agent.toolbox.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: agentsociety.agent.toolbox.__all__
:value: >
   ['AgentToolbox']

```{autodoc2-docstring} agentsociety.agent.toolbox.__all__
```

````

`````{py:class} AgentToolbox
:canonical: agentsociety.agent.toolbox.AgentToolbox

Bases: {py:obj}`typing.NamedTuple`

```{autodoc2-docstring} agentsociety.agent.toolbox.AgentToolbox
```

````{py:attribute} llm
:canonical: agentsociety.agent.toolbox.AgentToolbox.llm
:type: agentsociety.llm.llm.LLM
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.toolbox.AgentToolbox.llm
```

````

````{py:attribute} environment
:canonical: agentsociety.agent.toolbox.AgentToolbox.environment
:type: agentsociety.environment.environment.Environment
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.toolbox.AgentToolbox.environment
```

````

````{py:attribute} messager
:canonical: agentsociety.agent.toolbox.AgentToolbox.messager
:type: agentsociety.message.Messager
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.toolbox.AgentToolbox.messager
```

````

````{py:attribute} embedding
:canonical: agentsociety.agent.toolbox.AgentToolbox.embedding
:type: fastembed.SparseTextEmbedding
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.toolbox.AgentToolbox.embedding
```

````

````{py:attribute} database_writer
:canonical: agentsociety.agent.toolbox.AgentToolbox.database_writer
:type: typing.Optional[agentsociety.storage.DatabaseWriter]
:value: >
   None

```{autodoc2-docstring} agentsociety.agent.toolbox.AgentToolbox.database_writer
```

````

`````
