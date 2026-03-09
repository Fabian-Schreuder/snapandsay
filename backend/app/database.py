import logging
import ssl
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .models import Base

# Handle the protocol replacement for asyncpg safely without deconstructing the URL
# This avoids issues with special characters in passwords
if settings.DATABASE_URL.startswith("postgresql://"):
    async_db_connection_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    async_db_connection_url = settings.DATABASE_URL

# Disable connection pooling for serverless environments like Vercel
# Disable statement cache for compatibility with transaction poolers (like Supavisor on port 6543)
logger.info("Creating database engine...")
# Log the DB URL (mask password)
safe_url = settings.DATABASE_URL
if "@" in safe_url:
    part1, part2 = safe_url.split("@")
    safe_url = f"{part1.split(':')[0]}:***@{part2}"
logger.info(f"Connecting to Database: {safe_url}")


connect_args = {
    "statement_cache_size": 0,
}
if "127.0.0.1" in async_db_connection_url or "localhost" in async_db_connection_url:
    connect_args["ssl"] = False
else:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    async_db_connection_url,
    echo=settings.ECHO_SQL,
    poolclass=NullPool,
    connect_args=connect_args,
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=settings.EXPIRE_ON_COMMIT)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
