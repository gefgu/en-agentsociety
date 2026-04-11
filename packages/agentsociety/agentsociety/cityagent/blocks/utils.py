import re

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
