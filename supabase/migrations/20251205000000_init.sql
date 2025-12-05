-- Enable vector extension
create extension if not exists vector;

-- Create users table
create table public.users (
  id uuid references auth.users on delete cascade not null primary key,
  anonymous_id text unique not null,
  created_at timestamptz default now()
);

-- Index for anonymous_id
create index users_anonymous_id_idx on public.users using btree (anonymous_id);

-- Trigger function to handle new user creation
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.users (id, anonymous_id)
  values (
    new.id,
    coalesce(
      (new.raw_user_meta_data->>'anonymous_id')::text,
      'anon_' || substr(md5(random()::text), 0, 12) -- Fallback random ID
    )
  );
  return new;
end;
$$;

-- Trigger on auth.users
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
