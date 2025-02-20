# {py:mod}`agentsociety.memory.self_define`

```{py:module} agentsociety.memory.self_define
```

```{autodoc2-docstring} agentsociety.memory.self_define
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DynamicMemoryUnit <agentsociety.memory.self_define.DynamicMemoryUnit>`
  -
* - {py:obj}`DynamicMemory <agentsociety.memory.self_define.DynamicMemory>`
  -
````

### API

```{py:class} DynamicMemoryUnit(content: typing.Optional[dict] = None, required_attributes: typing.Optional[dict] = None, activate_timestamp: bool = False)
:canonical: agentsociety.memory.self_define.DynamicMemoryUnit

Bases: {py:obj}`agentsociety.memory.memory_base.MemoryUnit`

```

`````{py:class} DynamicMemory(required_attributes: dict[typing.Any, typing.Any], activate_timestamp: bool = False)
:canonical: agentsociety.memory.self_define.DynamicMemory

Bases: {py:obj}`agentsociety.memory.memory_base.MemoryBase`

````{py:method} add(msg: typing.Union[agentsociety.memory.self_define.DynamicMemoryUnit, collections.abc.Sequence[agentsociety.memory.self_define.DynamicMemoryUnit]]) -> None
:canonical: agentsociety.memory.self_define.DynamicMemory.add
:async:

````

````{py:method} pop(index: int) -> agentsociety.memory.self_define.DynamicMemoryUnit
:canonical: agentsociety.memory.self_define.DynamicMemory.pop
:async:

````

````{py:method} load(snapshots: typing.Union[dict, collections.abc.Sequence[dict]], reset_memory: bool = False) -> None
:canonical: agentsociety.memory.self_define.DynamicMemory.load
:async:

````

````{py:method} export() -> collections.abc.Sequence[dict]
:canonical: agentsociety.memory.self_define.DynamicMemory.export
:async:

````

````{py:method} reset() -> None
:canonical: agentsociety.memory.self_define.DynamicMemory.reset
:async:

````

````{py:method} get(key: typing.Any)
:canonical: agentsociety.memory.self_define.DynamicMemory.get
:async:

````

````{py:method} update(key: typing.Any, value: typing.Any, store_snapshot: bool = False)
:canonical: agentsociety.memory.self_define.DynamicMemory.update
:async:

````

````{py:method} update_dict(to_update_dict: dict, store_snapshot: bool = False)
:canonical: agentsociety.memory.self_define.DynamicMemory.update_dict
:async:

```{autodoc2-docstring} agentsociety.memory.self_define.DynamicMemory.update_dict
```

````

`````
