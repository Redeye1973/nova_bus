"""Scan docs/ and update Postgres FTS index."""

import os
import re
from pathlib import Path
from datetime import datetime

try:
    import psycopg2
except ImportError:
    psycopg2 = None

DOCS_ROOT = Path(os.getenv("DOCS_ROOT", "/docs"))
DB_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@nova-v2-postgres:5432/n8n_v2")


def extract_metadata(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    metadata = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            metadata[k.strip()] = v.strip()
    return metadata


def index_all():
    if psycopg2 is None:
        print("psycopg2 not available, skipping DB indexing")
        return

    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()

    indexed = 0
    for md_file in DOCS_ROOT.rglob("*.md"):
        rel_path = str(md_file.relative_to(DOCS_ROOT))
        try:
            content = md_file.read_text(encoding="utf-8")
            metadata = extract_metadata(content)

            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem

            project = metadata.get("project")
            if not project:
                parts = rel_path.split("/")
                if parts[0] == "projects" and len(parts) > 1:
                    project = parts[1]

            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)

            cur.execute("""
                INSERT INTO memory_index (file_path, project, doc_type, title, content, last_modified)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_path) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    last_modified = EXCLUDED.last_modified,
                    indexed_at = NOW()
            """, (rel_path, project, metadata.get("type"), title, content, mtime))
            indexed += 1
        except Exception as e:
            print(f"Error indexing {rel_path}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Indexed {indexed} docs")


if __name__ == "__main__":
    index_all()
