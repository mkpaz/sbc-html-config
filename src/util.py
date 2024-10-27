from typing import Any


def is_dict(val):
    return isinstance(val, dict)


def is_list(val):
    return isinstance(val, list)


def is_tuple(val):
    return isinstance(val, tuple)


def is_string(val):
    return isinstance(val, str)


def is_string_list(val):
    return is_list(val) and all(isinstance(item, str) for item in val)


def rpad(s: str, size: int) -> str:
    return s if size == 0 else s.rjust(len(s) + size)


def ensure_list(t: Any) -> list[Any]:
    if not t:
        return []
    return t if isinstance(t, list) else [t]


def ensure_dict(t: Any) -> dict[str, Any]:
    if not t:
        return {}
    return t if isinstance(t, dict) else {}


def contains_not_empty(d: dict[str, Any], key: str) -> bool:
    val = d.get(key)

    if val is None:
        return False
    elif isinstance(val, str):
        return val != ""

    return True
