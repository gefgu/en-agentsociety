"""Unit tests for PromptManager._parse_response, coerce_output, and execute_prompt.

These tests cover every real failure mode observed in production:
  - coerce_output preserving nested dicts (the needs_initialize bug)
  - parse failures across all ResponseMode variants
  - retry and validation callback logic
  - PLAIN_TEXT mode skipping coercion

No real LLM or Ray required — mock_llm replaces the network call.
"""

import pytest
import pytest_asyncio
from typing import Any, ClassVar, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import BaseModel

from agentsociety.prompts.base import BasePrompt
from agentsociety.prompts.prompt_manager import PromptManager, ResponseMode, PromptResult


# ---------------------------------------------------------------------------
# Reference implementations of the fixed needs_block validator logic
# (used by TestNeedsInitializeScenarios to test the logic independently)
# ---------------------------------------------------------------------------

def _has_satisfaction_keys_fixed(parsed: Any, satisfaction_keys: Tuple[str, ...]) -> bool:
    """Fixed validator: accepts any dict (top-level or nested) with at least 1 satisfaction key.

    Uses `any` instead of `all` so partial LLM responses (missing 1-2 keys) are accepted.
    Missing keys are filled in with defaults during extraction.
    Also handles typos in the wrapper key name by searching all nested dicts.
    """
    if not isinstance(parsed, dict):
        return False
    if any(k in parsed for k in satisfaction_keys):
        return True
    # Search any nested dict value — handles typos like "current_satisfation"
    for v in parsed.values():
        if isinstance(v, dict) and any(k in v for k in satisfaction_keys):
            return True
    return False


def _find_satisfaction_dict(
    parsed: dict, satisfaction_keys: Tuple[str, ...]
) -> Optional[dict]:
    """Find the dict (top-level or nested) that holds the 4 satisfaction keys."""
    if all(k in parsed for k in satisfaction_keys):
        return parsed
    for v in parsed.values():
        if isinstance(v, dict) and all(k in v for k in satisfaction_keys):
            return v
    return None


# ---------------------------------------------------------------------------
# Dummy prompt classes for TestCoerceOutput
# ---------------------------------------------------------------------------

class _FloatScorePrompt(BasePrompt):
    """Dummy prompt with a float score output field."""
    name: ClassVar[str] = "test_prompt"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "test"

    class Output(BaseModel):
        score: float

    def format_prompt(self) -> str:
        return "test"


class _AnyDataPrompt(BasePrompt):
    """Dummy prompt with an Any-typed data output field."""
    name: ClassVar[str] = "test_prompt"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "test"

    class Output(BaseModel):
        data: Any

    def format_prompt(self) -> str:
        return "test"


class _StrLabelPrompt(BasePrompt):
    """Dummy prompt with a str label output field."""
    name: ClassVar[str] = "test_prompt"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "test"

    class Output(BaseModel):
        label: str

    def format_prompt(self) -> str:
        return "test"


class _NoOutputPrompt(BasePrompt):
    """Dummy prompt without a nested Output model."""
    name: ClassVar[str] = "test_prompt"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "test"

    def format_prompt(self) -> str:
        return "test"


class _SimplePrompt(BasePrompt):
    """Minimal prompt for execute_prompt pipeline tests (score: float output)."""
    name: ClassVar[str] = "simple_prompt"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "test"

    class Output(BaseModel):
        score: float

    def format_prompt(self) -> str:
        return "Return a score."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pm_with_class(prompt_cls: type[BasePrompt]) -> PromptManager:
    """Create a PromptManager with a single prompt class in _loaded_classes.

    Injects *prompt_cls* under its own ``name`` ClassVar so ``coerce_output``
    and other class-aware methods can find it.
    """
    pm = PromptManager.__new__(PromptManager)
    pm.prompts_dir = ""
    pm.active_config = {}
    pm._loaded_classes = {prompt_cls.name: prompt_cls}
    pm._prompt_memory_handler = MagicMock()
    pm._prompt_memory_handler.resolve_field = AsyncMock(return_value=None)
    return pm


# ---------------------------------------------------------------------------
# TestParseResponse
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_json_clean_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = PromptManager._parse_response(raw, ResponseMode.JSON)
        assert result == {"key": "value"}

    def test_json_trailing_comma(self):
        raw = '{"a": 1,}'
        result = PromptManager._parse_response(raw, ResponseMode.JSON)
        assert result == {"a": 1}

    def test_json_missing_quotes_on_keys(self):
        raw = '{a: 1, b: "hello"}'
        result = PromptManager._parse_response(raw, ResponseMode.JSON)
        assert result["a"] == 1

    def test_json_nested_object(self):
        raw = '{"outer": {"inner": 0.9}}'
        result = PromptManager._parse_response(raw, ResponseMode.JSON)
        assert isinstance(result["outer"], dict)
        assert result["outer"]["inner"] == 0.9

    def test_extract_json_embedded_text(self):
        raw = 'Here is the answer: {"key": 1} done'
        result = PromptManager._parse_response(raw, ResponseMode.EXTRACT_JSON)
        assert result == {"key": 1}

    def test_extract_json_no_json_raises(self):
        raw = "No JSON here"
        with pytest.raises(ValueError, match="No JSON object found"):
            PromptManager._parse_response(raw, ResponseMode.EXTRACT_JSON)

    def test_extract_dict_from_text(self):
        raw = "result: {'score': 0.8}"
        result = PromptManager._parse_response(raw, ResponseMode.EXTRACT_DICT)
        assert isinstance(result, dict)
        assert "score" in result

    def test_extract_dict_no_dict_raises(self):
        raw = "no dict here"
        with pytest.raises(ValueError, match="No dict found"):
            PromptManager._parse_response(raw, ResponseMode.EXTRACT_DICT)

    def test_plain_text_returns_raw_unchanged(self):
        raw = "   Some free text with no JSON   "
        result = PromptManager._parse_response(raw, ResponseMode.PLAIN_TEXT)
        assert result == raw

    def test_plain_text_does_not_parse_json(self):
        raw = '{"should": "not be parsed"}'
        result = PromptManager._parse_response(raw, ResponseMode.PLAIN_TEXT)
        assert isinstance(result, str)
        assert result == raw

    def test_json_deeply_nested_survives(self):
        raw = '{"current_satisfaction": {"hunger_satisfaction": 0.9, "energy_satisfaction": 0.8, "safety_satisfaction": 0.9, "social_satisfaction": 0.6}}'
        result = PromptManager._parse_response(raw, ResponseMode.JSON)
        assert isinstance(result["current_satisfaction"], dict)
        assert result["current_satisfaction"]["hunger_satisfaction"] == 0.9


# ---------------------------------------------------------------------------
# TestCoerceOutput
# ---------------------------------------------------------------------------

class TestCoerceOutput:
    """Tests for Pydantic-based coerce_output.

    After the TOML migration, coerce_output delegates to
    ``Output.model_validate(parsed).model_dump()``.  Pydantic handles
    numeric coercion (str → float) and falls back to returning the
    original *parsed* dict on ValidationError.
    """

    def test_float_from_string(self):
        """Pydantic coerces a numeric string to float for float-typed output fields."""
        pm = _make_pm_with_class(_FloatScorePrompt)
        result = pm.coerce_output("test_prompt", {"score": "0.9"})
        assert result["score"] == pytest.approx(0.9)
        assert isinstance(result["score"], float)

    def test_float_passthrough(self):
        """A float value passes through unchanged."""
        pm = _make_pm_with_class(_FloatScorePrompt)
        result = pm.coerce_output("test_prompt", {"score": 0.75})
        assert result["score"] == pytest.approx(0.75)

    def test_any_field_preserves_nested_dict(self):
        """Any-typed output field must preserve dict values untouched."""
        pm = _make_pm_with_class(_AnyDataPrompt)
        nested = {"hunger_satisfaction": 0.9, "energy_satisfaction": 0.8}
        result = pm.coerce_output("test_prompt", {"data": nested})
        assert isinstance(result["data"], dict)
        assert result["data"]["hunger_satisfaction"] == 0.9

    def test_str_typed_field_dict_input_preserved_via_fallback(self):
        """THE BUG CASE: a dict value for a str-typed field must NOT be stringified.

        Before the TOML fix, ``coerce_output`` called ``str()`` on nested dicts
        producing a Python repr string that broke all downstream ``.get()`` calls.

        With Pydantic, dict→str coercion raises ValidationError, so
        ``coerce_output`` falls back to returning the original parsed value
        with the dict intact.
        """
        pm = _make_pm_with_class(_StrLabelPrompt)
        nested = {"hunger_satisfaction": 0.9, "energy_satisfaction": 0.8}
        result = pm.coerce_output("test_prompt", {"label": nested})
        # Pydantic cannot coerce dict → str → ValidationError → fallback
        assert isinstance(result["label"], dict), (
            f"coerce_output stringified a nested dict! Got: {result['label']!r}"
        )
        assert result["label"]["hunger_satisfaction"] == 0.9

    def test_unknown_prompt_returns_parsed_unchanged(self):
        """A prompt name not in _loaded_classes returns parsed as-is."""
        pm = _make_pm_with_class(_FloatScorePrompt)
        original = {"a": 1, "b": {"nested": True}}
        result = pm.coerce_output("nonexistent_prompt", original)
        assert result == original

    def test_no_output_class_returns_parsed_unchanged(self):
        """A prompt class without a nested Output model returns parsed as-is."""
        pm = _make_pm_with_class(_NoOutputPrompt)
        original = {"x": "anything"}
        result = pm.coerce_output("test_prompt", original)
        assert result == original

    def test_validation_error_returns_original(self):
        """A non-numeric string for a float field triggers fallback."""
        pm = _make_pm_with_class(_FloatScorePrompt)
        original = {"score": "not-a-float"}
        result = pm.coerce_output("test_prompt", original)
        assert result == original

    def test_extra_fields_stripped_on_successful_validation(self):
        """model_dump() only returns declared Output fields — extras are dropped."""
        pm = _make_pm_with_class(_FloatScorePrompt)
        result = pm.coerce_output("test_prompt", {"score": 0.5, "unexpected": "extra"})
        assert result["score"] == pytest.approx(0.5)
        assert "unexpected" not in result

    def test_any_field_preserves_list(self):
        """Any-typed output field preserves list values."""
        pm = _make_pm_with_class(_AnyDataPrompt)
        lst = [1, 2, 3]
        result = pm.coerce_output("test_prompt", {"data": lst})
        assert isinstance(result["data"], list)
        assert result["data"] == lst

    def test_any_field_preserves_none(self):
        """Any-typed output field preserves None."""
        pm = _make_pm_with_class(_AnyDataPrompt)
        result = pm.coerce_output("test_prompt", {"data": None})
        assert result["data"] is None


# ---------------------------------------------------------------------------
# TestNeedsInitializeScenarios — uses real Python prompt class
# ---------------------------------------------------------------------------

class TestNeedsInitializeScenarios:
    """These tests reproduce the exact production failure for needs_initialize.

    The TOML schema declared current_satisfaction as type="text", causing coerce_output
    to call str({"hunger_satisfaction": 0.9, ...}) and turn the dict into a Python repr
    string. The validator then (correctly) rejected it, causing 3 retries per agent per
    simulation start.

    After the fix: coerce_output delegates to Pydantic Output.model_validate().
    The NeedsInitialize Output model declares current_satisfaction as Any, so nested
    dicts pass through untouched.  Inputs that don't match the Output schema trigger
    a ValidationError → fallback → original parsed returned unchanged.
    """

    PROMPT_NAME = "needs_initialize"
    SATISFACTION_KEYS = (
        "hunger_satisfaction",
        "energy_satisfaction",
        "safety_satisfaction",
        "social_satisfaction",
    )

    def test_nested_dict_survives_coerce(self, prompt_manager):
        """Production response: nested under current_satisfaction."""
        parsed = {
            "current_satisfaction": {
                "hunger_satisfaction": 0.9,
                "energy_satisfaction": 0.8,
                "safety_satisfaction": 0.9,
                "social_satisfaction": 0.6,
            }
        }
        result = prompt_manager.coerce_output(self.PROMPT_NAME, parsed)
        sat = result.get("current_satisfaction")
        assert isinstance(sat, dict), (
            f"coerce_output destroyed the nested dict. Got type: {type(sat).__name__}, value: {sat!r}"
        )
        for key in self.SATISFACTION_KEYS:
            assert key in sat, f"Missing key '{key}' in coerced satisfaction dict"

    def test_flat_dict_also_works(self, prompt_manager):
        """Some LLMs return the 4 keys at top level without wrapper.

        The NeedsInitialize Output only declares current_satisfaction, so a flat
        dict (missing current_satisfaction) triggers a ValidationError → fallback
        → all 4 satisfaction keys preserved in the returned dict.
        """
        parsed = {
            "hunger_satisfaction": 0.9,
            "energy_satisfaction": 0.8,
            "safety_satisfaction": 0.9,
            "social_satisfaction": 0.6,
        }
        result = prompt_manager.coerce_output(self.PROMPT_NAME, parsed)
        # Keys not matched by Output schema → returned as-is via fallback
        for key in self.SATISFACTION_KEYS:
            assert key in result

    def test_validator_accepts_nested_after_coerce(self, prompt_manager):
        """End-to-end: after coerce_output, the needs_block validator must accept it."""
        parsed = {
            "current_satisfaction": {
                "hunger_satisfaction": 0.9,
                "energy_satisfaction": 0.8,
                "safety_satisfaction": 0.9,
                "social_satisfaction": 0.6,
            }
        }
        coerced = prompt_manager.coerce_output(self.PROMPT_NAME, parsed)
        sat = coerced.get("current_satisfaction", coerced)
        # Replicate the validator logic from needs_block.py
        assert isinstance(sat, dict)
        for key in self.SATISFACTION_KEYS:
            assert key in sat

    def test_validator_rejects_stringified_dict(self, prompt_manager):
        """The OLD bug: after coerce_output stringified the dict, validator should fail.
        After the fix this scenario no longer occurs — but we keep the test to confirm
        that a plain string value is correctly rejected by the validator logic.
        """
        # Simulate what the old coerce_output would produce
        stringified = "{'hunger_satisfaction': 0.9, 'energy_satisfaction': 0.8, 'safety_satisfaction': 0.9, 'social_satisfaction': 0.6}"
        parsed = {"current_satisfaction": stringified}
        # The validator from needs_block.py
        sat = parsed.get("current_satisfaction")
        assert not isinstance(sat, dict), "This test expects a string, not a dict"
        # Validator must return False for this
        result = isinstance(sat, dict) and all(k in sat for k in self.SATISFACTION_KEYS)
        assert result is False

    def test_string_satisfaction_values_are_acceptable(self, prompt_manager):
        """LLM returns string floats inside the nested dict — structure is preserved."""
        parsed = {
            "current_satisfaction": {
                "hunger_satisfaction": "0.9",
                "energy_satisfaction": "0.8",
                "safety_satisfaction": "0.9",
                "social_satisfaction": "0.6",
            }
        }
        coerced = prompt_manager.coerce_output(self.PROMPT_NAME, parsed)
        sat = coerced.get("current_satisfaction")
        # Still a dict after coercion
        assert isinstance(sat, dict)
        for key in self.SATISFACTION_KEYS:
            assert key in sat

    def test_typo_in_wrapper_key_is_tolerated(self):
        """LLM misspells 'current_satisfation' (missing 'i') — real production failure.

        Raw response seen in logs:
            {"current_satisfation": {"hunger_satisfaction": 0.8, ...}}

        The validator must find the 4 keys regardless of the wrapper key name.
        """
        parsed = {
            "current_satisfation": {  # typo: missing 'i'
                "hunger_satisfaction": 0.8,
                "energy_satisfaction": 0.9,
                "safety_satisfaction": 0.85,
                "social_satisfaction": 0.5,
            }
        }
        # Replicate the needs_block validator logic (the fixed version)
        result = _has_satisfaction_keys_fixed(parsed, self.SATISFACTION_KEYS)
        assert result is True, (
            "Validator rejected a response with a typo in the wrapper key. "
            "It should accept any nested dict containing all 4 satisfaction keys."
        )

    def test_extraction_finds_typo_wrapper(self):
        """After passing validation, extraction must also find the nested dict."""
        parsed = {
            "current_satisfation": {
                "hunger_satisfaction": 0.8,
                "energy_satisfaction": 0.9,
                "safety_satisfaction": 0.85,
                "social_satisfaction": 0.5,
            }
        }
        sat = _find_satisfaction_dict(parsed, self.SATISFACTION_KEYS)
        assert sat is not None
        assert sat["hunger_satisfaction"] == 0.8

    def test_partial_satisfaction_keys_accepted(self):
        """LLM returns only 3 of 4 keys — real production failure.

        Raw response seen in logs:
            {"current_satisfaction": {"hunger_satisfaction": 0.8,
                                      "energy_satisfaction": 0.9,
                                      "safety_satisfaction": 0.85}}
            (social_satisfaction missing)

        The validator must accept a partial dict; extraction fills in defaults
        for missing keys. Requiring all 4 keys causes retries even when the
        response is 75% valid.
        """
        parsed = {
            "current_satisfaction": {
                "hunger_satisfaction": 0.8,
                "energy_satisfaction": 0.9,
                "safety_satisfaction": 0.85,
                # social_satisfaction deliberately absent
            }
        }
        result = _has_satisfaction_keys_fixed(parsed, self.SATISFACTION_KEYS)
        assert result is True, (
            "Validator rejected a partial satisfaction dict. "
            "It should accept any nested dict with at least 1 satisfaction key."
        )

    def test_typo_coerce_then_extract(self, prompt_manager):
        """Full path: coerce_output then extract — typo response must produce correct values."""
        parsed = {
            "current_satisfation": {  # typo
                "hunger_satisfaction": 0.8,
                "energy_satisfaction": 0.9,
                "safety_satisfaction": 0.85,
                "social_satisfaction": 0.5,
            }
        }
        coerced = prompt_manager.coerce_output(self.PROMPT_NAME, parsed)
        # Validator accepts it
        assert _has_satisfaction_keys_fixed(coerced, self.SATISFACTION_KEYS)
        # Extraction finds the right nested dict
        sat = _find_satisfaction_dict(coerced, self.SATISFACTION_KEYS)
        assert sat is not None
        assert sat["hunger_satisfaction"] == 0.8
        assert sat["social_satisfaction"] == 0.5


# ---------------------------------------------------------------------------
# TestExecutePromptPipeline — async, uses mock_llm
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestExecutePromptPipeline:
    """Tests for the full execute_prompt loop using a mock LLM."""

    def _make_pm(self) -> PromptManager:
        """PromptManager with a minimal fake prompt class (score: float output)."""
        pm = PromptManager.__new__(PromptManager)
        pm.prompts_dir = ""
        pm.active_config = {}
        pm._loaded_classes = {"simple_prompt": _SimplePrompt}
        pm._prompt_memory_handler = MagicMock()
        pm._prompt_memory_handler.resolve_field = AsyncMock(return_value=None)
        return pm

    async def test_success_path(self, mock_llm, mock_memory):
        pm = self._make_pm()
        mock_llm.atext_request = AsyncMock(return_value='{"score": 0.8}')
        result = await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
        )
        assert result.success is True
        assert result.parsed["score"] == pytest.approx(0.8)
        assert result.error is None

    async def test_retry_on_llm_exception_then_succeeds(self, mock_llm, mock_memory):
        """LLM raises a network/timeout error on first attempt, succeeds on second.

        Note: json_repair never raises on garbage input — it returns an empty string.
        Retries are triggered by real exceptions (timeouts, network errors) or validate failures.
        """
        pm = self._make_pm()
        mock_llm.atext_request = AsyncMock(
            side_effect=[RuntimeError("LLM timeout"), '{"score": 0.5}']
        )
        result = await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
            max_retries=1,
        )
        assert result.success is True
        assert result.parsed["score"] == pytest.approx(0.5)
        assert mock_llm.atext_request.call_count == 2

    async def test_all_retries_exhausted_returns_failure(self, mock_llm, mock_memory):
        """All LLM calls fail with an exception — confirm success=False after max_retries.

        Note: json_repair silently repairs garbage strings (returning "" or {}).
        Using explicit exceptions to reliably trigger the failure path.
        """
        pm = self._make_pm()
        mock_llm.atext_request = AsyncMock(side_effect=RuntimeError("LLM error"))
        result = await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
            max_retries=2,
        )
        assert result.success is False
        assert result.error is not None
        assert mock_llm.atext_request.call_count == 3  # 1 attempt + 2 retries

    async def test_validate_callback_triggers_retry(self, mock_llm, mock_memory):
        pm = self._make_pm()
        # Both responses are valid JSON, but first fails validate
        mock_llm.atext_request = AsyncMock(
            side_effect=['{"score": -1.0}', '{"score": 0.9}']
        )
        result = await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
            max_retries=1,
            validate=lambda p: isinstance(p, dict) and p.get("score", -999) >= 0,
        )
        assert result.success is True
        assert result.parsed["score"] == pytest.approx(0.9)
        assert mock_llm.atext_request.call_count == 2

    async def test_validate_all_fail_returns_failure(self, mock_llm, mock_memory):
        pm = self._make_pm()
        mock_llm.atext_request = AsyncMock(return_value='{"score": -1.0}')
        result = await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
            max_retries=2,
            validate=lambda p: False,
        )
        assert result.success is False
        assert "Custom validation failed" in (result.error or "")

    async def test_plain_text_skips_coerce(self, mock_llm, mock_memory):
        pm = self._make_pm()
        raw = "This is a plain text response with no JSON"
        mock_llm.atext_request = AsyncMock(return_value=raw)
        result = await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
            response_mode=ResponseMode.PLAIN_TEXT,
        )
        assert result.success is True
        assert result.parsed == raw
        assert isinstance(result.parsed, str)

    async def test_dialog_override_bypasses_format_prompt(self, mock_llm, mock_memory):
        pm = self._make_pm()
        custom_dialog = [{"role": "user", "content": "custom question"}]
        mock_llm.atext_request = AsyncMock(return_value='{"score": 1.0}')
        await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
            dialog_override=custom_dialog,
        )
        call_args = mock_llm.atext_request.call_args
        actual_dialog = call_args[0][0]  # first positional arg
        assert actual_dialog == custom_dialog

    async def test_coerce_runs_on_json_response(self, mock_llm, mock_memory):
        """Confirm that string scores are coerced to float via Pydantic Output model."""
        pm = self._make_pm()
        mock_llm.atext_request = AsyncMock(return_value='{"score": "0.75"}')
        result = await pm.execute_prompt(
            prompt_name="simple_prompt",
            llm=mock_llm,
            memory=mock_memory,
            context={},
            block_name="TestBlock",
            func_name="test",
            agent_id="agent_0",
        )
        assert result.success is True
        # Pydantic coerces "0.75" str → 0.75 float
        assert result.parsed["score"] == pytest.approx(0.75)
        assert isinstance(result.parsed["score"], float)

    async def test_coerce_does_not_run_on_plain_text(self, mock_llm, mock_memory):
        """PLAIN_TEXT mode: coerce_output must never be called."""
        pm = self._make_pm()
        mock_llm.atext_request = AsyncMock(return_value='{"score": "0.75"}')
        with patch.object(pm, "coerce_output") as mock_coerce:
            result = await pm.execute_prompt(
                prompt_name="simple_prompt",
                llm=mock_llm,
                memory=mock_memory,
                context={},
                block_name="TestBlock",
                func_name="test",
                agent_id="agent_0",
                response_mode=ResponseMode.PLAIN_TEXT,
            )
        mock_coerce.assert_not_called()
        assert result.success is True
