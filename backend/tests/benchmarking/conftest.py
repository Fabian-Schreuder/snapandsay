"""Override root conftest fixtures for benchmarking unit tests that don't need DB."""

import pytest_asyncio


@pytest_asyncio.fixture(scope="function")
async def engine():
    """No-op engine for benchmarking tests — no DB needed."""
    yield None


@pytest_asyncio.fixture(scope="function", autouse=True)
async def patch_session_maker(engine):
    """No-op session maker patch for benchmarking tests."""
    yield
