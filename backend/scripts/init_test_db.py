import asyncio
import os
import pathlib

import asyncpg

# Adjust path to point to root of repo from backend/scripts
ROOT_DIR = pathlib.Path(__file__).parent.parent.parent
MIGRATIONS_DIR = ROOT_DIR / "supabase" / "migrations"

# Get DB URL from env or use default from .env file inspection
# User's .env had: TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres_test
# asyncpg expects postgresql://
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres_test")
if "postgresql+asyncpg://" in TEST_DB_URL:
    TEST_DB_URL = TEST_DB_URL.replace("postgresql+asyncpg://", "postgresql://")


async def init_test_db():
    print(f"Initializing test database at {TEST_DB_URL}...")

    try:
        conn = await asyncpg.connect(TEST_DB_URL)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return

    try:
        # 1. Reset schema
        print("Resetting public schema...")
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE;")
        await conn.execute("CREATE SCHEMA public;")
        await conn.execute("GRANT ALL ON SCHEMA public TO postgres;")
        await conn.execute("GRANT ALL ON SCHEMA public TO public;")

        # 2. Reset extensions
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # 2.5 Cleanup potentially conflicting policies in storage schema
        print("Cleaning up storage policies...")
        await conn.execute(
            'DROP POLICY IF EXISTS "Authenticated users can upload raw files" ON storage.objects;'
        )
        await conn.execute('DROP POLICY IF EXISTS "Users can view their own raw files" ON storage.objects;')

        # 2.6 Create auth schema and users table if not exists (simulating Supabase Auth)
        print("Ensuring auth schema exists...")
        await conn.execute("DROP SCHEMA IF EXISTS auth CASCADE;")
        await conn.execute("CREATE SCHEMA auth;")
        # Minimal auth.users table for testing constraints
        await conn.execute("""
            CREATE TABLE auth.users (
                instance_id uuid,
                id uuid NOT NULL PRIMARY KEY,
                aud character varying(255),
                role character varying(255),
                email character varying(255),
                encrypted_password character varying(255),
                email_confirmed_at timestamp with time zone,
                invited_at timestamp with time zone,
                confirmation_token character varying(255),
                confirmation_sent_at timestamp with time zone,
                recovery_token character varying(255),
                recovery_sent_at timestamp with time zone,
                email_change_token_new character varying(255),
                email_change character varying(255),
                email_change_sent_at timestamp with time zone,
                last_sign_in_at timestamp with time zone,
                raw_app_meta_data jsonb,
                raw_user_meta_data jsonb,
                is_super_admin boolean,
                created_at timestamp with time zone,
                updated_at timestamp with time zone,
                phone character varying(255),
                phone_confirmed_at timestamp with time zone,
                phone_change character varying(255),
                phone_change_token character varying(255),
                phone_change_sent_at timestamp with time zone,
                confirmed_at timestamp with time zone,
                email_change_token_current character varying(255),
                email_change_confirm_status smallint,
                banned_until timestamp with time zone,
                reauthentication_token character varying(255),
                reauthentication_sent_at timestamp with time zone,
                is_sso_user boolean DEFAULT false NOT NULL,
                deleted_at timestamp with time zone
            );
        """)

        # Mock auth functions common in Supabase to read from request.jwt.claims setting
        # This allows tests to simulate auth context by setting current_setting('request.jwt.claims')
        await conn.execute("""
            CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS $$
            DECLARE
                claims jsonb;
                uid_text text;
            BEGIN
                BEGIN
                    claims := current_setting('request.jwt.claims', true)::jsonb;
                EXCEPTION WHEN OTHERS THEN
                    RETURN null;
                END;
                
                uid_text := claims->>'sub';
                IF uid_text IS NULL THEN
                    RETURN null;
                END IF;
                
                RETURN uid_text::uuid;
            END;
            $$ LANGUAGE plpgsql STABLE;

            CREATE OR REPLACE FUNCTION auth.role() RETURNS text AS $$
            DECLARE
                claims jsonb;
            BEGIN
                BEGIN
                    claims := current_setting('request.jwt.claims', true)::jsonb;
                EXCEPTION WHEN OTHERS THEN
                    RETURN null;
                END;
                
                RETURN coalesce(claims->>'role', 'anon');
            END;
            $$ LANGUAGE plpgsql STABLE;
        """)

        # 3. Apply migrations
        migration_files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")])

        for migration_file in migration_files:
            print(f"Applying migration: {migration_file}")
            file_path = MIGRATIONS_DIR / migration_file
            with open(file_path) as f:
                sql_content = f.read()

            try:
                # asyncpg execute supports multiple statements in a single string
                await conn.execute(sql_content)
            except Exception as e:
                print(f"Error applying {migration_file}: {e}")
                raise e

        # 4. Grant permissions to roles (critical for RLS)
        print("Granting table permissions...")
        await conn.execute("GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;")
        await conn.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;")
        await conn.execute(
            "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;"
        )
        await conn.execute("GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role;")

        print("Test database initialization complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_test_db())
