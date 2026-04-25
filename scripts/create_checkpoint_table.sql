CREATE TABLE IF NOT EXISTS pipeline_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id TEXT NOT NULL,
    stage_name TEXT NOT NULL,
    stage_index INT DEFAULT 0,
    stage_state JSONB DEFAULT '{}',
    output_refs JSONB DEFAULT '{}',
    completed_at TIMESTAMP DEFAULT NOW(),
    can_resume BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_checkpoint_run ON pipeline_checkpoints(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_stage ON pipeline_checkpoints(pipeline_run_id, stage_index);
