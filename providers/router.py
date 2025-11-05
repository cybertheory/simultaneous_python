"""Router for selecting provider adapters based on runtime and provider."""

from typing import Any

from simultaneous.providers.base import ProviderAdapter, ProviderError
from simultaneous.providers.browserbase import BrowserbaseAdapter
from simultaneous.runtime.base import RuntimeKind


def get_adapter(
    runtime_kind: RuntimeKind,
    provider: str,
    config: dict[str, Any],
) -> ProviderAdapter:
    """
    Get the appropriate provider adapter.
    
    Args:
        runtime_kind: Type of runtime (browser, desktop, sandbox)
        provider: Provider name ("auto", "browserbase", etc.)
        config: Provider configuration (API keys, project IDs, etc.)
        
    Returns:
        Provider adapter instance
        
    Raises:
        ProviderError: If the combination is not supported
        
    Note:
        BrowserClient is a browser automation client wrapper, not a provider.
        Use Browserbase (or other providers) as the infrastructure provider,
        and use BrowserClient inside your agent code for browser automation.
    """
    # Normalize provider
    if provider == "auto":
        # For MVP, default to browserbase for browser runtime
        if runtime_kind == RuntimeKind.BROWSER:
            provider = "browserbase"
        else:
            raise ProviderError(
                f"No default provider for runtime kind '{runtime_kind.value}'"
            )
    
    # Map (runtime_kind, provider) to adapter
    if runtime_kind == RuntimeKind.BROWSER:
        if provider == "browserbase":
            return BrowserbaseAdapter(**config)
        else:
            raise ProviderError(
                f"Unsupported provider '{provider}' for runtime '{runtime_kind.value}'. "
                f"Supported providers: browserbase"
            )
    else:
        raise ProviderError(
            f"Runtime kind '{runtime_kind.value}' not yet supported"
        )







