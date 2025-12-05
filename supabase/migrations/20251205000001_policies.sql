-- Enable RLS
alter table public.users enable row level security;

-- Policy: Users can view own profile
create policy "Users can view own profile"
  on public.users
  for select
  using (auth.uid() = id);

-- Policy: Users can update own profile
create policy "Users can update own profile"
  on public.users
  for update
  using (auth.uid() = id);
