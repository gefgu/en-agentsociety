# `utils/` — Shared Utility Functions

This package contains utility decorators and helpers used across the framework.

---

## Files

| File | Purpose |
|---|---|
| `decorators.py` | `lock_decorator` — async lock wrapping utility |

---

## `lock_decorator`

A decorator factory that wraps an `async` method with an `asyncio.Lock` to ensure exclusive access.

```python
from agentsociety.utils.decorators import lock_decorator

class MyStore:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._data = {}

    @lock_decorator("_lock")
    async def update(self, key, value):
        self._data[key] = value

    @lock_decorator("_lock")
    async def get(self, key):
        return self._data.get(key)
```

The decorator takes the **name of the lock attribute** on `self` as a string, so the same decorator factory works with any class attribute holding an `asyncio.Lock`.

This pattern is used throughout `KVMemory` and `StreamMemory` to guarantee thread-safe concurrent reads and writes from multiple Ray task coroutines.

---

## Adding New Utilities

Place general-purpose helpers that do not belong to a specific module here. Avoid importing from higher-level package modules to prevent circular imports.
