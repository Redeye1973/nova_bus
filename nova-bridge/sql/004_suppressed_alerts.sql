CREATE TABLE IF NOT EXISTS suppressed_alerts (
    id              BIGSERIAL PRIMARY KEY,
    suppressed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel         TEXT NOT NULL,
    alert_text      TEXT NOT NULL,
    reason          TEXT NOT NULL,
    quiet_mode_ttl  INT
);

CREATE INDEX IF NOT EXISTS idx_suppressed_recent ON suppressed_alerts(suppressed_at DESC);
