from collections.abc import AsyncGenerator


from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .models import Base

# Handle the protocol replacement for asyncpg safely without deconstructing the URL
# This avoids issues with special characters in passwords
if settings.DATABASE_URL.startswith("postgresql://"):
    async_db_connection_url = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
else:
    async_db_connection_url = settings.DATABASE_URL

# Disable connection pooling for serverless environments like Vercel
engine = create_async_engine(async_db_connection_url, poolclass=NullPool)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=settings.EXPIRE_ON_COMMIT
)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
