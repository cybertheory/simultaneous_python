"""Pytest configuration and shared fixtures."""

import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base

# Use in-memory SQLite for tests (isolated, fast, no external dependencies)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Create a test database session.
    
    Uses in-memory SQLite for fast, isolated tests.
    This is independent of Supabase - tests don't need external connections.
    """
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = AsyncSession(test_engine, expire_on_commit=False)
    try:
        yield async_session
    finally:
        await async_session.close()
        await test_engine.dispose()


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for tests that need it.
    
    Returns a mock Supabase client that can be used in tests.
    """
    mock_client = MagicMock()
    mock_client.auth = MagicMock()
    mock_client.storage = MagicMock()
    return mock_client


@pytest.fixture
def disable_supabase_auth():
    """Disable Supabase auth checks in tests.
    
    This fixture patches the Supabase auth dependencies to allow tests
    to run without requiring real authentication.
    """
    with patch("app.services.supabase_auth.get_current_user"), \
         patch("app.services.supabase_auth.get_optional_user"):
        # Return None for optional user, or mock user for required auth
        yield


@pytest.fixture
def mock_supabase_user():
    """Mock Supabase user for authenticated tests.
    
    Returns a mock user dictionary that can be used in tests.
    """
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "user_metadata": {},
        "app_metadata": {},
    }


@pytest.fixture(autouse=True)
def reset_env_vars():
    """Reset environment variables before each test.
    
    Ensures tests don't interfere with each other's environment.
    """
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)





