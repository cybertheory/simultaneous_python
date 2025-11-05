"""Tests for Browserbase adapter."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from simultaneous.providers.base import ProviderError
from simultaneous.providers.browserbase import BrowserbaseAdapter


@pytest.mark.asyncio
async def test_launch_success() -> None:
    """Test successful session launch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "session_123"}
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        adapter = BrowserbaseAdapter(api_key="test_key")
        
        session_id = await adapter.launch()
        
        assert session_id == "session_123"
        mock_client.post.assert_called_once()
        
        await adapter.close()


@pytest.mark.asyncio
async def test_launch_with_bundle() -> None:
    """Test launch with bundle URL."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "session_456"}
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        adapter = BrowserbaseAdapter(api_key="test_key")
        
        session_id = await adapter.launch(
            bundle_url="https://example.com/bundle.tar.gz",
            env={"KEY": "value"},
        )
        
        assert session_id == "session_456"
        call_args = mock_client.post.call_args
        assert call_args[1]["json"].get("bundleUrl") == "https://example.com/bundle.tar.gz"
        assert call_args[1]["json"].get("env") == {"KEY": "value"}
        
        await adapter.close()


@pytest.mark.asyncio
async def test_launch_auth_error() -> None:
    """Test launch with authentication error."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client_class.return_value = mock_client
        
        adapter = BrowserbaseAdapter(api_key="test_key")
        
        with pytest.raises(ProviderError) as exc_info:
            await adapter.launch()
        
        assert exc_info.value.code == "auth_failed"
        assert not exc_info.value.retryable
        
        await adapter.close()


@pytest.mark.asyncio
async def test_status_success() -> None:
    """Test successful status check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "RUNNING",
        "createdAt": "2024-01-01T00:00:00Z",
        "endedAt": None,
        "exitCode": None,
        "region": "sfo",
    }
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        adapter = BrowserbaseAdapter(api_key="test_key")
        
        status = await adapter.status("session_123")
        
        assert status["state"] == "RUNNING"
        assert status["startedAt"] == "2024-01-01T00:00:00Z"
        assert status["finishedAt"] is None
        
        await adapter.close()


@pytest.mark.asyncio
async def test_status_not_found() -> None:
    """Test status check for non-existent session."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client_class.return_value = mock_client
        
        adapter = BrowserbaseAdapter(api_key="test_key")
        
        with pytest.raises(ProviderError) as exc_info:
            await adapter.status("session_999")
        
        assert exc_info.value.code == "not_found"
        
        await adapter.close()


@pytest.mark.asyncio
async def test_logs_success() -> None:
    """Test successful log fetching."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "logs": [
            {"timestamp": "2024-01-01T00:00:00Z", "stream": "stdout", "message": "Hello"},
            {"timestamp": "2024-01-01T00:00:01Z", "stream": "stderr", "message": "Error"},
        ],
        "nextCursor": "cursor_123",
    }
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        adapter = BrowserbaseAdapter(api_key="test_key")
        
        logs = await adapter.logs("session_123")
        
        assert len(logs["entries"]) == 2
        assert logs["entries"][0]["stream"] == "stdout"
        assert logs["entries"][0]["line"] == "Hello"
        assert logs["next_cursor"] == "cursor_123"
        
        await adapter.close()


@pytest.mark.asyncio
async def test_cancel_success() -> None:
    """Test successful cancellation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        adapter = BrowserbaseAdapter(api_key="test_key")
        
        # Should not raise
        await adapter.cancel("session_123")
        
        mock_client.post.assert_called_once()
        
        await adapter.close()


@pytest.mark.asyncio
async def test_missing_api_key() -> None:
    """Test missing API key raises error."""
    with pytest.raises(ProviderError) as exc_info:
        BrowserbaseAdapter()
    
    assert "API key required" in str(exc_info.value)





