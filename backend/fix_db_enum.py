import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment")
    exit(1)

# Remove the +asyncpg driver specifier if present (from previous script logic or wrong env)
if "postgresql+asyncpg://" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Ensure using port 54322 mapping logic if still relevant (kept for robustness, though production URL provided)
if (
    "localhost:5432" in DATABASE_URL
    and "postgres:password" in DATABASE_URL
    and "localhost:54322" not in DATABASE_URL
):
    # This logic was in the previous script, might not be needed for production run but keeping safe
    pass


async def fix_enum():
    try:
        print("Connecting to database...")
        # statement_cache_size=0 is critical for PgBouncer in transaction mode
        conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)

        print("Checking log_status_enum values...")
        # Get enum values
        # enum_range returns an array
        row = await conn.fetchrow("SELECT enum_range(NULL::log_status_enum)")
        enum_array = row[0] if row else []
        print(f"Current values: {enum_array}")

        if "failed" not in enum_array:
            print("Adding 'failed' to log_status_enum...")
            await conn.execute("ALTER TYPE log_status_enum ADD VALUE 'failed'")
            print("Added 'failed' successfully.")

        if "invalid" not in enum_array:
            print("Adding 'invalid' to log_status_enum...")
            await conn.execute("ALTER TYPE log_status_enum ADD VALUE 'invalid'")
            print("Added 'invalid' successfully.")

        if "failed" in enum_array and "invalid" in enum_array:
            print("All required enum values exist.")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(fix_enum())
