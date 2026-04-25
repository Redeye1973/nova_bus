CREATE TABLE IF NOT EXISTS software_test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    description TEXT,
    output_dir TEXT,
    status TEXT,
    total_tools INT,
    passed INT,
    failed INT,
    skipped INT,
    is_baseline BOOLEAN DEFAULT FALSE,
    compared_with_run_id TEXT,
    diff_count INT
);

CREATE TABLE IF NOT EXISTS software_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    tool_category TEXT,
    status TEXT,
    duration_ms INT,
    output_path TEXT,
    output_size_bytes INT,
    output_hash TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS softtest_run_idx ON software_test_results(run_id);
CREATE INDEX IF NOT EXISTS softtest_tool_idx ON software_test_results(tool_name);

CREATE TABLE IF NOT EXISTS software_test_diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT NOT NULL,
    baseline_run_id TEXT,
    tool_name TEXT,
    diff_type TEXT,
    diff_value DECIMAL,
    threshold DECIMAL,
    severity TEXT,
    metadata JSONB DEFAULT '{}'
);
