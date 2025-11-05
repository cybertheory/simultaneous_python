"""Base runtime protocol and types."""

from enum import Enum
from typing import Any, Protocol


class RuntimeKind(str, Enum):
    """Types of runtime environments."""
    
    BROWSER = "browser"
    DESKTOP = "desktop"
    SANDBOX = "sandbox"


class Runtime(Protocol):
    """Protocol for runtime configurations."""
    
    kind: RuntimeKind
    provider: str
    options: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert runtime to dictionary."""
        ...







