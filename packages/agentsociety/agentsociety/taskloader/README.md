# `taskloader/` — Task Loading and Management

This package provides a PyTorch `DataLoader`–inspired interface for loading structured tasks and assigning them to agents.

---

## Files

| File | Purpose |
|---|---|
| `taskloader.py` | `TaskLoader`, `Task`, `TaskStatus` |

---

## Key Types

### `TaskStatus`

```python
class TaskStatus(Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
```

### `Task`

The base dataclass for all task types:

```python
@dataclass
class Task:
    ground_truth: Any              # expected answer / label
    task_id: int                   # unique identifier
    status: TaskStatus = PENDING
    result: Optional[Any] = None   # filled by the agent
    assigned_agent_id: Optional[int] = None

    def get_task_context(self) -> dict:
        """Returns all fields except the basic ones (task_id, status, result, ground_truth)."""

    def set_result(self, result: Any) -> None:
        """Marks task as COMPLETED and stores result."""
```

Subclass `Task` to add domain-specific fields:

```python
@dataclass
class QATask(Task):
    question: str = ""
    context_text: str = ""
    source_doc: str = ""
```

### `TaskLoader`

```python
loader = TaskLoader(
    task_class=QATask,
    task_file="tasks.jsonl",     # JSON or JSONL format
    shuffle=False,
    batch_size=1,
)

# Get next batch
tasks = loader.get_next_batch(n=4)    # list of Task objects

# Track completion
loader.mark_completed(task_id=0, result="Paris")
stats = loader.get_stats()
# {"total": 100, "pending": 96, "running": 4, "completed": 0}
```

---

## Task File Format

**JSONL** (one task per line):

```jsonl
{"task_id": 0, "question": "What is 2+2?", "ground_truth": "4"}
{"task_id": 1, "question": "Capital of France?", "ground_truth": "Paris"}
```

**JSON** (array):

```json
[
  {"task_id": 0, "question": "...", "ground_truth": "..."},
  {"task_id": 1, "question": "...", "ground_truth": "..."}
]
```

---

## Integration with `IndividualEngine`

`IndividualEngine` uses `TaskLoader` internally:

1. Loads all tasks at startup.
2. Assigns tasks to `IndividualAgentBase` agents in round-robin fashion.
3. Waits until all tasks reach `COMPLETED` status.
4. Writes results to storage for evaluation.

---

## `TaskLoaderConfig`

```python
class TaskLoaderConfig(BaseModel):
    task_class: type[Task]
    task_file: str
    shuffle: bool = False
```

---

## Custom Task Example

```python
from dataclasses import dataclass
from agentsociety.taskloader import Task

@dataclass
class CodeTask(Task):
    problem_statement: str = ""
    test_cases: list = field(default_factory=list)
    language: str = "python"
```

The loader will automatically populate all fields from the JSON file using the dataclass field names.
