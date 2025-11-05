"""Typed browser provider identifiers for autocomplete-friendly usage."""

from enum import Enum


class Browsers(str, Enum):
    BROWSERBASE = "browserbase"


# Backwards-compatible alias
BrowserBase = Browsers.BROWSERBASE


