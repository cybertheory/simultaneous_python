"""E2B provider adapter via Simultaneous API."""

import asyncio
from typing import Any

import httpx

from simultaneous.providers.base import ProviderAdapter, ProviderError
from simultaneous.utils.env import get_env, redact_sensitive


class E2BAdapter:
    """
    Adapter for E2B provider via Simultaneous API.
    
    This adapter calls the Simultaneous API to create E2B sandboxes,
    which then returns session URLs that can be used with container clients like ContainerClient.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        project_id: str | None = None,
        template: str | None = None,
        simultaneous_api_url: str | None = None,
        simultaneous_api_key: str | None = None,
    ):
        """
        Initialize E2B adapter.
        
        Args:
            api_key: Simultaneous API key (defaults to SIMULTANEOUS_API_KEY env var)
            project_id: Simultaneous project ID (UUID)
            template: E2B template ID (defaults to "base")
            simultaneous_api_url: Simultaneous API base URL (defaults to https://api.simultaneous.live)
            simultaneous_api_key: Simultaneous API key (alternative to api_key)
        """
        self.simultaneous_api_key = simultaneous_api_key or api_key or get_env("SIMULTANEOUS_API_KEY")
        self.project_id = project_id  # Simultaneous project ID (UUID)
        self.template = template or get_env("E2B_TEMPLATE", "base")
        
        # Simultaneous API base URL
        from simultaneous.client.sim_client import SimClient
        self.simultaneous_api_url = (simultaneous_api_url or SimClient.API_BASE_URL).rstrip("/")
        
        if not self.project_id:
            raise ProviderError(
                "Project ID required. Pass project_id or set SIMULTANEOUS_PROJECT_ID env var."
            )
        
        self._client: httpx.AsyncClient | None = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for Simultaneous API."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.simultaneous_api_key:
                headers["Authorization"] = f"Bearer {self.simultaneous_api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.simultaneous_api_url,
                timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0),
                headers=headers,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def launch(
        self,
        *,
        bundle_url: str | None = None,
        env: dict[str, str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Launch a new sandbox via Simultaneous API (which creates an E2B sandbox).
        
        Args:
            bundle_url: URL to agent bundle
            env: Environment variables
            options: Additional options (template, metadata, etc.)
            
        Returns:
            Dictionary with session_id and session_url (sessionUrl)
        """
        payload: dict[str, Any] = {
            "template": self.template,
        }
        
        if env:
            payload["envVars"] = env
        
        if bundle_url:
            payload["bundleUrl"] = bundle_url
        
        if options:
            # Extract E2B-specific options
            if "template" in options:
                payload["template"] = options["template"]
            if "metadata" in options:
                payload["metadata"] = options["metadata"]
            if "envVars" in options:
                # Merge with top-level env if provided
                existing_env = payload.get("envVars", {})
                existing_env.update(options["envVars"])
                payload["envVars"] = existing_env
        
        try:
            # Call Simultaneous API to create an E2B sandbox
            response = await self.client.post(
                f"/v1/e2b/projects/{self.project_id}/sandboxes",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract provider session info from Simultaneous API response
            session_id = (
                data.get("providerSandboxId")
                or data.get("provider_sandbox_id")
                or data.get("sandboxId")
                or data.get("id")
            )
            session_url = data.get("sessionUrl") or data.get("session_url")
            
            if not session_id:
                raise ProviderError("Simultaneous API response missing sandbox ID")
            
            if not session_url:
                # Try to get URL from sandbox details endpoint
                sandbox_detail = await self.client.get(
                    f"/v1/e2b/projects/{self.project_id}/sandboxes/{session_id}"
                )
                if sandbox_detail.status_code == 200:
                    detail_data = sandbox_detail.json()
                    session_url = detail_data.get("sessionUrl") or detail_data.get("session_url")
            
            return {
                "session_id": str(session_id),
                "session_url": session_url,  # MCP URL for container connection
            }
        
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            error_msg = redact_sensitive(str(e))
            
            if status == 401:
                raise ProviderError(
                    "Simultaneous API authentication failed. Check your API key.",
                    code="auth_failed",
                    retryable=False,
                ) from e
            elif status == 403:
                raise ProviderError(
                    "Simultaneous API access forbidden. Check project permissions.",
                    code="forbidden",
                    retryable=False,
                ) from e
            elif status == 429:
                raise ProviderError(
                    "Simultaneous API rate limit exceeded.",
                    code="rate_limit",
                    retryable=True,
                ) from e
            elif status >= 500:
                raise ProviderError(
                    f"Simultaneous API server error: {error_msg}",
                    code="server_error",
                    retryable=True,
                ) from e
            else:
                raise ProviderError(
                    f"Simultaneous API request failed: {error_msg}",
                    code="request_failed",
                    retryable=False,
                ) from e
        
        except httpx.RequestError as e:
            error_msg = redact_sensitive(str(e))
            raise ProviderError(
                f"Simultaneous API connection error: {error_msg}",
                code="connection_error",
                retryable=True,
            ) from e
    
    async def status(self, provider_run_id: str) -> dict[str, Any]:
        """
        Get status of an E2B sandbox via Simultaneous API.
        
        Args:
            provider_run_id: Sandbox ID
            
        Returns:
            Status dict with: state, startedAt, finishedAt, exitCode, meta
        """
        try:
            # Call Simultaneous API to get sandbox status
            response = await self.client.get(
                f"/v1/e2b/projects/{self.project_id}/sandboxes/{provider_run_id}"
            )
            response.raise_for_status()
            data = response.json()
            
            # Map E2B states to normalized states
            e2b_state = data.get("status", "unknown").upper()
            state_map = {
                "PENDING": "QUEUED",
                "RUNNING": "RUNNING",
                "SUCCEEDED": "SUCCEEDED",
                "FAILED": "FAILED",
                "CANCELLED": "CANCELLED",
                "TERMINATED": "FAILED",
            }
            normalized_state = state_map.get(e2b_state, e2b_state)
            
            return {
                "state": normalized_state,
                "startedAt": data.get("createdAt"),
                "finishedAt": data.get("endedAt"),
                "exitCode": data.get("exitCode"),
                "meta": {
                    "status": e2b_state,
                    "template": data.get("template"),
                },
            }
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderError(
                    f"Sandbox not found: {provider_run_id}",
                    code="not_found",
                    retryable=False,
                ) from e
            raise ProviderError(
                f"Status check failed: {redact_sensitive(str(e))}",
                code="status_failed",
                retryable=True,
            ) from e
        
        except httpx.RequestError as e:
            raise ProviderError(
                f"Connection error: {redact_sensitive(str(e))}",
                code="connection_error",
                retryable=True,
            ) from e
    
    async def logs(
        self,
        provider_run_id: str,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """
        Get logs from an E2B sandbox via Simultaneous API.
        
        Args:
            provider_run_id: Sandbox ID
            cursor: Pagination cursor (optional)
            
        Returns:
            Logs dict with: entries, next_cursor
        """
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        
        try:
            # Call Simultaneous API to get sandbox logs
            response = await self.client.get(
                f"/v1/e2b/projects/{self.project_id}/sandboxes/{provider_run_id}/logs",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize log entries
            entries = []
            for entry in data.get("logs", []):
                entries.append({
                    "ts": entry.get("timestamp"),
                    "stream": entry.get("stream", "stdout"),
                    "line": entry.get("message", ""),
                })
            
            return {
                "entries": entries,
                "next_cursor": data.get("nextCursor"),
            }
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderError(
                    f"Sandbox not found: {provider_run_id}",
                    code="not_found",
                    retryable=False,
                ) from e
            raise ProviderError(
                f"Logs fetch failed: {redact_sensitive(str(e))}",
                code="logs_failed",
                retryable=True,
            ) from e
        
        except httpx.RequestError as e:
            raise ProviderError(
                f"Connection error: {redact_sensitive(str(e))}",
                code="connection_error",
                retryable=True,
            ) from e
    
    async def cancel(self, provider_run_id: str) -> None:
        """
        Cancel an E2B sandbox via Simultaneous API.
        
        Args:
            provider_run_id: Sandbox ID
        """
        try:
            # Call Simultaneous API to cancel sandbox
            response = await self.client.post(
                f"/v1/e2b/projects/{self.project_id}/sandboxes/{provider_run_id}/cancel"
            )
            response.raise_for_status()
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Already cancelled or not found - treat as success
                return
            raise ProviderError(
                f"Cancel failed: {redact_sensitive(str(e))}",
                code="cancel_failed",
                retryable=False,
            ) from e
        
        except httpx.RequestError as e:
            raise ProviderError(
                f"Connection error: {redact_sensitive(str(e))}",
                code="connection_error",
                retryable=True,
            ) from e

