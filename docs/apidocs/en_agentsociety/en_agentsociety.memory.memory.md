# {py:mod}`en_agentsociety.memory.memory`

```{py:module} en_agentsociety.memory.memory
```

```{autodoc2-docstring} en_agentsociety.memory.memory
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`KVMemory <en_agentsociety.memory.memory.KVMemory>`
  - ```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory
    :summary:
    ```
* - {py:obj}`MemoryNode <en_agentsociety.memory.memory.MemoryNode>`
  - ```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode
    :summary:
    ```
* - {py:obj}`StreamMemory <en_agentsociety.memory.memory.StreamMemory>`
  - ```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory
    :summary:
    ```
* - {py:obj}`Memory <en_agentsociety.memory.memory.Memory>`
  - ```{autodoc2-docstring} en_agentsociety.memory.memory.Memory
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.memory.memory.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.memory.memory.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.memory.memory.__all__
:value: >
   ['KVMemory', 'StreamMemory', 'Memory']

```{autodoc2-docstring} en_agentsociety.memory.memory.__all__
```

````

`````{py:class} KVMemory(memory_config: en_agentsociety.agent.memory_config_generator.MemoryConfig, embedding: fastembed.SparseTextEmbedding)
:canonical: en_agentsociety.memory.memory.KVMemory

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory.__init__
```

````{py:method} initialize_embeddings() -> None
:canonical: en_agentsociety.memory.memory.KVMemory.initialize_embeddings
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory.initialize_embeddings
```

````

````{py:method} _generate_semantic_text(key: str, value: typing.Any) -> str
:canonical: en_agentsociety.memory.memory.KVMemory._generate_semantic_text

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory._generate_semantic_text
```

````

````{py:method} search(query: str, top_k: int = 3, filter: typing.Optional[dict] = None) -> str
:canonical: en_agentsociety.memory.memory.KVMemory.search
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory.search
```

````

````{py:method} should_embed(key: str) -> bool
:canonical: en_agentsociety.memory.memory.KVMemory.should_embed

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory.should_embed
```

````

````{py:method} get(key: typing.Any, default_value: typing.Optional[typing.Any] = None) -> typing.Any
:canonical: en_agentsociety.memory.memory.KVMemory.get
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory.get
```

````

````{py:method} update(key: typing.Any, value: typing.Any, mode: typing.Union[typing.Literal[replace], typing.Literal[merge]] = 'replace') -> None
:canonical: en_agentsociety.memory.memory.KVMemory.update
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory.update
```

````

````{py:method} export(keys: list[str]) -> dict[str, typing.Any]
:canonical: en_agentsociety.memory.memory.KVMemory.export
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.KVMemory.export
```

````

`````

`````{py:class} MemoryNode
:canonical: en_agentsociety.memory.memory.MemoryNode

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode
```

````{py:attribute} topic
:canonical: en_agentsociety.memory.memory.MemoryNode.topic
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode.topic
```

````

````{py:attribute} day
:canonical: en_agentsociety.memory.memory.MemoryNode.day
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode.day
```

````

````{py:attribute} t
:canonical: en_agentsociety.memory.memory.MemoryNode.t
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode.t
```

````

````{py:attribute} location
:canonical: en_agentsociety.memory.memory.MemoryNode.location
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode.location
```

````

````{py:attribute} description
:canonical: en_agentsociety.memory.memory.MemoryNode.description
:type: str
:value: >
   None

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode.description
```

````

````{py:attribute} cognition_id
:canonical: en_agentsociety.memory.memory.MemoryNode.cognition_id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode.cognition_id
```

````

````{py:attribute} id
:canonical: en_agentsociety.memory.memory.MemoryNode.id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.memory.memory.MemoryNode.id
```

````

`````

`````{py:class} StreamMemory(environment: typing.Optional[en_agentsociety.environment.Environment], status_memory: en_agentsociety.memory.memory.KVMemory, embedding: fastembed.SparseTextEmbedding, max_len: int = 1000)
:canonical: en_agentsociety.memory.memory.StreamMemory

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.__init__
```

````{py:method} add(topic: str, description: str) -> int
:canonical: en_agentsociety.memory.memory.StreamMemory.add
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.add
```

````

````{py:method} get_related_cognition(memory_id: int) -> typing.Union[en_agentsociety.memory.memory.MemoryNode, None]
:canonical: en_agentsociety.memory.memory.StreamMemory.get_related_cognition
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.get_related_cognition
```

````

````{py:method} format_memory(memories: list[en_agentsociety.memory.memory.MemoryNode]) -> str
:canonical: en_agentsociety.memory.memory.StreamMemory.format_memory
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.format_memory
```

````

````{py:method} get_by_ids(memory_ids: list[int]) -> str
:canonical: en_agentsociety.memory.memory.StreamMemory.get_by_ids
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.get_by_ids
```

````

````{py:method} search(query: str, topic: typing.Optional[str] = None, top_k: int = 3, day_range: typing.Optional[tuple[int, int]] = None, time_range: typing.Optional[tuple[int, int]] = None) -> str
:canonical: en_agentsociety.memory.memory.StreamMemory.search
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.search
```

````

````{py:method} search_today(query: str = '', topic: typing.Optional[str] = None, top_k: int = 100) -> str
:canonical: en_agentsociety.memory.memory.StreamMemory.search_today
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.search_today
```

````

````{py:method} add_cognition_to_memory(memory_ids: list[int], cognition: str) -> None
:canonical: en_agentsociety.memory.memory.StreamMemory.add_cognition_to_memory
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.add_cognition_to_memory
```

````

````{py:method} get_all() -> list[dict]
:canonical: en_agentsociety.memory.memory.StreamMemory.get_all
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.StreamMemory.get_all
```

````

`````

`````{py:class} Memory(environment: typing.Optional[en_agentsociety.environment.Environment], embedding: fastembed.SparseTextEmbedding, memory_config: en_agentsociety.agent.memory_config_generator.MemoryConfig)
:canonical: en_agentsociety.memory.memory.Memory

```{autodoc2-docstring} en_agentsociety.memory.memory.Memory
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.memory.memory.Memory.__init__
```

````{py:property} status
:canonical: en_agentsociety.memory.memory.Memory.status
:type: en_agentsociety.memory.memory.KVMemory

```{autodoc2-docstring} en_agentsociety.memory.memory.Memory.status
```

````

````{py:property} stream
:canonical: en_agentsociety.memory.memory.Memory.stream
:type: en_agentsociety.memory.memory.StreamMemory

```{autodoc2-docstring} en_agentsociety.memory.memory.Memory.stream
```

````

````{py:method} initialize_embeddings()
:canonical: en_agentsociety.memory.memory.Memory.initialize_embeddings
:async:

```{autodoc2-docstring} en_agentsociety.memory.memory.Memory.initialize_embeddings
```

````

`````
