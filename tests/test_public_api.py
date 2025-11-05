"""Tests for public API."""

import pytest

from simultaneous import Browser, SimClient


@pytest.mark.asyncio
async def test_client_initialization() -> None:
    """Test client initialization."""
    client = SimClient(api_key="test_key")
    
    assert client.api_key == "test_key"
    assert client.default_runtime is not None
    assert hasattr(client, "runs")
    assert hasattr(client, "logs")
    assert hasattr(client, "workflow")


@pytest.mark.asyncio
async def test_agent_decorator() -> None:
    """Test agent decorator registration."""
    client = SimClient()
    
    @client.agent(name="test-agent", runtime=Browser())
    async def test_agent(query: str) -> list[dict]:
        """Test agent."""
        return []
    
    agent_info = client.get_agent("test-agent")
    
    assert agent_info is not None
    assert agent_info["name"] == "test-agent"
    assert "func" in agent_info
    assert len(agent_info["inputs"]) == 1
    assert agent_info["inputs"][0]["name"] == "query"


def test_browser_runtime() -> None:
    """Test Browser runtime creation."""
    browser = Browser(provider="browserbase", region="sfo", project="proj_123")
    
    assert browser.kind.value == "browser"
    assert browser.provider == "browserbase"
    assert browser.region == "sfo"
    assert browser.project == "proj_123"
    
    runtime_dict = browser.to_dict()
    assert runtime_dict["kind"] == "browser"
    assert runtime_dict["provider"] == "browserbase"


def test_browser_runtime_auto() -> None:
    """Test Browser runtime with auto provider."""
    browser = Browser()
    
    assert browser.provider == "auto"
    assert browser.region == "auto"





