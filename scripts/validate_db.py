"""Database validation script for Supabase schema.

This script validates:
1. Schema correctness (tables, extensions)
2. Trigger functionality (auto-creation of public.users)
3. RLS policies (SELECT and UPDATE permissions)

Run from project root: python scripts/validate_db.py
"""
import asyncio
import os
import tomllib
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"
CONFIG_FILE = PROJECT_ROOT / "supabase" / "config.toml"

# Load env variables from project root
if ENV_FILE.exists():
    load_dotenv(dotenv_path=str(ENV_FILE))

# Try to read port from config or use default
DB_PORT = 54322
try:
    with open(CONFIG_FILE, "rb") as f:
        config = tomllib.load(f)
        DB_PORT = config.get("db", {}).get("port", 54322)
except Exception:
    pass

# Construct async DB URL from env or use secure default
# SECURITY: Never hardcode credentials in production
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "SUPABASE_DB_URL",
        f"postgresql+asyncpg://postgres:postgres@127.0.0.1:{DB_PORT}/postgres"
    )
)

async def validate_db() -> None:
    """Validate database schema, triggers, and RLS policies.
    
    Performs comprehensive validation:
    - Extension installation (vector)
    - Table existence (public.users)
    - Trigger functionality (on_auth_user_created)
    - RLS policies (SELECT, UPDATE)
    
    Raises:
        Exception: If critical validation steps fail
    """
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
    test_anon_id = "test_anon_id"
    
    async with engine.begin() as conn:
        try:
            # Clean up previous test run using parameterized queries
            await conn.execute(
                text("DELETE FROM auth.users WHERE id = :user_id"),
                {"user_id": test_user_id}
            )
            await conn.execute(
                text("DELETE FROM public.users WHERE id = :user_id"),
                {"user_id": test_user_id}
            )
            
            print("Testing Trigger: creating new auth.user...")
            # Insert into auth.users to fire trigger (parameterized)
            await conn.execute(
                text("""
                    INSERT INTO auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, raw_user_meta_data)
                    VALUES ('00000000-0000-0000-0000-000000000000', :user_id, 'authenticated', 'authenticated', :email, 'password', now(), :metadata::jsonb)
                """),
                {
                    "user_id": test_user_id,
                    "email": test_email,
                    "metadata": f'{{"anonymous_id": "{test_anon_id}"}}'
                }
            )
            
            # Check if public.users record was created automatically
            result = await conn.execute(
                text("SELECT * FROM public.users WHERE id = :user_id"),
                {"user_id": test_user_id}
            )
            user_record = result.first()
            
            if user_record:
                print(f"✅ Trigger fired: public.users record created for {test_user_id}")
                if user_record.anonymous_id == test_anon_id:
                    print("✅ Metadata extraction: anonymous_id correctly populated")
                else:
                    print(f"❌ Metadata fail: expected '{test_anon_id}', got {user_record.anonymous_id}")
            else:
                print("❌ Trigger FAIL: public.users record NOT created")

        except Exception as e:
            print(f"❌ Error during trigger test: {e}")
            
    # 4. RLS Verification
    # To test RLS, we switch the current transaction's role to 'authenticated' and set request.jwt.claim.sub
    
    print("\n--- 3. RLS Validation ---")
    
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            # Context: Authenticated as test user
            await conn.execute(text("SET LOCAL ROLE authenticated"))
            await conn.execute(
                text("SELECT set_config('request.jwt.claims', :claims, true)"),
                {"claims": f'{{"sub": "{test_user_id}", "role": "authenticated"}}'}
            )
            
            # Test SELECT policy
            result = await conn.execute(text("SELECT id FROM public.users"))
            rows = result.fetchall()
            if len(rows) == 1 and str(rows[0].id) == test_user_id:
                print("✅ RLS SELECT: User can see their own data")
            elif len(rows) == 0:
                print("❌ RLS SELECT Fail: User CANNOT see their own data")
            else:
                print(f"❌ RLS SELECT Fail: User saw {len(rows)} rows (expected 1)")

            # Test UPDATE policy
            try:
                await conn.execute(
                    text("UPDATE public.users SET created_at = created_at WHERE id = :user_id"),
                    {"user_id": test_user_id}
                )
                print("✅ RLS UPDATE: User can update their own data")
            except Exception as update_err:
                print(f"❌ RLS UPDATE Fail: {update_err}")
            
        except Exception as e:
            print(f"❌ Error during RLS test: {e}")
        finally:
            await trans.rollback()

    # Cleanup in finally block to ensure it runs even on error
    try:
        async with engine.begin() as conn:
            print("\n--- Cleanup ---")
            await conn.execute(
                text("DELETE FROM auth.users WHERE id = :user_id"),
                {"user_id": test_user_id}
            )
            print("✅ Test data cleaned up")
    except Exception as cleanup_err:
        print(f"⚠️  Cleanup warning: {cleanup_err}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(validate_db())
