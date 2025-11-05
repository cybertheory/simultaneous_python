"""Browser runtime configuration."""

from dataclasses import dataclass
from typing import Any

from simultaneous.runtime.base import Runtime, RuntimeKind


@dataclass
class Browser(Runtime):
    """
    Browser runtime configuration.
    
    Args:
        provider: Provider name ("auto" or "browserbase")
        region: Region for the provider ("auto", "sfo", etc.)
        project: Project identifier for the provider
        **kwargs: Additional provider-specific options
        
    Note:
        BrowserClient is a browser automation client wrapper, not a provider.
        Use Browserbase as the provider (infrastructure), and use BrowserClient
        inside your agent code for browser automation.
    """
    
    provider: str = "auto"
    region: str = "auto"
    project: str | None = None
    options: dict[str, Any] | None = None
    
    def __post_init__(self) -> None:
        """Initialize runtime kind and normalize options."""
        self.kind = RuntimeKind.BROWSER
        if self.options is None:
            self.options = {}
        if self.region != "auto":
            self.options["region"] = self.region
        if self.project:
            self.options["project"] = self.project
    
    def to_dict(self) -> dict[str, Any]:
        """Convert browser runtime to dictionary."""
        return {
            "kind": self.kind.value,
            "provider": self.provider,
            "options": self.options or {},
        }







