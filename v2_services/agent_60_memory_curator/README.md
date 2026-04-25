# Agent 60 — Memory Curator

Centralized project memory with file access, full-text search, and timeline.

## Endpoints

- `GET /health` — health check
- `GET /memory/list?path=` — list directory
- `GET /memory/get?path=` — read file
- `POST /memory/write` — write file (body: path, content, overwrite)
- `POST /memory/append` — append to file (body: path, content)
- `GET /memory/search?q=&project=` — full-text search
- `GET /memory/timeline?project=&days=` — chronological events
- `POST /invoke` — unified action endpoint

## Port

8060
