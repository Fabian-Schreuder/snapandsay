import asyncio
import os
import tomllib
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path="../.env")

# Try to read port from config or use default
try:
    with open("../supabase/config.toml", "rb") as f:
        config = tomllib.load(f)
        DB_PORT = config.get("db", {}).get("port", 54322)
except Exception:
    DB_PORT = 54322

# Construct async DB URL
# Note: We need the service_role key or postgres admin credentials to setup the test data
# For local dev, postgres/postgres is usually fine for admin tasks
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+asyncpg://postgres:postgres@127.0.0.1:{DB_PORT}/postgres")

async def validate_db():
    print(f"Connecting to DB on port {DB_PORT}...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        print("\n--- 1. Schema Validation ---")
        
        # 1. Check Extension
        result = await conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        if result.first():
            print("✅ 'vector' extension is installed.")
        else:
            print("❌ 'vector' extension MISSING.")
            
        # 2. Check Users Table
        result = await conn.execute(text("SELECT to_regclass('public.users')"))
        if result.scalar():
            print("✅ 'public.users' table exists.")
        else:
            print("❌ 'public.users' table MISSING.")
            return # Cannot proceed

    # 3. Functional Testing (Triggers & RLS)
    print("\n--- 2. Functional Testing (Triggers & RLS) ---")
    
    # We need to act as different users. 
    # Since we are using the postgres admin user, we can set local role/config to simulate RLS
    # BUT, to test the trigger 'on_auth_user_created', we must insert into auth.users.
    
    test_user_id = "00000000-0000-0000-0000-000000000001"
    test_email = "test_user_1@example.com"
    
    async with engine.begin() as conn:
        try:
            # Clean up previous test run
            await conn.execute(text(f"DELETE FROM auth.users WHERE id = '{test_user_id}'"))
            await conn.execute(text(f"DELETE FROM public.users WHERE id = '{test_user_id}'"))
            
            print("Testing Trigger: creating new auth.user...")
            # Insert into auth.users to fire trigger
            await conn.execute(text(f"""
                INSERT INTO auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, raw_user_meta_data)
                VALUES ('00000000-0000-0000-0000-000000000000', '{test_user_id}', 'authenticated', 'authenticated', '{test_email}', 'password', now(), '{{"anonymous_id": "test_anon_id"}}')
            """))
            
            # Check if public.users record was created automatically
            result = await conn.execute(text(f"SELECT * FROM public.users WHERE id = '{test_user_id}'"))
            user_record = result.first()
            
            if user_record:
                print(f"✅ Trigger fired: public.users record created for {test_user_id}")
                if user_record.anonymous_id == "test_anon_id":
                    print("✅ Metadata extraction: anonymous_id correctly populated")
                else:
                    print(f"❌ Metadata fail: expected 'test_anon_id', got {user_record.anonymous_id}")
            else:
                print("❌ Trigger FAIL: public.users record NOT created")

        except Exception as e:
            print(f"❌ Error during trigger test: {e}")
            
    # 4. RLS Verification
    # To test RLS, we switch the current transaction's role to 'authenticated' and set request.jwt.claim.sub
    
    print("\n--- 3. RLS Validation ---")
    
    async with engine.connect() as conn: # Use connect for session-level config settings
        trans = await conn.begin()
        try:
            # Context: User 1
            await conn.execute(text("SET LOCAL ROLE authenticated"))
            await conn.execute(text(f"SELECT set_config('request.jwt.claims', '{{\"sub\": \"{test_user_id}\", \"role\": \"authenticated\"}}', true)"))
            
            # Attempt to read own data
            result = await conn.execute(text("SELECT id FROM public.users"))
            rows = result.fetchall()
            if len(rows) == 1 and str(rows[0].id) == test_user_id:
                print("✅ RLS Success: User can see their own data")
            elif len(rows) == 0:
                print("❌ RLS Fail: User CANNOT see their own data")
            else:
                print(f"❌ RLS Fail: User saw {len(rows)} rows (expected 1)")

            # Clean up not needed as transaction rolls back or we just end session, 
            # but for cleanliness we'll delete the test user as admin in a new block
            
        except Exception as e:
            print(f"❌ Error during RLS test: {e}")
        finally:
            await trans.rollback()

    # Cleanup
    async with engine.begin() as conn:
        print("\n--- cleanup ---")
        await conn.execute(text(f"DELETE FROM auth.users WHERE id = '{test_user_id}'"))
        print("Test data cleaned up.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(validate_db())
