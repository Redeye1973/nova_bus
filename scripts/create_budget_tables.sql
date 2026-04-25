CREATE TABLE IF NOT EXISTS pipeline_budgets (
    pipeline_type TEXT PRIMARY KEY,
    max_cost_usd DECIMAL(10,4),
    max_duration_seconds INT,
    max_gpu_seconds INT DEFAULT 0,
    max_api_calls INT DEFAULT 100,
    notify_threshold_pct INT DEFAULT 80
);

INSERT INTO pipeline_budgets VALUES
    ('shmup_sprite', 0.50, 600, 30, 100, 80),
    ('story_chapter', 0.30, 300, 0, 50, 80),
    ('bake_postcode', 1.00, 1200, 0, 200, 80)
ON CONFLICT (pipeline_type) DO NOTHING;

CREATE TABLE IF NOT EXISTS pipeline_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id TEXT NOT NULL,
    pipeline_type TEXT NOT NULL,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    api_calls INT DEFAULT 0,
    gpu_seconds INT DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_pipeline ON pipeline_usage(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_usage_type ON pipeline_usage(pipeline_type);
