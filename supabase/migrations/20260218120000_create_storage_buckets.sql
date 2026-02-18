-- Create raw_uploads bucket if it doesn't exist
insert into storage.buckets (id, name, public)
values ('raw_uploads', 'raw_uploads', true)
on conflict (id) do nothing;

-- Set up security policies for the bucket
-- Allow public access to read (for debugging/verification if needed, though strictly signed URLs are safer)
create policy "Public Access"
  on storage.objects for select
  using ( bucket_id = 'raw_uploads' );

-- Allow authenticated users to upload files
create policy "Authenticated users can upload"
  on storage.objects for insert
  with check ( bucket_id = 'raw_uploads' and auth.role() = 'authenticated' );

-- Allow users to update their own files (optional, depending on flow)
create policy "Users can update own files"
  on storage.objects for update
  using ( bucket_id = 'raw_uploads' and auth.uid() = owner );
