import asyncio
import logging

from sqlalchemy import text

from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_invalid_status():
    async with engine.begin() as conn:
        try:
            # Check if 'invalid' exists in the enum
            # This is postgres specific
            logger.info("Attempting to add 'invalid' to log_status_enum...")
            await conn.execute(text("ALTER TYPE log_status_enum ADD VALUE IF NOT EXISTS 'invalid';"))
            logger.info("Successfully added 'invalid' to log_status_enum.")
        except Exception as e:
            logger.error(f"Migration failed (it might already exist or not be supported on this DB): {e}")


if __name__ == "__main__":
    asyncio.run(add_invalid_status())
