"""
Simultaneous SDK - Run agents across multiple providers.

Public API:
    - SimClient: Main client for managing agents and runs
    - Browser, Desktop, Sandbox: Runtime abstractions
    - BrowserClient: Browser automation client for use in agent code
    - run: Convenience function for simple runs
"""

from simultaneous.client.sim_client import SimClient
from simultaneous.client.browser import BrowserClient
from simultaneous.runtime.browser import Browser
from simultaneous.runtime.base import Runtime, RuntimeKind
from simultaneous.browsers import Browsers, BrowserBase
from simultaneous.client.llms import (
    Models,
    GPT4o,
    OPENAI_COMPUTER_USE_MINI,
    OPENAI_COMPUTER_USE,
)

__all__ = [
    "SimClient",
    "Browser",
    "BrowserClient",
    "Runtime",
    "RuntimeKind",
    # typed enums / aliases
    "Browsers",
    "BrowserBase",
    "Models",
    "GPT4o",
    "OPENAI_COMPUTER_USE_MINI",
    "OPENAI_COMPUTER_USE",
]

__version__ = "0.1.0"







