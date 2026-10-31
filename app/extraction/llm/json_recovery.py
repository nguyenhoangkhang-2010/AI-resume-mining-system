import json
from typing import Any, Dict, List, Optional


def recover_array_objects(
    text: str,
    array_key: Optional[str] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Recovers the complete objects from a JSON array whose text was cut
    short (an LLM stops at its token limit in the middle of a list).

    The array is the one under `array_key` (for example {"experience": [...])
    or, without a key, the first array in the text. Every object that is
    closed before the cut is returned; an object that was cut in the middle
    is dropped. Returns None when nothing complete could be recovered.
    """

    if array_key:
        key_index = text.find(f'"{array_key}"')

        if key_index < 0:
            return None

        array_start = text.find("[", key_index)
    else:
        array_start = text.find("[")

    if array_start < 0:
        return None

    objects: List[Dict[str, Any]] = []

    bracket_depth = 0
    brace_depth = 0
    object_start: Optional[int] = None

    in_string = False
    escaped = False

    for index in range(array_start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True

        elif char == "[":
            bracket_depth += 1

        elif char == "]":
            bracket_depth -= 1

            if bracket_depth == 0:
                break

        elif char == "{":
            if brace_depth == 0 and bracket_depth == 1:
                object_start = index

            brace_depth += 1

        elif char == "}":
            brace_depth -= 1

            if brace_depth == 0 and object_start is not None:
                try:
                    parsed = json.loads(text[object_start:index + 1])
                except json.JSONDecodeError:
                    parsed = None

                if isinstance(parsed, dict):
                    objects.append(parsed)

                object_start = None

    return objects or None
