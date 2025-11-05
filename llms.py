"""Typed model names for autocomplete-friendly usage."""

from enum import Enum


class Models(str, Enum):
    GPT4O = "gpt-4o"
    CLAUDE_3_5 = "claude-3.5"


# Backwards-compatible alias
GPT4o = Models.GPT4O


