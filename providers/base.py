"""Base provider adapter protocol."""

from typing import Any, Protocol


class ProviderError(RuntimeError):
    """Base exception for provider-related errors."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        retryable: bool | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ProviderAdapter(Protocol):
    """Protocol for provider adapters."""
    
    async def launch(
        self,
        *,
        bundle_url: str | None = None,
        env: dict[str, str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Launch a new run on the provider.
        
        Args:
            bundle_url: URL to the agent bundle (tar.gz)
            env: Environment variables to set
            options: Provider-specific options
            
        Returns:
            Dictionary with session_id and session_url (connectUrl for browser connection)
        """
        ...
    
    async def status(self, provider_run_id: str) -> dict[str, Any]:
        """
        Get the status of a run.
        
        Args:
            provider_run_id: Provider-specific run ID
            
        Returns:
            Status dictionary with keys: state, startedAt, finishedAt, exitCode, meta
        """
        ...
    
    async def logs(
        self,
        provider_run_id: str,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """
        Get logs from a run.
        
        Args:
            provider_run_id: Provider-specific run ID
            cursor: Cursor for pagination (optional)
            
        Returns:
            Logs dictionary with keys: entries, next_cursor
        """
        ...
    
    async def cancel(self, provider_run_id: str) -> None:
        """
        Cancel a running execution.
        
        Args:
            provider_run_id: Provider-specific run ID
        """
        ...







