import asyncio

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def check_db():
    print("--- Database Check ---")
    db_url = settings.DATABASE_URL
    print(f"Loaded DATABASE_URL: {db_url.split('@')[-1] if '@' in db_url else 'INVALID'}")

    try:
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            print("Successfully connected to database!")

            # Check DB name
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"Current Database: {db_name}")

            # Check Enum
            print("Checking log_status_enum...")
            result = await conn.execute(
                text(
                    "SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'log_status_enum'"
                )
            )
            labels = [row[0] for row in result.fetchall()]
            print(f"Enum labels found: {labels}")

            if "failed" in labels:
                print("SUCCESS: 'failed' is in enum.")
            else:
                print("FAILURE: 'failed' is MISSING from enum.")

    except Exception as e:
        print(f"Database connection failed: {e}")


async def check_llm():
    print("\n--- LLM Check ---")
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        print("FAILURE: OPENAI_API_KEY is not set.")
        return

    print(f"OPENAI_API_KEY is set (starts with {api_key[:8]}...)")

    client = AsyncOpenAI(api_key=api_key)

    try:
        print("Attempting simple completion...")
        response = await client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": "Hello"}], max_tokens=5
        )
        print(f"Response received: {response.choices[0].message.content}")

        print("Attempting streaming completion...")
        stream = await client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": "Hello"}], stream=True, max_tokens=5
        )

        print("Stream started. Chunks:")
        async for chunk in stream:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    print(f"Chunk: {content!r}")
        print("Stream finished.")

    except Exception as e:
        print(f"LLM call failed: {e}")


async def main():
    await check_db()
    await check_llm()


if __name__ == "__main__":
    # Ensure we use the same env file loading logic as the app
    # The app uses pydantic_settings which reads .env by default
    asyncio.run(main())
