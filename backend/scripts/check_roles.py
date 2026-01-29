import asyncio
import os

import asyncpg

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres_test")
if "postgresql+asyncpg://" in TEST_DB_URL:
    TEST_DB_URL = TEST_DB_URL.replace("postgresql+asyncpg://", "postgresql://")


async def check_roles():
    print(f"Connecting to {TEST_DB_URL}...")
    conn = await asyncpg.connect(TEST_DB_URL)

    roles = await conn.fetch(
        "SELECT rolname FROM pg_roles WHERE rolname IN ('authenticated', 'anon', 'service_role')"
    )
    print(f"Found roles: {[r['rolname'] for r in roles]}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_roles())
