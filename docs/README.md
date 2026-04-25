---
created: 2026-04-25
type: reference
status: active
---

# NOVA v2 Documentation

## Structuur

| Folder | Inhoud |
|--------|--------|
| `architecture/` | Architectuur docs, pipeline flows, ADRs |
| `architecture/pipelines/` | Per-pipeline flow documentatie |
| `architecture/decisions/` | Architecture Decision Records (ADR) |
| `projects/` | Per-project docs (canon, design, assets, progress) |
| `projects/black_ledger/` | Black Ledger v4 shmup |
| `projects/surilians/` | Surilians manuscript |
| `projects/tyriankloon/` | TyrianKloon Hoogeveen |
| `sessions/` | Sessie logs en chat archieven |
| `sessions/cursor_reports/` | Auto-gegenereerde Cursor sessie rapporten |
| `sessions/claude_chats/` | Handmatig geexporteerde Claude.ai chats |
| `reference/` | Tool configs, API inventaris, infra snapshots |

## Conventies

- Bestandsnaam: `snake_case.md`
- Sessie bestanden: `YYYY-MM-DD_topic_slug.md`
- YAML frontmatter met `created`, `project`, `type`, `status`
- ADR naming: `ADR-NNN-short-description.md`
