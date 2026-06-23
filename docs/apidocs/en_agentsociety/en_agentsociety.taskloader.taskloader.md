# {py:mod}`en_agentsociety.taskloader.taskloader`

```{py:module} en_agentsociety.taskloader.taskloader
```

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`TaskStatus <en_agentsociety.taskloader.taskloader.TaskStatus>`
  - ```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskStatus
    :summary:
    ```
* - {py:obj}`Task <en_agentsociety.taskloader.taskloader.Task>`
  - ```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task
    :summary:
    ```
* - {py:obj}`TaskLoader <en_agentsociety.taskloader.taskloader.TaskLoader>`
  - ```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader
    :summary:
    ```
````

### API

`````{py:class} TaskStatus(*args, **kwds)
:canonical: en_agentsociety.taskloader.taskloader.TaskStatus

Bases: {py:obj}`enum.Enum`

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskStatus
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskStatus.__init__
```

````{py:attribute} PENDING
:canonical: en_agentsociety.taskloader.taskloader.TaskStatus.PENDING
:value: >
   'pending'

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskStatus.PENDING
```

````

````{py:attribute} RUNNING
:canonical: en_agentsociety.taskloader.taskloader.TaskStatus.RUNNING
:value: >
   'running'

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskStatus.RUNNING
```

````

````{py:attribute} COMPLETED
:canonical: en_agentsociety.taskloader.taskloader.TaskStatus.COMPLETED
:value: >
   'completed'

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskStatus.COMPLETED
```

````

`````

`````{py:class} Task
:canonical: en_agentsociety.taskloader.taskloader.Task

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task
```

````{py:attribute} ground_truth
:canonical: en_agentsociety.taskloader.taskloader.Task.ground_truth
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.ground_truth
```

````

````{py:attribute} task_id
:canonical: en_agentsociety.taskloader.taskloader.Task.task_id
:type: int
:value: >
   None

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.task_id
```

````

````{py:attribute} status
:canonical: en_agentsociety.taskloader.taskloader.Task.status
:type: en_agentsociety.taskloader.taskloader.TaskStatus
:value: >
   None

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.status
```

````

````{py:attribute} result
:canonical: en_agentsociety.taskloader.taskloader.Task.result
:type: typing.Optional[typing.Any]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.result
```

````

````{py:attribute} assigned_agent_id
:canonical: en_agentsociety.taskloader.taskloader.Task.assigned_agent_id
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.assigned_agent_id
```

````

````{py:method} get_task_context() -> dict[str, typing.Any]
:canonical: en_agentsociety.taskloader.taskloader.Task.get_task_context

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.get_task_context
```

````

````{py:method} set_result(result: typing.Any) -> None
:canonical: en_agentsociety.taskloader.taskloader.Task.set_result

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.set_result
```

````

````{py:method} set_running() -> None
:canonical: en_agentsociety.taskloader.taskloader.Task.set_running

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.set_running
```

````

````{py:method} reset() -> None
:canonical: en_agentsociety.taskloader.taskloader.Task.reset

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.reset
```

````

````{py:method} assign_to_agent(agent_id: int) -> None
:canonical: en_agentsociety.taskloader.taskloader.Task.assign_to_agent

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.Task.assign_to_agent
```

````

`````

`````{py:class} TaskLoader(task_type: type[en_agentsociety.taskloader.taskloader.Task], file_path: str, shuffle: bool = False, max_tasks: typing.Optional[int] = None)
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.__init__
```

````{py:method} _load_tasks() -> None
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader._load_tasks

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader._load_tasks
```

````

````{py:method} next(n: int = 1) -> typing.Optional[typing.Union[en_agentsociety.taskloader.taskloader.Task, typing.List[en_agentsociety.taskloader.taskloader.Task]]]
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.next

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.next
```

````

````{py:method} get_pending_count() -> int
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.get_pending_count

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.get_pending_count
```

````

````{py:method} get_completed_count() -> int
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.get_completed_count

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.get_completed_count
```

````

````{py:method} get_running_count() -> int
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.get_running_count

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.get_running_count
```

````

````{py:method} reset_all() -> None
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.reset_all

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.reset_all
```

````

````{py:method} get_task_by_id(task_id: str) -> typing.Optional[en_agentsociety.taskloader.taskloader.Task]
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.get_task_by_id

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.get_task_by_id
```

````

````{py:method} get_tasks_by_status(status: en_agentsociety.taskloader.taskloader.TaskStatus) -> typing.List[en_agentsociety.taskloader.taskloader.Task]
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.get_tasks_by_status

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.get_tasks_by_status
```

````

````{py:method} __len__() -> int
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.__len__

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.__len__
```

````

````{py:method} __iter__()
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.__iter__

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.__iter__
```

````

````{py:method} __next__() -> en_agentsociety.taskloader.taskloader.Task
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.__next__

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.__next__
```

````

````{py:method} get_task_results()
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.get_task_results

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.get_task_results
```

````

````{py:method} get_uncollected_completed_count() -> int
:canonical: en_agentsociety.taskloader.taskloader.TaskLoader.get_uncollected_completed_count

```{autodoc2-docstring} en_agentsociety.taskloader.taskloader.TaskLoader.get_uncollected_completed_count
```

````

`````
