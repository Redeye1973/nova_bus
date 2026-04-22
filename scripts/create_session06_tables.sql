-- Session 06 — operational core (bake_jobs + cost_log) in n8n_v2 Postgres.
-- Apply: docker cp ... && docker exec nova-v2-postgres psql -U postgres -d n8n_v2 -f /tmp/create_session06_tables.sql

CREATE TABLE IF NOT EXISTS bake_jobs (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  postcode TEXT NOT NULL,
  layers JSONB NOT NULL DEFAULT '[]'::jsonb,
  state TEXT NOT NULL DEFAULT 'queued',
  progress INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  payload JSONB,
  last_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_bake_jobs_state ON bake_jobs(state);

CREATE TABLE IF NOT EXISTS cost_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMP DEFAULT NOW(),
  service TEXT NOT NULL,
  operation TEXT,
  estimated_cost_eur NUMERIC,
  actual_cost_eur NUMERIC,
  agent_id TEXT,
  metadata JSONB
);
CREATE INDEX IF NOT EXISTS idx_cost_log_service_ts ON cost_log(service, timestamp DESC);
