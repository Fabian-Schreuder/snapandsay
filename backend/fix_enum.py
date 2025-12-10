import asyncio
from app.database import engine
from sqlalchemy import text

async def add_failed_to_enum():
    async with engine.begin() as conn:
        print("Adding 'failed' to log_status_enum...")
        try:
            # Postgres supports ALTER TYPE ... ADD VALUE
            await conn.execute(text("ALTER TYPE log_status_enum ADD VALUE IF NOT EXISTS 'failed';"))
            print("Successfully added 'failed' to log_status_enum")
        except Exception as e:
            print(f"Error adding enum value: {e}")

if __name__ == "__main__":
    asyncio.run(add_failed_to_enum())
