-- Add meal_type column to dietary_logs table
-- This column was added to the SQLAlchemy model but missing from migrations

ALTER TABLE dietary_logs
ADD COLUMN IF NOT EXISTS meal_type VARCHAR;
