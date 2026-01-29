-- Create research_logs table for research metrics tracking
CREATE TABLE research_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id UUID NOT NULL UNIQUE REFERENCES dietary_logs(id) ON DELETE CASCADE,
    
    -- Research Metrics
    input_modality VARCHAR NOT NULL,  -- 'voice', 'photo', 'text'
    processing_time_ms INTEGER NOT NULL,
    agent_turns_count INTEGER NOT NULL,
    was_corrected BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_score FLOAT NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on log_id for foreign key lookups
CREATE INDEX idx_research_logs_log_id ON research_logs(log_id);

-- RLS (same pattern as dietary_logs - users can only see their own research logs via the dietary_log relationship)
ALTER TABLE research_logs ENABLE ROW LEVEL SECURITY;

-- Note: Access control is enforced through the dietary_logs relationship
-- Users access research_logs via their dietary_logs, which already have RLS policies
CREATE POLICY "Users can view research logs for their own dietary logs"
    ON research_logs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM dietary_logs 
            WHERE dietary_logs.id = research_logs.log_id 
            AND dietary_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert research logs for their own dietary logs"
    ON research_logs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM dietary_logs 
            WHERE dietary_logs.id = research_logs.log_id 
            AND dietary_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update research logs for their own dietary logs"
    ON research_logs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM dietary_logs 
            WHERE dietary_logs.id = research_logs.log_id 
            AND dietary_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete research logs for their own dietary logs"
    ON research_logs FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM dietary_logs 
            WHERE dietary_logs.id = research_logs.log_id 
            AND dietary_logs.user_id = auth.uid()
        )
    );
