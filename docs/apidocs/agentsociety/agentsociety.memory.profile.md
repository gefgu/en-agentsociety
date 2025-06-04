# {py:mod}`agentsociety.memory.profile`

```{py:module} agentsociety.memory.profile
```

```{autodoc2-docstring} agentsociety.memory.profile
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ProfileMemoryUnit <agentsociety.memory.profile.ProfileMemoryUnit>`
  -
* - {py:obj}`ProfileMemory <agentsociety.memory.profile.ProfileMemory>`
  -
````

### API

```{py:class} ProfileMemoryUnit(content: agentsociety.memory.const.Optional[dict] = None, activate_timestamp: bool = False)
:canonical: agentsociety.memory.profile.ProfileMemoryUnit

Bases: {py:obj}`agentsociety.memory.memory_base.MemoryUnit`

```

`````{py:class} ProfileMemory(msg: agentsociety.memory.const.Optional[typing.Union[agentsociety.memory.profile.ProfileMemoryUnit, collections.abc.Sequence[agentsociety.memory.profile.ProfileMemoryUnit], dict, collections.abc.Sequence[dict]]] = None, activate_timestamp: bool = False)
:canonical: agentsociety.memory.profile.ProfileMemory

Bases: {py:obj}`agentsociety.memory.memory_base.MemoryBase`

````{py:method} add(msg: typing.Union[agentsociety.memory.profile.ProfileMemoryUnit, collections.abc.Sequence[agentsociety.memory.profile.ProfileMemoryUnit]]) -> None
:canonical: agentsociety.memory.profile.ProfileMemory.add
:async:

````

````{py:method} pop(index: int) -> agentsociety.memory.profile.ProfileMemoryUnit
:canonical: agentsociety.memory.profile.ProfileMemory.pop
:async:

````

````{py:method} load(snapshots: typing.Union[dict, collections.abc.Sequence[dict]], reset_memory: bool = False) -> None
:canonical: agentsociety.memory.profile.ProfileMemory.load
:async:

````

````{py:method} export() -> collections.abc.Sequence[dict]
:canonical: agentsociety.memory.profile.ProfileMemory.export
:async:

````

````{py:method} reset() -> None
:canonical: agentsociety.memory.profile.ProfileMemory.reset
:async:

````

````{py:method} get(key: typing.Any)
:canonical: agentsociety.memory.profile.ProfileMemory.get
:async:

````

````{py:method} update(key: typing.Any, value: typing.Any, store_snapshot: bool = False)
:canonical: agentsociety.memory.profile.ProfileMemory.update
:async:

````

````{py:method} update_dict(to_update_dict: dict, store_snapshot: bool = False)
:canonical: agentsociety.memory.profile.ProfileMemory.update_dict
:async:

```{autodoc2-docstring} agentsociety.memory.profile.ProfileMemory.update_dict
```

````

`````
