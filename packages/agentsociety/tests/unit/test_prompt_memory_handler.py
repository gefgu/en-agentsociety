from typing import Any

import pytest

from agentsociety.prompts.prompt_memory_handler import PromptMemoryHandler


class _Status:
    def __init__(self, values: dict[str, Any]):
        self._values = values

    async def get_many(self, defaults: dict[str, Any]) -> dict[str, Any]:
        return {
            key: self._values.get(key, default)
            for key, default in defaults.items()
        }


class _Memory:
    def __init__(self, values: dict[str, Any]):
        self.status = _Status(values)


@pytest.mark.asyncio
async def test_resolve_location_uses_nested_aoi_id():
    memory = _Memory(
        {
            "position": {"aoi_position": {"aoi_id": 12, "poi_id": 3}},
            "home": {"aoi_position": {"aoi_id": 1}},
            "work": {"aoi_position": {"aoi_id": 2}},
            "location_knowledge": {
                "gym": {"id": 12, "description": "nearby gym"},
            },
        }
    )

    result = await PromptMemoryHandler().resolve_location("current_location", memory)

    assert result == "12"


@pytest.mark.asyncio
async def test_resolve_location_does_not_raise_for_unhashable_aoi_position():
    memory = _Memory(
        {
            "position": {"aoi_position": {"aoi_id": ["bad", "id"]}},
            "home": {"aoi_position": {"aoi_id": 1}},
            "work": {"aoi_position": {"aoi_id": 2}},
            "location_knowledge": {
                "bad": {"id": {"aoi_position": {"aoi_id": ["bad", "id"]}}},
            },
        }
    )

    result = await PromptMemoryHandler().resolve_location("current_location", memory)

    assert result == "Outside"
