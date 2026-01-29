import asyncio
import os
import uuid

import asyncpg

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres_test")
if "postgresql+asyncpg://" in TEST_DB_URL:
    TEST_DB_URL = TEST_DB_URL.replace("postgresql+asyncpg://", "postgresql://")


async def reproduce_rls_error():
    print(f"Connecting to {TEST_DB_URL}...")
    conn = await asyncpg.connect(TEST_DB_URL)

    test_id = str(uuid.uuid4())
    print(f"Test ID: {test_id}")

    try:
        # 1. Insert user as superuser (postgres)
        print("Inserting user...")
        await conn.execute(
            """
            INSERT INTO auth.users (id, aud, role, email, encrypted_password, email_confirmed_at, raw_user_meta_data)
            VALUES ($1, 'authenticated', 'authenticated', $2, 'password', now(), $3::jsonb)
        """,
            test_id,
            f"rls_{test_id[:8]}@example.com",
            f'{{"anonymous_id": "anon_{test_id[:8]}"}}',
        )

        # 2. Switch to authenticated role
        print("Switching to 'authenticated' role...")
        async with conn.transaction():
            await conn.execute("SET LOCAL ROLE authenticated")

            # 3. Set config
            claims = f'{{"sub": "{test_id}", "role": "authenticated"}}'
            print(f"Setting claims: {claims}")
            await conn.execute("SELECT set_config('request.jwt.claims', $1, true)", claims)

            # 4. Select from public.users
            print("Selecting from public.users...")
            row = await conn.fetchrow("SELECT id FROM public.users WHERE id = $1", test_id)
            print(f"Result: {row}")

    except Exception as e:
        print(f"ERROR: {e}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(reproduce_rls_error())
