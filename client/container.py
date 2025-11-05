"""Container automation clients for use in agent code.

This module provides container automation clients (like E2B) that can be used
inside agent code to interact with sandboxes. These are different from providers
(like E2B) which provide the infrastructure/runtime.
"""

from typing import Any, Optional
import os
from simultaneous.runtime.base import RuntimeKind
from simultaneous.providers.base import ProviderAdapter
from simultaneous.providers.router import get_adapter


class ContainerClient:
    """
    Container automation client for use in agent code.
    
    This client wraps container automation SDKs (like E2B) and can be used inside
    agent code to interact with sandboxes. It connects to a session URL provided by
    the provider (e.g., E2B) and exposes the E2B SDK underneath.
    
    Example:
        ```python
        from simultaneous import SimClient, Sandbox, ContainerClient
        
        client = SimClient()
        
        @client.agent(name="code-exec", runtime=Sandbox(provider="e2b"))
        async def code_exec(code: str):
            # ContainerClient is initialized with the session URL from the provider
            container = ContainerClient(session_url="mcp://...")
            await container.init()
            # Access the underlying E2B SDK
            sandbox = container.sandbox
            result = await sandbox.run("python script.py")
            # ... automation code
        ```
    
    Note:
        ContainerClient is a container automation client wrapper, not a provider. The provider
        (e.g., E2B via Simultaneous API) provides the session URL that
        ContainerClient connects to.
    """
    
    def __init__(
        self,
        *,
        e2b_sandbox_id: Optional[str] = None,
        session_url: Optional[str] = None,
        # Provider/adapter configuration (optional; enables self-launch)
        adapter: ProviderAdapter | None = None,
        provider: str | None = None,
        provider_config: dict | None = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize ContainerClient.
        
        Args:
            e2b_sandbox_id: E2B sandbox ID (preferred)
            session_url: Container session URL (MCP endpoint from provider)
            api_key: E2B API key (optional, defaults to E2B_API_KEY env var)
            adapter: Provider adapter instance (optional)
            provider: Provider name (e.g., "e2b") (optional)
            provider_config: Provider configuration (optional)
            **kwargs: Additional options
        """
        self.e2b_sandbox_id = e2b_sandbox_id
        self.session_url = session_url
        self.api_key = api_key or os.getenv("E2B_API_KEY")
        self._options = kwargs
        # provider/adapter
        self._adapter = adapter
        self._provider = provider
        self._provider_config = provider_config or {}
        
        # Try to import e2b if available
        try:
            from e2b import Sandbox
            self._Sandbox = Sandbox
            self._has_e2b = True
            self._sandbox_instance = None
        except ImportError:
            self._Sandbox = None
            self._has_e2b = False
            self._sandbox_instance = None
    
    def __repr__(self) -> str:
        """String representation."""
        session_display = f"session_url={self.session_url[:30]}..." if self.session_url else "session_url=None"
        return f"ContainerClient({session_display})"
    
    def is_available(self) -> bool:
        """Check if E2B SDK is installed."""
        return self._has_e2b
    
    async def init(self) -> None:
        """
        Initialize the container client and connect to the sandbox.
        
        This must be called before accessing the sandbox object.
        """
        if not self._has_e2b:
            raise ImportError(
                "Container automation SDK (E2B) is not installed. Install it with: pip install e2b"
            )
        
        # Determine sandbox ID to use; if missing, launch via adapter/provider
        sandbox_id = self.e2b_sandbox_id
        if not sandbox_id and self.session_url:
            # Try to extract sandbox ID from session URL if possible
            # E2B MCP URLs may contain sandbox ID
            pass
        
        if not sandbox_id:
            # Attempt to launch a new provider session if adapter/provider provided
            if self._adapter is None and self._provider:
                self._adapter = get_adapter(
                    runtime_kind=RuntimeKind.SANDBOX,
                    provider=self._provider,
                    config={**self._provider_config},
                )
            if self._adapter is not None:
                # Start with any provider config given by user
                launch_opts: dict[str, Any] = {**(self._provider_config or {})}
                # Ensure template default
                launch_opts.setdefault("template", os.getenv("E2B_TEMPLATE", "base"))

                result = await self._adapter.launch(options=launch_opts)
                sandbox_id = result.get("session_id")
                # Capture provider session URL when available for direct connection
                if result.get("session_url"):
                    self.session_url = result.get("session_url")
                # Persist for external access
                self.e2b_sandbox_id = sandbox_id
        
        if not sandbox_id:
            raise ValueError(
                "Either e2b_sandbox_id or a session_url with extractable sandbox ID is required"
            )
        
        # Set API key if provided
        if self.api_key and not os.getenv("E2B_API_KEY"):
            os.environ["E2B_API_KEY"] = self.api_key
        
        # Reconnect to existing sandbox using E2B SDK
        # E2B SDK: Sandbox.reconnect(sandbox_id=...) returns a Sandbox instance
        import asyncio
        def reconnect_sandbox():
            """Reconnect to sandbox."""
            if hasattr(self._Sandbox, "reconnect"):
                return self._Sandbox.reconnect(sandbox_id=sandbox_id)
            else:
                raise RuntimeError(
                    "E2B SDK reconnect method not available. "
                    "The sandbox instance should be stored when creating it."
                )
        
        self._sandbox_instance = await asyncio.to_thread(reconnect_sandbox)
    
    @property
    def sandbox(self):
        """
        Get the E2B sandbox object.
        
        This exposes the underlying E2B SDK Sandbox instance.
        
        Note: You must call init() first before accessing this property.
        """
        if not self._sandbox_instance:
            raise RuntimeError(
                "ContainerClient not initialized. Call await container.init() first."
            )
        return self._sandbox_instance
    
    async def close(self) -> None:
        """Close the container session."""
        if self._sandbox_instance:
            import asyncio
            await asyncio.to_thread(self._sandbox_instance.close)
            self._sandbox_instance = None

