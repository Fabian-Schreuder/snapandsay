import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.database as app_db
from app.config import settings
from app.database import get_async_session
from app.main import app as fastapi_app
from app.models import Base


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create a fresh test database engine for each test function."""
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=True)

    # Ensure schema is fresh for tests (commented out by default to avoid accidental data loss)
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def patch_session_maker(engine):
    """Patch the global async_session_maker to use the test engine."""
    old_session_maker = app_db.async_session_maker
    app_db.async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield
    app_db.async_session_maker = old_session_maker


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Create a fresh database session for each test."""
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session):
    """Fixture to create a test client that uses the test database session."""

    # General database override (raw session access)
    async def override_get_async_session():
        try:
            yield db_session
        finally:
            await db_session.close()

    # Set up test database override
    fastapi_app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://localhost:8000"
    ) as client:
        yield client
