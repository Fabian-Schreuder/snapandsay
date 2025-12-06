-- Create Enum
CREATE TYPE log_status_enum AS ENUM ('processing', 'clarification', 'logged');

-- Create Table
CREATE TABLE dietary_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    audio_path TEXT,
    transcript TEXT,
    description TEXT,
    calories INTEGER,
    protein INTEGER,
    carbs INTEGER,
    fats INTEGER,
    status log_status_enum NOT NULL DEFAULT 'processing',
    client_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_dietary_logs_user_id ON dietary_logs(user_id);
CREATE INDEX idx_dietary_logs_created_at ON dietary_logs(created_at);

-- RLS
ALTER TABLE dietary_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own logs"
    ON dietary_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own logs"
    ON dietary_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own logs"
    ON dietary_logs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own logs"
    ON dietary_logs FOR DELETE
    USING (auth.uid() = user_id);

-- Storage
INSERT INTO storage.buckets (id, name, public) 
VALUES ('raw_uploads', 'raw_uploads', false)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Authenticated users can upload raw files"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'raw_uploads' AND 
    (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can view their own raw files"
ON storage.objects FOR SELECT TO authenticated
USING (
    bucket_id = 'raw_uploads' AND 
    (storage.foldername(name))[1] = auth.uid()::text
);
