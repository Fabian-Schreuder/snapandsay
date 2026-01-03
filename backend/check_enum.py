import asyncio

import asyncpg

DB_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


async def check_enum():
    try:
        conn = await asyncpg.connect(DB_DSN)
        print(f"Connected to {DB_DSN}")

        # Query to get enum labels
        query = """
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'log_status_enum';
        """

        rows = await conn.fetch(query)
        labels = [row["enumlabel"] for row in rows]
        print(f"Current labels for 'log_status_enum': {labels}")

        await conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_enum())
