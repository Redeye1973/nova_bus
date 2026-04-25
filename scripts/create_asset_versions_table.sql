CREATE TABLE IF NOT EXISTS asset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_logical_id TEXT NOT NULL,
    version_number INT NOT NULL,
    minio_path TEXT NOT NULL,
    content_hash TEXT,
    parent_version_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    UNIQUE(asset_logical_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_asset_logical ON asset_versions(asset_logical_id);
CREATE INDEX IF NOT EXISTS idx_asset_active ON asset_versions(asset_logical_id, is_active);
