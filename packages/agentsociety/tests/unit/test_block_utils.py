from agentsociety.cityagent.blocks.utils import coerce_minutes


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
