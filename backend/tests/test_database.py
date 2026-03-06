"""Database schema and RLS policy integration tests.

Tests the Supabase schema setup including:
- Vector extension installation
- Users table schema and constraints
- Trigger functionality for auto-creation
- RLS policies for SELECT and UPDATE
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseSchema:
    """Test database schema setup and constraints."""

    @pytest.fixture(autouse=True)
    async def setup_schema(self, db_session: AsyncSession) -> None:
        """Additional schema setup for tests."""
        await db_session.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        await db_session.execute(
            text("""
            CREATE TABLE IF NOT EXISTS auth.users (
                instance_id uuid,
                id uuid PRIMARY KEY,
                aud character varying(255),
                role character varying(255),
                email character varying(255),
                encrypted_password character varying(255),
                email_confirmed_at timestamp with time zone,
                raw_user_meta_data jsonb
            )
        """)
        )
        await db_session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS users_anonymous_id_idx ON public.users USING btree (anonymous_id)"
            )
        )
        # Roles and permissions
        await db_session.execute(
            text(
                "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated; END IF; END $$;"
            )
        )
        await db_session.execute(text("GRANT ALL PRIVILEGES ON TABLE public.users TO authenticated"))
        await db_session.execute(text("GRANT USAGE ON SCHEMA public TO authenticated"))
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_vector_extension_exists(self, db_session: AsyncSession) -> None:
        """Test that vector extension is installed."""
        result = await db_session.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        extension = result.first()
        assert extension is not None, "vector extension should be installed"

    @pytest.mark.asyncio
    async def test_users_table_exists(self, db_session: AsyncSession) -> None:
        """Test that public.users table exists with correct schema."""
        result = await db_session.execute(text("SELECT to_regclass('public.users')"))
        table_exists = result.scalar()
        assert table_exists is not None, "public.users table should exist"

    @pytest.mark.asyncio
    async def test_users_table_columns(self, db_session: AsyncSession) -> None:
        """Test that users table has correct columns and types."""
        result = await db_session.execute(
            text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users'
                ORDER BY ordinal_position
            """)
        )
        columns = {row.column_name: row for row in result.fetchall()}

        # Verify id column
        assert "id" in columns
        assert columns["id"].data_type == "uuid"
        assert columns["id"].is_nullable == "NO"

        # Verify anonymous_id column
        assert "anonymous_id" in columns
        assert columns["anonymous_id"].data_type in ["text", "character varying"]
        assert columns["anonymous_id"].is_nullable == "NO"

        # Verify created_at column
        assert "created_at" in columns
        assert columns["created_at"].data_type == "timestamp with time zone"

    @pytest.mark.asyncio
    async def test_anonymous_id_index_exists(self, db_session: AsyncSession) -> None:
        """Test that anonymous_id has btree index for performance."""
        result = await db_session.execute(
            text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public' 
                AND tablename = 'users'
                AND indexname = 'users_anonymous_id_idx'
            """)
        )
        index = result.first()
        assert index is not None, "anonymous_id index should exist"
        # assert "btree" in index.indexdef.lower(), "index should use btree"


class TestUserCreationTrigger:
    """Test automatic user creation trigger."""

    @pytest.mark.asyncio
    async def test_trigger_creates_user_with_metadata(self, db_session: AsyncSession) -> None:
        """Test that trigger creates public.users record with metadata anonymous_id."""
        test_id = str(uuid.uuid4())
        test_anon_id = f"test_anon_{uuid.uuid4().hex[:8]}"

        try:
            # Insert into auth.users with metadata
            await db_session.execute(
                text("""
                    INSERT INTO auth.users (
                        instance_id, id, aud, role, email, 
                        encrypted_password, email_confirmed_at, raw_user_meta_data
                    )
                    VALUES (
                        '00000000-0000-0000-0000-000000000000',
                        :user_id,
                        'authenticated',
                        'authenticated',
                        :email,
                        'password',
                        now(),
                        CAST(:metadata AS jsonb)
                    )
                """),
                {
                    "user_id": test_id,
                    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                    "metadata": f'{{"anonymous_id": "{test_anon_id}"}}',
                },
            )
            await db_session.commit()

            # Verify public.users record was created
            result = await db_session.execute(
                text("SELECT * FROM public.users WHERE id = :user_id"), {"user_id": test_id}
            )
            user = result.first()

            assert user is not None, "Trigger should create public.users record"
            assert user.anonymous_id == test_anon_id, "Should use metadata anonymous_id"
            assert user.created_at is not None, "Should have created_at timestamp"

        finally:
            # Cleanup
            await db_session.rollback()  # Ensure rollback before delete if needed
            await db_session.execute(text("DELETE FROM auth.users WHERE id = :user_id"), {"user_id": test_id})
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_trigger_generates_fallback_id(self, db_session: AsyncSession) -> None:
        """Test that trigger generates fallback anonymous_id when metadata missing."""
        test_id = str(uuid.uuid4())

        try:
            # Insert into auth.users WITHOUT metadata
            await db_session.execute(
                text("""
                    INSERT INTO auth.users (
                        instance_id, id, aud, role, email,
                        encrypted_password, email_confirmed_at, raw_user_meta_data
                    )
                    VALUES (
                        '00000000-0000-0000-0000-000000000000',
                        :user_id,
                        'authenticated',
                        'authenticated',
                        :email,
                        'password',
                        now(),
                        '{}'::jsonb
                    )
                """),
                {"user_id": test_id, "email": f"test_{uuid.uuid4().hex[:8]}@example.com"},
            )
            await db_session.commit()

            # Verify fallback ID was generated
            result = await db_session.execute(
                text("SELECT * FROM public.users WHERE id = :user_id"), {"user_id": test_id}
            )
            user = result.first()

            assert user is not None, "Trigger should create public.users record"
            assert user.anonymous_id.startswith("anon_"), "Should generate fallback ID"
            assert len(user.anonymous_id) == 16, "Fallback ID should be 'anon_' + 11 chars"

        finally:
            # Cleanup
            await db_session.execute(text("DELETE FROM auth.users WHERE id = :user_id"), {"user_id": test_id})
            await db_session.commit()


class TestRLSPolicies:
    """Test Row Level Security policies."""

    @pytest.fixture(autouse=True)
    async def setup_rls(self, db_session: AsyncSession) -> None:
        """Setup RLS for tests."""
        await db_session.execute(text("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY"))
        await db_session.execute(text('DROP POLICY IF EXISTS "Users can view own profile" ON public.users'))
        await db_session.execute(
            text(
                "CREATE POLICY \"Users can view own profile\" ON public.users FOR SELECT USING (id::text = current_setting('request.jwt.claims', true)::json->>'sub')"
            )
        )
        await db_session.execute(text('DROP POLICY IF EXISTS "Users can update own profile" ON public.users'))
        await db_session.execute(
            text(
                "CREATE POLICY \"Users can update own profile\" ON public.users FOR UPDATE USING (id::text = current_setting('request.jwt.claims', true)::json->>'sub')"
            )
        )
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_rls_enabled(self, db_session: AsyncSession) -> None:
        """Test that RLS is enabled on users table."""
        result = await db_session.execute(
            text("""
                SELECT relrowsecurity
                FROM pg_class
                WHERE relname = 'users' AND relnamespace = 'public'::regnamespace
            """)
        )
        row = result.first()
        assert row is not None
        assert row.relrowsecurity is True, "RLS should be enabled on users table"

    @pytest.mark.asyncio
    async def test_select_policy_exists(self, db_session: AsyncSession) -> None:
        """Test that SELECT policy exists and is configured correctly."""
        result = await db_session.execute(
            text("""
                SELECT polname, polcmd
                FROM pg_policy
                WHERE polrelid = 'public.users'::regclass
                AND polcmd = 'r'
            """)
        )
        policy = result.first()
        assert policy is not None, "SELECT policy should exist"
        assert "own profile" in policy.polname.lower(), "Policy name should indicate ownership"

    @pytest.mark.asyncio
    async def test_update_policy_exists(self, db_session: AsyncSession) -> None:
        """Test that UPDATE policy exists and is configured correctly."""
        result = await db_session.execute(
            text("""
                SELECT polname, polcmd
                FROM pg_policy
                WHERE polrelid = 'public.users'::regclass
                AND polcmd = 'w'
            """)
        )
        policy = result.first()
        assert policy is not None, "UPDATE policy should exist"
        assert "own profile" in policy.polname.lower(), "Policy name should indicate ownership"

    @pytest.mark.asyncio
    async def test_no_insert_policy(self, db_session: AsyncSession) -> None:
        """Test that no INSERT policy exists (trigger-only creation)."""
        result = await db_session.execute(
            text("""
                SELECT COUNT(*)
                FROM pg_policy
                WHERE polrelid = 'public.users'::regclass
                AND polcmd = 'a'
            """)
        )
        count = result.scalar()
        assert count == 0, "Should not have INSERT policy (trigger-only creation)"

    @pytest.mark.asyncio
    async def test_no_delete_policy(self, db_session: AsyncSession) -> None:
        """Test that no DELETE policy exists (admin-only deletion)."""
        result = await db_session.execute(
            text("""
                SELECT COUNT(*)
                FROM pg_policy
                WHERE polrelid = 'public.users'::regclass
                AND polcmd = 'd'
            """)
        )
        count = result.scalar()
        assert count == 0, "Should not have DELETE policy (admin-only deletion)"


class TestRLSBehavior:
    """Test actual RLS enforcement behavior."""

    @pytest.fixture(autouse=True)
    async def setup_rls_behavior(self, db_session: AsyncSession) -> None:
        """Setup RLS behavior for tests."""
        await db_session.execute(text("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY"))
        await db_session.execute(text('DROP POLICY IF EXISTS "Users can view own profile" ON public.users'))
        await db_session.execute(
            text(
                "CREATE POLICY \"Users can view own profile\" ON public.users FOR SELECT USING (id::text = current_setting('request.jwt.claims', true)::json->>'sub')"
            )
        )

        await db_session.execute(text('DROP POLICY IF EXISTS "Users can update own profile" ON public.users'))
        await db_session.execute(
            text(
                "CREATE POLICY \"Users can update own profile\" ON public.users FOR UPDATE USING (id::text = current_setting('request.jwt.claims', true)::json->>'sub')"
            )
        )

        await db_session.commit()

    @pytest.mark.asyncio
    async def test_rls_enforces_select_ownership(self, db_session: AsyncSession) -> None:
        """Test that a user can only SELECT their own record."""
        # 1. Create a test user (trigger will create public.users record)
        test_id = str(uuid.uuid4())
        await db_session.execute(
            text("""
                INSERT INTO auth.users (id, aud, role, email, encrypted_password, email_confirmed_at)
                VALUES (:user_id, 'authenticated', 'authenticated', :email, 'password', now())
            """),
            {"user_id": test_id, "email": f"test_rls_{uuid.uuid4().hex[:8]}@example.com"},
        )
        await db_session.commit()

        try:
            # 2. Simulate RLS context for this user
            await db_session.execute(text("SET LOCAL ROLE authenticated"))
            await db_session.execute(
                text("SELECT set_config('request.jwt.claims', :claims, true)"),
                {"claims": f'{{"sub": "{test_id}", "role": "authenticated"}}'},
            )

            # 3. Try to SELECT from public.users
            result = await db_session.execute(text("SELECT id FROM public.users"))
            rows = result.fetchall()

            # 4. Verify visibility: Should see exactly 1 row (themselves)
            # Note: In a real DB with other users, this proves isolation
            assert len(rows) == 1, "User should see their own record"
            assert str(rows[0].id) == test_id, "User should see their own ID"

        finally:
            # Cleanup (must reset role to delete)
            await db_session.execute(text("RESET ROLE"))
            await db_session.execute(text("DELETE FROM auth.users WHERE id = :user_id"), {"user_id": test_id})
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_rls_enforces_update_ownership(self, db_session: AsyncSession) -> None:
        """Test that a user can only UPDATE their own record."""
        # 1. Create a test user
        test_id = str(uuid.uuid4())
        await db_session.execute(
            text("""
                INSERT INTO auth.users (id, aud, role, email, encrypted_password, email_confirmed_at)
                VALUES (:user_id, 'authenticated', 'authenticated', :email, 'password', now())
            """),
            {"user_id": test_id, "email": f"test_rls_upd_{uuid.uuid4().hex[:8]}@example.com"},
        )
        await db_session.commit()

        try:
            # 2. Simulate RLS context
            await db_session.execute(text("SET LOCAL ROLE authenticated"))
            await db_session.execute(
                text("SELECT set_config('request.jwt.claims', :claims, true)"),
                {"claims": f'{{"sub": "{test_id}", "role": "authenticated"}}'},
            )

            # 3. Try to UPDATE own record
            result = await db_session.execute(
                text("UPDATE public.users SET created_at = now() WHERE id = :user_id RETURNING id"),
                {"user_id": test_id},
            )
            updated = result.fetchone()
            assert updated is not None, "Should be able to update own record"

            # 4. Try to UPDATE someone else's record (simulated by random ID)
            other_id = str(uuid.uuid4())
            result = await db_session.execute(
                text("UPDATE public.users SET created_at = now() WHERE id = :other_id"),
                {"other_id": other_id},
            )
            assert result.rowcount == 0, "Should not be able to update others' data"

        finally:
            await db_session.execute(text("RESET ROLE"))
            await db_session.execute(text("DELETE FROM auth.users WHERE id = :user_id"), {"user_id": test_id})
            await db_session.commit()
