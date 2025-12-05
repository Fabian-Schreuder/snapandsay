# Story 1.2: Database & Supabase Configuration

Status: Done

## Story

As a developer,
I want to set up the Supabase project and database schema,
So that we can store user data securely.

## Acceptance Criteria

1.  **Given** A Supabase project is initialized (local)
    **When** I run the migration scripts
    **Then** The `users` table exists with `id` (UUID), `anonymous_id` (String), and `created_at`
2.  **And** The `pgvector` extension is enabled via migration
3.  **And** RLS policies are enforced on the `users` table to allow access only to the owning user
4.  **And** The public `users` table record is **automatically created** upon sign-up via an internal Postgres Trigger (no client-side insert)

## Tasks / Subtasks

- [x] Task 1: Supabase Migration (AC: 1, 2)
    - [x] Create `supabase/migrations/0000_init.sql`
    - [x] Enable `vector` extension
    - [x] Define `users` table
        - `id`: UUID, Primary Key, references `auth.users.id` on delete cascade
        - `anonymous_id`: Text, Unique, Not Null (Research ID)
        - `created_at`: Timestamptz, Default `now()`
    - [x] Create Index on `anonymous_id` (btree) for fast lookups
    - [x] Create Trigger Function `public.handle_new_user()`
        - Insert into `public.users` (`id`, `anonymous_id`) when new `auth.users` created
        - Generate `anonymous_id` if not present (or pass from metadata)
    - [x] Create Trigger `on_auth_user_created`
        - Execute `handle_new_user` after insert on `auth.users`
- [x] Task 2: Security & Policies (AC: 3, 4)
    - [x] Enable RLS on `users` table
    - [x] Add Policy: "Users can view own profile" (`select` using `auth.uid()`)
    - [x] Add Policy: "Users can update own profile" (`update` using `auth.uid()`)
    - [x] Verify Policy: "Service Role can manage all" (Implicit, but ensure no blocking policies)
- [x] Task 3: Verification
    - [x] Run `supabase db reset` locally to verify migration matches schema
    - [x] Verify `users` table allows RLS protected access

## Dev Notes

- **Migration Standards:**
    - Use pure SQL in `supabase/migrations/`.
    - Do NOT use Alembic or other Python ORM migration tools for schema changes (Architecture Decision).
- **Table Design:**
    - `public.users` is a mirror/extension of `auth.users`.
    - **Trigger Requirement:** User creation MUST be handled by a Database Trigger on `auth.users`. Client-side creation is forbidden to ensure data integrity and security.
    - `anonymous_id` is the de-identified ID used for research purposes/UI display.
    - **Indexing:** `anonymous_id` must be indexed.
- **References:**
    - [Architecture: Data Architecture](docs/architecture.md#data-architecture)
    - [Architecture: Naming Patterns](docs/architecture.md#naming-patterns)
    - [Epics: Story 1.2](docs/epics.md#story-12-database--supabase-configuration)

### Project Structure Notes

- **Supabase Root:** `supabase/`
- **Migrations:** `supabase/migrations/`

## Dev Agent Record

### Context Reference

- **Architecture:** `docs/architecture.md`
- **Epics:** `docs/epics.md`
- **Previous Story:** `docs/sprint-artifacts/1-1-project-initialization-repo-setup.md`

### Agent Model Used

- Agentic Mode (Sm Agent)

### One-Shot File List

#### [NEW] [20251205000000_init.sql](file:///home/fabian/dev/work/snapandsay/supabase/migrations/20251205000000_init.sql)
#### [NEW] [20251205000001_policies.sql](file:///home/fabian/dev/work/snapandsay/supabase/migrations/20251205000001_policies.sql)
#### [MODIFY] [validate_db.py](file:///home/fabian/dev/work/snapandsay/scripts/validate_db.py)
#### [MODIFY] [config.toml](file:///home/fabian/dev/work/snapandsay/supabase/config.toml)

### Completion Notes List

- [x] Created migration files for users table and RLS policies
- [x] Enabled vector extension
- [x] Configured users table with RLS and triggers
- [x] Verified local migration application with `npx supabase db reset`
- [x] Validated schema and extensions using Python script `validate_db.py`
