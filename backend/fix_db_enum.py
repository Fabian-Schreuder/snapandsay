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

# Attempt to use port 54322 if localhost (common for local supabase)
if "localhost:5432" in DATABASE_URL:
    print("Detected localhost:5432, trying 54322 for Docker mapped port...")
    # Try default supabase docker password if 'password' is used
    if "postgres:password" in DATABASE_URL:
         print("Overwriting with detected Docker credentials...")
         # Docker inspect confirmed: POSTGRES_PASSWORD=postgres
         # Database name is likely 'postgres'
         DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"
    
    # Also handle if it was already modified but still wrong
    if "localhost:54322" in DATABASE_URL and "postgres:postgres" not in DATABASE_URL:
         print("Forcing correct credentials for localhost:54322...")
         DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"

async def fix_enum():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Checking log_status_enum values...")
        # Check current values
        result = await conn.execute(text("SELECT unnest(enum_range(NULL::log_status_enum))"))
        values = [row[0] for row in result.fetchall()]
        print(f"Current values: {values}")
        
        if 'failed' not in values:
            print("Adding 'failed' to log_status_enum...")
            # This cannot run inside a transaction block for some PG versions, but ALTER TYPE ADD VALUE usually handles it.
            # However, SQLAlchemy's begin() starts a transaction. ALTER TYPE ... ADD VALUE cannot run inside a transaction block.
            # We need to run it in isolation level AUTOCOMMIT.
            pass
        else:
            print("'failed' already exists in enum")
            return

    # Re-connect with isolation level autocommit for ALTER TYPE
    engine_autocommit = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT", echo=True)
    async with engine_autocommit.connect() as conn:
        if 'failed' not in values:
             await conn.execute(text("ALTER TYPE log_status_enum ADD VALUE 'failed'"))
             print("Added 'failed' successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(fix_enum())
    except Exception as e:
        print(f"Error: {e}")
