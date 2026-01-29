import asyncio
import os

import asyncpg

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres_test")
if "postgresql+asyncpg://" in TEST_DB_URL:
    TEST_DB_URL = TEST_DB_URL.replace("postgresql+asyncpg://", "postgresql://")


async def test_auth_uid():
    print(f"Connecting to {TEST_DB_URL}...")
    conn = await asyncpg.connect(TEST_DB_URL)

    try:
        print("Testing auth.uid() without config...")
        val = await conn.fetchval("SELECT auth.uid()")
        print(f"auth.uid() = {val} (Expected None)")

        print("Testing auth.uid() WITH config...")
        # Note: set_config is transaction-local usually
        async with conn.transaction():
            await conn.execute(
                'SELECT set_config(\'request.jwt.claims\', \'{"sub": "12345678-1234-5678-1234-567812345678", "role": "authenticated"}\', true)'
            )
            val = await conn.fetchval("SELECT auth.uid()")
            print(f"auth.uid() = {val} (Expected UUID)")

            role = await conn.fetchval("SELECT auth.role()")
            print(f"auth.role() = {role} (Expected authenticated)")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(test_auth_uid())
