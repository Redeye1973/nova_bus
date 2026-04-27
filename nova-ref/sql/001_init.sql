CREATE SCHEMA IF NOT EXISTS cache;
CREATE SCHEMA IF NOT EXISTS learn;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS cache.entities (
    id              TEXT PRIMARY KEY,
    category        TEXT NOT NULL,
    subcategory     TEXT,
    canonical_name  TEXT NOT NULL,
    aliases         TEXT[] DEFAULT '{}',
    source_refs     JSONB NOT NULL,
    dimensions      JSONB,
    materials       TEXT[] DEFAULT '{}',
    era             TEXT,
    context         TEXT,
    description     TEXT,
    license         TEXT NOT NULL,
    license_attrib  TEXT,
    raw_payload     JSONB,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL,
    fetch_count     INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_entities_category ON cache.entities(category, subcategory);
CREATE INDEX IF NOT EXISTS idx_entities_aliases  ON cache.entities USING GIN (aliases);
CREATE INDEX IF NOT EXISTS idx_entities_source   ON cache.entities USING GIN (source_refs);
CREATE INDEX IF NOT EXISTS idx_entities_expires  ON cache.entities(expires_at);

CREATE TABLE IF NOT EXISTS cache.queries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_query       TEXT NOT NULL,
    normalized      TEXT NOT NULL,
    category_hint   TEXT,
    matched_entity  TEXT REFERENCES cache.entities(id),
    confidence      FLOAT,
    used_adapters   TEXT[] DEFAULT '{}',
    duration_ms     INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_queries_normalized ON cache.queries(normalized);
CREATE INDEX IF NOT EXISTS idx_queries_created    ON cache.queries(created_at DESC);

CREATE TABLE IF NOT EXISTS cache.adapter_status (
    adapter_name    TEXT PRIMARY KEY,
    last_success    TIMESTAMPTZ,
    last_failure    TIMESTAMPTZ,
    failure_count   INT NOT NULL DEFAULT 0,
    avg_latency_ms  INT,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS cache.rate_limits (
    build_name      TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    limit_per_min   INT NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (build_name, endpoint)
);

CREATE TABLE IF NOT EXISTS learn.build_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_name      TEXT NOT NULL,
    build_version   TEXT,
    request_payload JSONB NOT NULL,
    used_entities   TEXT[] DEFAULT '{}',
    used_adapters   TEXT[] DEFAULT '{}',
    output_artifact TEXT,
    outcome         TEXT,
    quality_score   FLOAT,
    feedback_source TEXT,
    feedback_notes  TEXT,
    duration_ms     INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_build      ON learn.build_runs(build_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_outcome    ON learn.build_runs(outcome, quality_score);
CREATE INDEX IF NOT EXISTS idx_runs_entities   ON learn.build_runs USING GIN (used_entities);

CREATE TABLE IF NOT EXISTS learn.patterns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type    TEXT NOT NULL,
    build_name      TEXT,
    category        TEXT,
    conditions      JSONB NOT NULL,
    recommendation  JSONB NOT NULL,
    evidence_count  INT NOT NULL DEFAULT 1,
    confidence      FLOAT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_lookup ON learn.patterns(pattern_type, build_name, category);

CREATE TABLE IF NOT EXISTS learn.run_embeddings (
    run_id          UUID PRIMARY KEY REFERENCES learn.build_runs(id) ON DELETE CASCADE,
    embedding       vector(384) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
    ON learn.run_embeddings USING hnsw (embedding vector_cosine_ops);
