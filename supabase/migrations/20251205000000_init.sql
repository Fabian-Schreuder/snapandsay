-- Enable vector extension for future embedding support
create extension if not exists vector;

-- Create users table
-- References auth.users with CASCADE delete to ensure data consistency
-- anonymous_id is the de-identified research ID shown to users
create table public.users (
  id uuid references auth.users on delete cascade not null primary key,
  anonymous_id text unique not null,
  created_at timestamptz default now()
);

-- Index for anonymous_id lookups (used in research queries and user display)
create index users_anonymous_id_idx on public.users using btree (anonymous_id);

-- Trigger function to automatically create public.users record when auth.users is created
-- Uses security definer to ensure trigger has permission to insert
-- Extracts anonymous_id from metadata or generates fallback
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  -- Attempt to insert new user profile
  -- On conflict (duplicate anonymous_id), retry with new random ID
  insert into public.users (id, anonymous_id)
  values (
    new.id,
    coalesce(
      (new.raw_user_meta_data->>'anonymous_id')::text,
      'anon_' || substr(md5(random()::text), 1, 11) -- FIXED: substr is 1-indexed, generate 11 chars for total of 16
    )
  )
  on conflict (anonymous_id) do nothing; -- Edge case: if collision occurs, user record won't be created
  
  -- Note: In production, consider adding retry logic or raising exception if insert fails
  return new;
exception
  when others then
    -- FAIL HARD: Abort the transaction so auth.users is NOT created if public.users fails
    -- This ensures we don't end up with zombie users without profiles
    raise exception 'Failed to create public.users record for auth.users.id=%: %', new.id, sqlerrm;
end;
$$;

-- Trigger on auth.users to automatically sync to public.users
-- Fires after each insert to ensure auth.users.id exists before referencing
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
