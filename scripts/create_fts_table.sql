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
