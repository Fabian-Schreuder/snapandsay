import asyncio
import os
import uuid

import asyncpg

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres_test")
if "postgresql+asyncpg://" in TEST_DB_URL:
    TEST_DB_URL = TEST_DB_URL.replace("postgresql+asyncpg://", "postgresql://")


async def reproduce_error():
    print(f"Connecting to {TEST_DB_URL}...")
    conn = await asyncpg.connect(TEST_DB_URL)

    test_id = str(uuid.uuid4())
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    metadata = f'{{"anonymous_id": "test_anon_{uuid.uuid4().hex[:8]}"}}'

    print("Attempting INSERT...")
    try:
        await conn.execute(
            """
            INSERT INTO auth.users (
                instance_id, id, aud, role, email, 
                encrypted_password, email_confirmed_at, raw_user_meta_data
            )
            VALUES (
                '00000000-0000-0000-0000-000000000000',
                $1,
                'authenticated',
                'authenticated',
                $2,
                'password',
                now(),
                CAST($3 AS jsonb)
            )
        """,
            test_id,
            email,
            metadata,
        )
        print("INSERT successful!")
    except Exception as e:
        print(f"INSERT FAILED: {e}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(reproduce_error())
