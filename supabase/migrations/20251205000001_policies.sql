-- Enable Row Level Security on users table
-- This ensures users can only access their own data
alter table public.users enable row level security;

-- Policy: Users can view own profile
-- Allows SELECT operations only for records where auth.uid() matches the user's id
create policy "Users can view own profile"
  on public.users
  for select
  using (auth.uid() = id);

-- Policy: Users can update own profile
-- Allows UPDATE operations only for records where auth.uid() matches the user's id
create policy "Users can update own profile"
  on public.users
  for update
  using (auth.uid() = id);

-- Policy: Prevent user-initiated inserts (trigger-only creation)
-- No INSERT policy means users cannot directly insert into public.users
-- Profile creation is handled exclusively by the handle_new_user trigger
-- This ensures data integrity and consistent user creation flow

-- Policy: Prevent user-initiated deletes (admin-only via service role)
-- No DELETE policy means authenticated users cannot delete their own profiles
-- Profile deletion, if needed, should be handled by admin/service role
-- This aligns with research data retention requirements

-- Note: Service role bypasses RLS and can perform all operations
-- Use service role key for admin operations and data export
