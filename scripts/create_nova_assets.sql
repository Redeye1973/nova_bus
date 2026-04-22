CREATE TABLE IF NOT EXISTS nova_assets (
  asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_type TEXT NOT NULL,
  path TEXT NOT NULL,
  producer_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  judge_score NUMERIC,
  judge_verdict TEXT,
  metadata JSONB
);
CREATE INDEX IF NOT EXISTS idx_assets_type_verdict ON nova_assets(asset_type, judge_verdict);
