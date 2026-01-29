-- Add title column to dietary_logs if it doesn't exist
ALTER TABLE dietary_logs ADD COLUMN IF NOT EXISTS title TEXT;

-- Add 'invalid' to log_status_enum
ALTER TYPE log_status_enum ADD VALUE IF NOT EXISTS 'invalid';
