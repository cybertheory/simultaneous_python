"""Run management: create, wait, cancel runs."""

import asyncio
from typing import Any, Callable

from simultaneous.providers.base import ProviderAdapter, ProviderError
from simultaneous.runtime.base import Runtime, RuntimeKind
from simultaneous.runtime.browser import Browser
from simultaneous.utils.ids import generate_run_id


class RunManager:
    """Manages runs across providers."""
    
    def __init__(self, client: "SimClient"):
        """Initialize run manager."""
        self.client = client
        self._runs: dict[str, dict[str, Any]] = {}
    
    async def create(
        self,
        agent_ref: str | Callable,
        params: dict[str, Any] | None = None,
        runtime: Runtime | None = None,
        parallel: int = 1,
    ) -> str:
        """
        Create a new run.
        
        Args:
            agent_ref: Agent name or callable
            params: Input parameters
            runtime: Runtime configuration (uses default if None)
            parallel: Number of parallel shards
            
        Returns:
            Run ID
        """
        # Get agent info
        if callable(agent_ref):
            # TODO: Extract agent metadata from decorated function
            agent_name = agent_ref.__name__
        else:
            agent_name = agent_ref
        
        # Use default runtime if not provided
        if runtime is None:
            runtime = self.client.default_runtime or Browser()
        
        # Generate run ID
        run_id = generate_run_id()
        
        # Get adapter
        from simultaneous.providers.router import get_adapter
        
        # Extract provider config from runtime
        runtime_dict = runtime.to_dict() if hasattr(runtime, "to_dict") else {}
        provider_config = runtime_dict.get("options", {})
        
        # Extract project_id from runtime (it's stored in options or as project attribute)
        if not provider_config.get("project_id") and not provider_config.get("project"):
            # Try to get from runtime project attribute
            if hasattr(runtime, "project") and runtime.project:
                provider_config["project_id"] = runtime.project
        
        # Ensure project_id is in config for BrowserbaseAdapter
        if "project" in provider_config and "project_id" not in provider_config:
            provider_config["project_id"] = provider_config["project"]
        
        adapter = get_adapter(
            runtime_kind=runtime.kind,
            provider=runtime.provider,
            config=provider_config,
        )
        
        # Pack agent (if needed)
        # TODO: Implement agent packing and upload
        
        # Create parallel shards
        provider_sessions = []
        for _ in range(parallel):
            try:
                session_info = await adapter.launch(
                    bundle_url=None,  # TODO: Upload bundle and get URL
                    env=params,
                    options={},
                )
                # Handle both dict response (new) and string response (legacy)
                if isinstance(session_info, dict):
                    provider_sessions.append(session_info)
                else:
                    # Legacy: string session ID
                    provider_sessions.append({
                        "session_id": session_info,
                        "session_url": None,
                    })
            except ProviderError as e:
                # TODO: Handle partial failures
                raise
        
        # Extract session IDs and URLs
        provider_run_ids = [s.get("session_id") or s for s in provider_sessions]
        session_urls = [s.get("session_url") for s in provider_sessions if isinstance(s, dict)]
        
        # Store run info
        self._runs[run_id] = {
            "agent_name": agent_name,
            "runtime": runtime,
            "provider_run_ids": provider_run_ids,
            "provider_sessions": provider_sessions,
            "session_urls": session_urls,
            "adapter": adapter,
            "params": params or {},
            "parallel": parallel,
        }
        
        return run_id
    
    async def wait(
        self,
        run_id: str,
        poll_interval: float = 1.0,
    ) -> dict[str, Any]:
        """
        Wait for a run to complete.
        
        Args:
            run_id: Run ID
            poll_interval: Polling interval in seconds
            
        Returns:
            Final status dictionary
        """
        if run_id not in self._runs:
            raise ValueError(f"Run not found: {run_id}")
        
        run_info = self._runs[run_id]
        adapter = run_info["adapter"]
        provider_run_ids = run_info["provider_run_ids"]
        
        # Poll until all shards are terminal
        while True:
            all_terminal = True
            states = []
            
            for provider_run_id in provider_run_ids:
                status = await adapter.status(provider_run_id)
                state = status.get("state", "UNKNOWN")
                states.append(state)
                
                if state not in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                    all_terminal = False
            
            if all_terminal:
                # Aggregate results
                results = []
                for provider_run_id in provider_run_ids:
                    status = await adapter.status(provider_run_id)
                    results.append(status)
                
                return {
                    "run_id": run_id,
                    "state": self._aggregate_state(states),
                    "results": results,
                }
            
            await asyncio.sleep(poll_interval)
    
    async def cancel(self, run_id: str) -> None:
        """
        Cancel a run.
        
        Args:
            run_id: Run ID
        """
        if run_id not in self._runs:
            raise ValueError(f"Run not found: {run_id}")
        
        run_info = self._runs[run_id]
        adapter = run_info["adapter"]
        provider_run_ids = run_info["provider_run_ids"]
        
        # Cancel all shards
        for provider_run_id in provider_run_ids:
            try:
                await adapter.cancel(provider_run_id)
            except ProviderError:
                # Continue on errors
                pass
    
    def _aggregate_state(self, states: list[str]) -> str:
        """Aggregate multiple states into a single state."""
        if all(s == "SUCCEEDED" for s in states):
            return "SUCCEEDED"
        elif any(s == "FAILED" for s in states):
            return "FAILED"
        elif any(s == "CANCELLED" for s in states):
            return "CANCELLED"
        else:
            return states[0] if states else "UNKNOWN"

