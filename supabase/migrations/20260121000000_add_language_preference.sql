-- Add language_preference column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS language_preference VARCHAR(5) NOT NULL DEFAULT 'nl';

COMMENT ON COLUMN users.language_preference IS 'User preferred language code (e.g., nl, en)';
