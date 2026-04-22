-- Session 08 — pipeline validation metrics (Postgres)
CREATE TABLE IF NOT EXISTS pipeline_runs (
  run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline_name TEXT NOT NULL,
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  total_steps INT,
  completed_steps INT,
  pending_bridge_steps INT,
  failed_steps INT,
  total_latency_ms BIGINT,
  judge_scores JSONB,
  final_verdict TEXT,
  input_payload JSONB,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_step_logs (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
  step_order INT,
  agent_name TEXT,
  started_at TIMESTAMP,
  latency_ms INT,
  response_code INT,
  verdict TEXT,
  output_excerpt TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_step_logs_run ON pipeline_step_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_name_started ON pipeline_runs(pipeline_name, started_at DESC);
