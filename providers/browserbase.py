"""Browserbase provider adapter via Simultaneous API."""

import asyncio
from typing import Any

import httpx

from simultaneous.providers.base import ProviderAdapter, ProviderError
from simultaneous.utils.env import get_env, redact_sensitive


class BrowserbaseAdapter:
    """
    Adapter for Browserbase provider via Simultaneous API.
    
    This adapter calls the Simultaneous API to create Browserbase sessions,
    which then returns session URLs that can be used with browser clients like BrowserClient.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        project_id: str | None = None,
        region: str | None = None,
        simultaneous_api_url: str | None = None,
        simultaneous_api_key: str | None = None,
    ):
        """
        Initialize Browserbase adapter.
        
        Args:
            api_key: Simultaneous API key (defaults to SIMULTANEOUS_API_KEY env var)
            project_id: Simultaneous project ID (UUID)
            region: Region for Browserbase (defaults to "sfo")
            simultaneous_api_url: Simultaneous API base URL (defaults to https://api.simultaneous.live)
            simultaneous_api_key: Simultaneous API key (alternative to api_key)
        """
        self.simultaneous_api_key = simultaneous_api_key or api_key or get_env("SIMULTANEOUS_API_KEY")
        self.project_id = project_id  # Simultaneous project ID (UUID)
        self.region = region or get_env("BROWSERBASE_REGION", "sfo")
        
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
        Launch a new session via Simultaneous API (which creates a Browserbase session).
        
        Args:
            bundle_url: URL to agent bundle
            env: Environment variables
            options: Additional options (script, timeout_sec, etc.)
            
        Returns:
            Dictionary with session_id and session_url (connectUrl)
        """
        payload: dict[str, Any] = {
            "region": self.region,
        }
        
        if env:
            payload["env"] = env
        
        if bundle_url:
            payload["bundleUrl"] = bundle_url
        
        if options:
            # Extract Browserbase-specific options
            if "script" in options:
                payload["script"] = options["script"]
            if "timeoutSec" in options:
                payload["timeoutSec"] = options["timeoutSec"]
            if "projectId" in options:
                payload["projectId"] = options["projectId"]  # Browserbase project ID
            elif "browserbase_project_id" in options:
                payload["projectId"] = options["browserbase_project_id"]
        
        try:
            # Call Simultaneous API to create a Browserbase session
            response = await self.client.post(
                f"/v1/browserbase/projects/{self.project_id}/sessions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract provider session info from Simultaneous API response
            # Our API returns both the internal session id (id) and providerSessionId
            session_id = (
                data.get("providerSessionId")
                or data.get("provider_session_id")
                or data.get("sessionId")
                or data.get("id")
            )
            connect_url = data.get("connectUrl") or data.get("connect_url")
            selenium_url = data.get("seleniumRemoteUrl") or data.get("selenium_remote_url")
            
            if not session_id:
                raise ProviderError("Simultaneous API response missing session ID")
            
            if not connect_url:
                # Try to get URL from session details endpoint
                session_detail = await self.client.get(
                    f"/v1/browserbase/projects/{self.project_id}/sessions/{session_id}"
                )
                if session_detail.status_code == 200:
                    detail_data = session_detail.json()
                    connect_url = detail_data.get("connectUrl") or detail_data.get("connect_url")
            
            return {
                "session_id": str(session_id),
                "session_url": connect_url,  # WebSocket URL for browser connection
                "selenium_url": selenium_url,
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
        Get status of a Browserbase session via Simultaneous API.
        
        Args:
            provider_run_id: Session ID
            
        Returns:
            Status dict with: state, startedAt, finishedAt, exitCode, meta
        """
        try:
            # Call Simultaneous API to get session status
            response = await self.client.get(
                f"/v1/browserbase/projects/{self.project_id}/sessions/{provider_run_id}"
            )
            response.raise_for_status()
            data = response.json()
            
            # Map Browserbase states to normalized states
            bb_state = data.get("status", "unknown").upper()
            state_map = {
                "PENDING": "QUEUED",
                "RUNNING": "RUNNING",
                "SUCCEEDED": "SUCCEEDED",
                "FAILED": "FAILED",
                "CANCELLED": "CANCELLED",
                "TIMEOUT": "FAILED",
            }
            normalized_state = state_map.get(bb_state, bb_state)
            
            return {
                "state": normalized_state,
                "startedAt": data.get("createdAt"),
                "finishedAt": data.get("endedAt"),
                "exitCode": data.get("exitCode"),
                "meta": {
                    "status": bb_state,
                    "region": data.get("region"),
                },
            }
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderError(
                    f"Session not found: {provider_run_id}",
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
        Get logs from a Browserbase session via Simultaneous API.
        
        Args:
            provider_run_id: Session ID
            cursor: Pagination cursor (optional)
            
        Returns:
            Logs dict with: entries, next_cursor
        """
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        
        try:
            # Call Simultaneous API to get session logs
            response = await self.client.get(
                f"/v1/browserbase/projects/{self.project_id}/sessions/{provider_run_id}/logs",
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
                    f"Session not found: {provider_run_id}",
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
        Cancel a Browserbase session via Simultaneous API.
        
        Args:
            provider_run_id: Session ID
        """
        try:
            # Call Simultaneous API to cancel session
            response = await self.client.post(
                f"/v1/browserbase/projects/{self.project_id}/sessions/{provider_run_id}/cancel"
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







