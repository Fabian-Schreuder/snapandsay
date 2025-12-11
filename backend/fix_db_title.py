import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment")
    exit(1)

# Ensure async driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Handle local dev port mapping 
if "localhost:5432" in DATABASE_URL and "postgres:password" in DATABASE_URL:
     print("Detected localhost dev environment, checking port 54322...")
     DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"

async def fix_title():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Checking for title column in dietary_logs...")
        # Check if column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='dietary_logs' AND column_name='title'"
        ))
        
        if not result.scalar():
            print("Adding 'title' column...")
            await conn.execute(text("ALTER TABLE dietary_logs ADD COLUMN title VARCHAR"))
            print("Column 'title' added successfully.")
        else:
            print("Column 'title' already exists.")

if __name__ == "__main__":
    try:
        asyncio.run(fix_title())
    except Exception as e:
        print(f"Error: {e}")
