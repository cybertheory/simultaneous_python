"""Tests for provider router."""

import pytest

from simultaneous.providers.base import ProviderError
from simultaneous.providers.router import get_adapter
from simultaneous.runtime.base import RuntimeKind


def test_get_browserbase_adapter() -> None:
    """Test getting Browserbase adapter for browser runtime."""
    adapter = get_adapter(
        runtime_kind=RuntimeKind.BROWSER,
        provider="browserbase",
        config={"api_key": "test_key"},
    )
    
    assert adapter is not None
    assert hasattr(adapter, "launch")
    assert hasattr(adapter, "status")
    assert hasattr(adapter, "logs")
    assert hasattr(adapter, "cancel")


def test_get_browserbase_adapter_auto() -> None:
    """Test auto provider defaults to browserbase for browser runtime."""
    adapter = get_adapter(
        runtime_kind=RuntimeKind.BROWSER,
        provider="auto",
        config={"api_key": "test_key"},
    )
    
    assert adapter is not None
    assert hasattr(adapter, "launch")


def test_unsupported_provider() -> None:
    """Test unsupported provider raises error."""
    with pytest.raises(ProviderError) as exc_info:
        get_adapter(
            runtime_kind=RuntimeKind.BROWSER,
            provider="unsupported",
            config={},
        )
    
    assert "Unsupported provider" in str(exc_info.value)


def test_unsupported_runtime() -> None:
    """Test unsupported runtime kind raises error."""
    with pytest.raises(ProviderError) as exc_info:
        get_adapter(
            runtime_kind=RuntimeKind.DESKTOP,
            provider="auto",
            config={},
        )
    
    assert "not yet supported" in str(exc_info.value)





