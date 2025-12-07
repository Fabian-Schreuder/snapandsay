-- Add needs_review column to dietary_logs table
-- This column flags logs that require human review due to low confidence

ALTER TABLE dietary_logs
ADD COLUMN IF NOT EXISTS needs_review BOOLEAN NOT NULL DEFAULT FALSE;

-- Add comment for documentation
COMMENT ON COLUMN dietary_logs.needs_review IS 'Flag indicating log requires human review due to low confidence analysis';
