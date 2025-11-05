"""Typed model names for autocomplete-friendly usage."""

from enum import Enum


class Models(str, Enum):
    GPT4O = "gpt-4o"
    CLAUDE_3_5 = "claude-3.5"
    # OpenAI Computer Use-capable Omni models (supported by LiteLLM)
    O4_MINI = "o4-mini"
    O4 = "o4"


# Backwards-compatible alias
GPT4o = Models.GPT4O

# Convenience aliases for Computer Use
OPENAI_COMPUTER_USE_MINI = Models.O4_MINI
OPENAI_COMPUTER_USE = Models.O4



