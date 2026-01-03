import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

# Add backend to path
sys.path.append(os.getcwd())

async def main():
    url = settings.TEST_DATABASE_URL
    print("Connecting to Test DB")
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE dietary_logs ADD COLUMN IF NOT EXISTS needs_review BOOLEAN NOT NULL DEFAULT FALSE;"))
            print("Migration applied successfully")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
