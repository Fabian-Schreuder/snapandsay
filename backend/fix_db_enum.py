import asyncio
import os
import logging
from sqlalchemy import text, create_engine, inspect
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_enum():
    db_url = settings.DATABASE_URL
    # Mask password for logging
    masked_url = db_url.split("@")[-1] if "@" in db_url else "unknown"
    logger.info(f"Connecting to database at ...@{masked_url}")

    # Use sync engine for simple schema inspection/alteration script
    # Asyncpg can be tricky with some DDL commands in transactions
    # We will use the sync driver logic if possible, or just raw sql via invalidation
    
    # Actually, let's stick to the raw connection string we have but use a sync driver if needed
    # But settings.DATABASE_URL is async (postgresql+asyncpg).
    # Let's verify if we can use async engine for this.
    
    from sqlalchemy.ext.asyncio import create_async_engine
    
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        logger.info("Checking current values for 'log_status_enum'...")
        
        # This query works on Postgres to get enum labels
        result = await conn.execute(text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'log_status_enum'"))
        existing_labels = [row[0] for row in result.fetchall()]
        
        logger.info(f"Found labels: {existing_labels}")
        
        if "failed" not in existing_labels:
            logger.info("Adding 'failed' to log_status_enum...")
            # ALTER TYPE ... ADD VALUE cannot run inside a transaction block in some contexts, 
            # but usually it's fine in autocommit mode. 
            # SQLAlchemy async 'begin' starts a transaction. 
            # Let's try to execute it.
            try:
                await conn.execute(text("ALTER TYPE log_status_enum ADD VALUE 'failed'"))
                logger.info("Successfully added 'failed'.")
            except Exception as e:
                logger.error(f"Failed to add value: {e}")
                # It might fail if it exists (race condition) or transaction issue
        else:
            logger.info("'failed' already exists in log_status_enum.")

if __name__ == "__main__":
    try:
        asyncio.run(fix_enum())
    except Exception as e:
        logger.error(f"Script failed: {e}")
