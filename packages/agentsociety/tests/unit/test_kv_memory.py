import asyncio
from collections import deque
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agentsociety.memory.kv_memory import KVMemory, _MISSING


def make_memory(data: dict):
    memory = KVMemory.__new__(KVMemory)
    memory._memory_config = SimpleNamespace(attributes={})
    memory._data = data
    memory._vectorstore = AsyncMock()
    memory._key_to_doc_id = {}
    memory._lock = asyncio.Lock()
    return memory


@pytest.mark.asyncio
async def test_get_many_returns_deep_copied_values_and_defaults():
    memory = make_memory({"profile": {"age": 30}})

    values = await memory.get_many(
        {
            "profile": _MISSING,
            "missing": {"fallback": []},
        }
    )

    values["profile"]["age"] = 40
    values["missing"]["fallback"].append("changed")

    assert await memory.get("profile") == {"age": 30}
    values_again = await memory.get_many({"missing": {"fallback": []}})
    assert values_again["missing"] == {"fallback": []}


@pytest.mark.asyncio
async def test_get_many_raises_for_missing_key_without_default():
    memory = make_memory({})

    with pytest.raises(KeyError, match="No attribute `missing` in memories!"):
        await memory.get_many({"missing": _MISSING})


@pytest.mark.asyncio
async def test_update_many_replaces_multiple_fields():
    memory = make_memory({"hunger": 0.5, "energy": 0.5})

    await memory.update_many({"hunger": 0.7, "energy": 0.9})

    assert await memory.get_many({"hunger": _MISSING, "energy": _MISSING}) == {
        "hunger": 0.7,
        "energy": 0.9,
    }


@pytest.mark.asyncio
async def test_update_many_merge_preserves_existing_merge_behavior():
    memory = make_memory(
        {
            "dict_value": {"a": 1},
            "list_value": [1],
            "set_value": {1},
            "deque_value": deque([1]),
        }
    )

    await memory.update_many(
        {
            "dict_value": {"b": 2},
            "list_value": [2],
            "set_value": {2},
            "deque_value": deque([2]),
        },
        mode="merge",
    )

    values = await memory.get_many(
        {
            "dict_value": _MISSING,
            "list_value": _MISSING,
            "set_value": _MISSING,
            "deque_value": _MISSING,
        }
    )

    assert values["dict_value"] == {"a": 1, "b": 2}
    assert values["list_value"] == [1, 2]
    assert values["set_value"] == {1, 2}
    assert values["deque_value"] == deque([1, 2])
