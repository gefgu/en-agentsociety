import math
import numbers
import re
from collections.abc import Callable
from typing import Optional

import json_repair


def prettify_document(document: str) -> str:
    # Remove sequences of whitespace characters (including newlines)
    cleaned = re.sub(r"\s+", " ", document).strip()
    return cleaned


def extract_dict_from_string(input_string):
    """
    Extract dictionaries from the input string. Supports multi-line dictionaries and nested dictionaries.

    Uses json_repair.loads instead of ast.literal_eval so that JSON-style values
    (null, true, false, double-quoted strings) are handled correctly.
    """
    # Use regular expression to find all possible dictionary parts, allowing multi-line dictionaries
    dict_pattern = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"  # Regular expression to match dictionaries, supports nesting
    matches = re.findall(
        dict_pattern, input_string, re.DOTALL
    )  # re.DOTALL allows matching newline characters

    dicts = []

    for match in matches:
        try:
            parsed_dict = json_repair.loads(match)
            if isinstance(parsed_dict, dict):
                dicts.append(parsed_dict)
        except Exception:
            pass

    return dicts


def clean_json_response(response: str) -> str:
    """remove the special characters in the response"""
    response = response.replace("```json", "").replace("```", "")
    return response.strip()


def coerce_minutes(
    value,
    default: int | Callable[[], int],
    *,
    minimum: int = 0,
    maximum: Optional[int] = None,
) -> int:
    """Return a sane integer minute value from model output.

    LLMs sometimes return values such as "unknown", "30 minutes", or "1.5 hours"
    even when the output schema asks for an integer. This helper keeps those
    responses from crashing the simulation while still accepting useful numbers.
    """

    def resolve_default() -> int:
        resolved = default() if callable(default) else default
        return int(resolved)

    parsed: Optional[float]
    if value is None or isinstance(value, bool):
        parsed = None
    elif isinstance(value, numbers.Real):
        parsed = float(value)
    elif isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"", "unknown", "none", "null", "n/a", "na", "dont know", "don't know"}:
            parsed = None
        else:
            try:
                parsed = float(stripped)
            except ValueError:
                match = re.search(r"[-+]?\d+(?:\.\d+)?", stripped)
                parsed = float(match.group(0)) if match else None
                if parsed is not None and re.search(r"\b(hours?|hrs?|h)\b", stripped):
                    parsed *= 60
    else:
        parsed = None

    if parsed is None or not math.isfinite(parsed):
        minutes = resolve_default()
    else:
        minutes = int(round(parsed))

    if minutes < minimum:
        minutes = minimum
    if maximum is not None and minutes > maximum:
        minutes = maximum
    return minutes
