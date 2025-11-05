"""Desktop runtime configuration (placeholder)."""

from dataclasses import dataclass
from typing import Any

from simultaneous.runtime.base import Runtime, RuntimeKind


@dataclass
class Desktop(Runtime):
    """Desktop runtime configuration (not yet implemented)."""
    
    provider: str = "auto"
    options: dict[str, Any] | None = None
    
    def __post_init__(self) -> None:
        """Initialize runtime kind."""
        self.kind = RuntimeKind.DESKTOP
        if self.options is None:
            self.options = {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert desktop runtime to dictionary."""
        return {
            "kind": self.kind.value,
            "provider": self.provider,
            "options": self.options or {},
        }








