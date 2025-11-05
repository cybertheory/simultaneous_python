"""JSON utilities."""

import json
from typing import Any


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON, returning default on error."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize to JSON, returning default on error."""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return default








