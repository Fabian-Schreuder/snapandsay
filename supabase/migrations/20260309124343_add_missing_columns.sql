ALTER TABLE dietary_logs ADD COLUMN clarification_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE dietary_logs ADD COLUMN ampm_data JSONB;
