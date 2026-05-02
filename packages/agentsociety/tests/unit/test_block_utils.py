from types import SimpleNamespace

import pytest

from agentsociety.prompts.prompt_manager import PromptResult
from agentsociety.cityagent.blocks.utils import coerce_minutes
from agentsociety.cityagent.blocks.needs_block import (
    NeedsBlock,
    _extract_valid_satisfaction_updates,
    _find_complete_satisfaction_dict,
    _has_complete_satisfaction_dict,
)


def test_coerce_minutes_accepts_numeric_values():
    assert coerce_minutes(12, 5) == 12
    assert coerce_minutes("12", 5) == 12
    assert coerce_minutes("12.6", 5) == 13


def test_coerce_minutes_extracts_units_from_text():
    assert coerce_minutes("30 minutes", 5) == 30
    assert coerce_minutes("1.5 hours", 5) == 90


def test_coerce_minutes_uses_default_for_unknown_values():
    assert coerce_minutes("unknown", 5) == 5
    assert coerce_minutes(None, lambda: 7) == 7


def test_coerce_minutes_clamps_bounds():
    assert coerce_minutes("-10", 5, minimum=1) == 1
    assert coerce_minutes("1000", 5, maximum=180) == 180


def test_needs_block_ensure_float_defaults_none_values():
    assert NeedsBlock._ensure_float(None, None, "hunger_satisfaction") == 0.5
    assert NeedsBlock._ensure_float(None, None, "energy_satisfaction") == 0.5
    assert NeedsBlock._ensure_float(None, None, "social_satisfaction") == 0.5


def test_needs_block_ensure_float_handles_memory_strings():
    assert NeedsBlock._ensure_float(None, "0.75", "hunger_satisfaction") == 0.75
    assert NeedsBlock._ensure_float(None, "bad", "hunger_satisfaction") == 0.5


def test_needs_initialize_validator_requires_complete_values():
    parsed = {
        "current_satisfaction": {
            "hunger_satisfaction": "0.8",
            "energy_satisfaction": 0.9,
            "safety_satisfaction": 0.85,
            "social_satisfaction": 0.5,
        }
    }
    assert _has_complete_satisfaction_dict(parsed) is True
    assert _find_complete_satisfaction_dict(parsed) == {
        "hunger_satisfaction": 0.8,
        "energy_satisfaction": 0.9,
        "safety_satisfaction": 0.85,
        "social_satisfaction": 0.5,
    }


def test_needs_initialize_validator_rejects_partial_values():
    parsed = {
        "current_satisfaction": {
            "hunger_satisfaction": 0.8,
            "energy_satisfaction": 0.9,
            "safety_satisfaction": 0.85,
        }
    }
    assert _has_complete_satisfaction_dict(parsed) is False


def test_needs_initialize_validator_accepts_json_string_value():
    parsed = {
        "current_satisfaction": """
        {
            "hunger_satisfaction": 0.75,
            "energy_satisfaction": 0.8,
            "safety_satisfaction": 0.75,
            "social_satisfaction": 0.45
        }
        """
    }
    assert _find_complete_satisfaction_dict(parsed) == {
        "hunger_satisfaction": 0.75,
        "energy_satisfaction": 0.8,
        "safety_satisfaction": 0.75,
        "social_satisfaction": 0.45,
    }


def test_valid_satisfaction_updates_skip_optional_none_fields():
    parsed = {
        "hunger_satisfaction": 0.7,
        "energy_satisfaction": None,
        "safety_satisfaction": None,
        "social_satisfaction": None,
    }
    assert _extract_valid_satisfaction_updates(parsed) == {
        "hunger_satisfaction": 0.7
    }


def test_valid_satisfaction_updates_reject_invalid_optional_values():
    parsed = {
        "hunger_satisfaction": "bad",
        "energy_satisfaction": 1.2,
        "safety_satisfaction": False,
        "social_satisfaction": None,
    }
    assert _extract_valid_satisfaction_updates(parsed) == {}


class _FakeStatus:
    def __init__(self, initial_data=None):
        self.data = {
            "hunger_satisfaction": 0.9,
            "energy_satisfaction": 0.9,
            "safety_satisfaction": 0.4,
            "social_satisfaction": 0.6,
            "current_plan": False,
            "current_need": "whatever",
            "need_fulfillment": 0,
            "plan_history": [],
        }
        if initial_data:
            self.data.update(initial_data)
        self.updated_many = []
        self.updated = []

    async def get(self, key, default_value=None):
        return self.data.get(key, default_value)

    async def get_many(self, keys):
        return {key: self.data.get(key, default) for key, default in keys.items()}

    async def update_many(self, values):
        self.updated_many.append(values)
        self.data.update(values)

    async def update(self, key, value):
        self.updated.append((key, value))
        self.data[key] = value


class _FakeStream:
    def __init__(self):
        self.items = []

    async def add(self, **kwargs):
        self.items.append(kwargs)


class _FakeMemory:
    def __init__(self, initial_data=None):
        self.status = _FakeStatus(initial_data)
        self.stream = _FakeStream()


class _FakeEnvironment:
    def __init__(self):
        self.tick = 3600

    def get_datetime(self, format_time=False):
        if format_time:
            return 0, "08:00"
        return 0, 8 * 60 * 60

    def get_tick(self):
        return self.tick

    def sense(self, key):
        if key == "workday":
            return False
        return None


class _FakeToolbox:
    def __init__(self):
        self.environment = _FakeEnvironment()

    def get_tool(self, name):
        return None


def _make_needs_block_with_prompt_result(result, initial_data=None):
    block = NeedsBlock.__new__(NeedsBlock)
    block._toolbox = _FakeToolbox()
    block._agent_memory = _FakeMemory(initial_data)
    block.context = SimpleNamespace()
    block.now_day = 0
    block.need_work = False
    block.initialized = False
    block.initial_prompt_name = "needs_initialize"
    block.evaluation_prompt_name = "needs_evaluation"
    block.last_evaluation_time = 0
    block.alpha_H = 0.15
    block.alpha_D = 0.08
    block.alpha_P = 0.05
    block.alpha_C = 0.1
    block.T_H = 0.2
    block.T_D = 0.2
    block.T_P = 0.2
    block.T_C = 0.3
    block._need_to_do = None
    block._need_to_do_checked = False
    block._last_tick_time = 0
    block.id = "test-agent"

    async def execute_prompt(*args, **kwargs):
        return result

    block.execute_prompt = execute_prompt
    return block


@pytest.mark.asyncio
async def test_needs_initialize_writes_complete_llm_values():
    result = PromptResult(
        raw_response="",
        parsed={
            "current_satisfaction": {
                "hunger_satisfaction": 0.8,
                "energy_satisfaction": 0.7,
                "safety_satisfaction": 0.6,
                "social_satisfaction": 0.5,
            }
        },
        state_dict={},
        prompt_context={},
        success=True,
    )
    block = _make_needs_block_with_prompt_result(result)

    await block.initialize()

    assert block.initialized is True
    assert block.memory.status.data["hunger_satisfaction"] == 0.8
    assert block.memory.status.data["energy_satisfaction"] == 0.7
    assert block.memory.status.data["safety_satisfaction"] == 0.6
    assert block.memory.status.data["social_satisfaction"] == 0.5


@pytest.mark.asyncio
async def test_needs_initialize_rejects_partial_success_without_overwriting_defaults():
    result = PromptResult(
        raw_response="",
        parsed={
            "current_satisfaction": {
                "hunger_satisfaction": 0.8,
                "energy_satisfaction": 0.7,
                "safety_satisfaction": 0.6,
            }
        },
        state_dict={},
        prompt_context={},
        success=True,
    )
    block = _make_needs_block_with_prompt_result(result)

    await block.initialize()

    assert block.initialized is False
    assert block.memory.status.data["hunger_satisfaction"] == 0.9
    assert block.memory.status.data["energy_satisfaction"] == 0.9
    assert block.memory.status.data["safety_satisfaction"] == 0.4
    assert block.memory.status.data["social_satisfaction"] == 0.6


@pytest.mark.asyncio
async def test_needs_normalization_repairs_none_values_to_domain_defaults():
    block = _make_needs_block_with_prompt_result(
        PromptResult("", None, {}, {}, success=False),
        {
            "hunger_satisfaction": None,
            "energy_satisfaction": None,
            "safety_satisfaction": None,
            "social_satisfaction": None,
        },
    )

    normalized = await block._get_normalized_satisfaction()

    assert normalized == {
        "hunger_satisfaction": 0.9,
        "energy_satisfaction": 0.9,
        "safety_satisfaction": 0.4,
        "social_satisfaction": 0.6,
    }
    assert block.memory.status.updated_many[-1] == normalized


@pytest.mark.asyncio
async def test_needs_normalization_converts_strings_and_repairs_invalid_values():
    block = _make_needs_block_with_prompt_result(
        PromptResult("", None, {}, {}, success=False),
        {
            "hunger_satisfaction": "0.75",
            "energy_satisfaction": "bad",
            "safety_satisfaction": 1.2,
            "social_satisfaction": False,
        },
    )

    normalized = await block._get_normalized_satisfaction()

    assert normalized == {
        "hunger_satisfaction": 0.75,
        "energy_satisfaction": 0.9,
        "safety_satisfaction": 0.4,
        "social_satisfaction": 0.6,
    }
    assert block.memory.status.updated_many[-1] == normalized


@pytest.mark.asyncio
async def test_needs_normalization_leaves_valid_values_unwritten():
    block = _make_needs_block_with_prompt_result(
        PromptResult("", None, {}, {}, success=False),
        {
            "hunger_satisfaction": 0.7,
            "energy_satisfaction": 0.8,
            "safety_satisfaction": 0.9,
            "social_satisfaction": 0.6,
        },
    )

    normalized = await block._get_normalized_satisfaction()

    assert normalized == {
        "hunger_satisfaction": 0.7,
        "energy_satisfaction": 0.8,
        "safety_satisfaction": 0.9,
        "social_satisfaction": 0.6,
    }
    assert block.memory.status.updated_many == []


@pytest.mark.asyncio
async def test_time_decay_uses_normalized_satisfaction_without_noisy_fallback(monkeypatch):
    block = _make_needs_block_with_prompt_result(
        PromptResult("", None, {}, {}, success=False),
        {
            "hunger_satisfaction": None,
            "energy_satisfaction": None,
            "safety_satisfaction": None,
            "social_satisfaction": None,
        },
    )
    monkeypatch.setattr(NeedsBlock, "_ensure_float", lambda *args: pytest.fail("_ensure_float should not be used"))

    await block.time_decay()

    assert block.memory.status.data["hunger_satisfaction"] == pytest.approx(0.75)
    assert block.memory.status.data["energy_satisfaction"] == pytest.approx(0.82)
    assert block.memory.status.data["safety_satisfaction"] == pytest.approx(0.35)
    assert block.memory.status.data["social_satisfaction"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_determine_current_need_uses_normalized_satisfaction_without_noisy_fallback(monkeypatch):
    block = _make_needs_block_with_prompt_result(
        PromptResult("", None, {}, {}, success=False),
        {
            "hunger_satisfaction": None,
            "energy_satisfaction": None,
            "safety_satisfaction": None,
            "social_satisfaction": None,
            "current_plan": None,
        },
    )
    monkeypatch.setattr(NeedsBlock, "_ensure_float", lambda *args: pytest.fail("_ensure_float should not be used"))

    cognition = await block.determine_current_need()

    assert cognition == "I have no specific needs right now"
    assert block.memory.status.data["hunger_satisfaction"] == 0.9
    assert block.memory.status.data["energy_satisfaction"] == 0.9
    assert block.memory.status.data["safety_satisfaction"] == 0.4
    assert block.memory.status.data["social_satisfaction"] == 0.6


@pytest.mark.asyncio
async def test_evaluate_and_adjust_needs_uses_normalized_satisfaction_without_noisy_fallback(monkeypatch):
    result = PromptResult(
        raw_response="",
        parsed=None,
        state_dict={},
        prompt_context={},
        success=False,
        error="stop after normalization",
    )
    block = _make_needs_block_with_prompt_result(
        result,
        {
            "hunger_satisfaction": None,
            "energy_satisfaction": None,
            "safety_satisfaction": None,
            "social_satisfaction": None,
        },
    )
    monkeypatch.setattr(NeedsBlock, "_ensure_float", lambda *args: pytest.fail("_ensure_float should not be used"))
    completed_plan = {
        "target": "rest",
        "steps": [
            {
                "intention": "rest",
                "type": "home",
                "evaluation": {"evaluation": "completed"},
            }
        ],
    }

    await block.evaluate_and_adjust_needs(completed_plan)

    assert block.memory.status.data["hunger_satisfaction"] == 0.9
    assert block.memory.status.data["energy_satisfaction"] == 0.9
    assert block.memory.status.data["safety_satisfaction"] == 0.4
    assert block.memory.status.data["social_satisfaction"] == 0.6


@pytest.mark.asyncio
async def test_evaluate_and_adjust_needs_does_not_persist_optional_none_fields():
    result = PromptResult(
        raw_response="",
        parsed={
            "hunger_satisfaction": 0.65,
            "energy_satisfaction": None,
            "safety_satisfaction": None,
            "social_satisfaction": None,
        },
        state_dict={},
        prompt_context={},
        success=True,
    )
    block = _make_needs_block_with_prompt_result(result)
    completed_plan = {
        "target": "eat",
        "steps": [
            {
                "intention": "eat",
                "type": "home",
                "evaluation": {"evaluation": "completed"},
            }
        ],
    }

    await block.evaluate_and_adjust_needs(completed_plan)

    assert block.memory.status.data["hunger_satisfaction"] == 0.65
    assert block.memory.status.data["energy_satisfaction"] == 0.9
    assert block.memory.status.data["safety_satisfaction"] == 0.4
    assert block.memory.status.data["social_satisfaction"] == 0.6
    assert block.memory.status.updated_many[-1] == {"hunger_satisfaction": 0.65}


@pytest.mark.asyncio
async def test_reflect_to_intervention_does_not_persist_optional_none_fields():
    result = PromptResult(
        raw_response="",
        parsed={
            "hunger_satisfaction": None,
            "energy_satisfaction": 0.8,
            "safety_satisfaction": None,
            "social_satisfaction": None,
        },
        state_dict={},
        prompt_context={},
        success=True,
    )
    block = _make_needs_block_with_prompt_result(
        result,
        {
            "current_plan": {
                "index": 0,
                "steps": [{"intention": "walk", "type": "mobility"}],
            }
        },
    )
    block.reflection_prompt_name = "needs_reflection"

    await block.reflect_to_intervention("slow down")

    assert block.memory.status.data["hunger_satisfaction"] == 0.9
    assert block.memory.status.data["energy_satisfaction"] == 0.8
    assert block.memory.status.data["safety_satisfaction"] == 0.4
    assert block.memory.status.data["social_satisfaction"] == 0.6
    assert block.memory.status.updated_many[-1] == {"energy_satisfaction": 0.8}


@pytest.mark.asyncio
async def test_needs_initialize_failure_keeps_existing_defaults():
    result = PromptResult(
        raw_response="",
        parsed=None,
        state_dict={},
        prompt_context={},
        success=False,
        error="Custom validation failed",
    )
    block = _make_needs_block_with_prompt_result(result)

    await block.initialize()

    assert block.initialized is False
    assert block.memory.status.data["hunger_satisfaction"] == 0.9
    assert block.memory.status.data["energy_satisfaction"] == 0.9
    assert block.memory.status.data["safety_satisfaction"] == 0.4
    assert block.memory.status.data["social_satisfaction"] == 0.6
