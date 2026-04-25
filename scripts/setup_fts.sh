#!/bin/bash
echo "=== Creating FTS table ==="
docker exec nova-v2-postgres psql -U postgres -d n8n_v2 << 'SQL'
CREATE TABLE IF NOT EXISTS memory_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT UNIQUE NOT NULL,
    project TEXT,
    doc_type TEXT,
    title TEXT,
    content TEXT NOT NULL,
    last_modified TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT NOW(),
    search_vector TSVECTOR
);

CREATE INDEX IF NOT EXISTS memory_search_idx ON memory_index USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS memory_project_idx ON memory_index(project);

CREATE OR REPLACE FUNCTION memory_search_trigger() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', coalesce(NEW.title, '') || ' ' || coalesce(NEW.content, ''));
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS memory_search_update ON memory_index;
CREATE TRIGGER memory_search_update
    BEFORE INSERT OR UPDATE ON memory_index
    FOR EACH ROW EXECUTE FUNCTION memory_search_trigger();

SELECT 'FTS table ready' AS status;
SQL

echo ""
echo "=== Running initial index ==="
docker exec nova-v2-memory-curator python /app/index_docs.py 2>&1

echo ""
echo "=== Verifying index ==="
docker exec nova-v2-postgres psql -U postgres -d n8n_v2 -c "SELECT count(*) as docs_indexed FROM memory_index;"

echo ""
echo "=== Test search ==="
docker exec nova-v2-postgres psql -U postgres -d n8n_v2 -c "SELECT file_path, title FROM memory_index WHERE search_vector @@ plainto_tsquery('english', 'pipeline') LIMIT 5;"

echo ""
echo "=== Setup hourly reindex cron ==="
CRON_LINE="0 * * * * docker exec nova-v2-memory-curator python /app/index_docs.py >> /var/log/nova-backup/memory-index.log 2>&1"
if ! crontab -l 2>/dev/null | grep -q "memory-index"; then
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
  echo "Cron added for hourly reindex"
else
  echo "Cron already exists"
fi
