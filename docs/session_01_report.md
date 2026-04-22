# Sessie 01 Rapport

- **Timestamp:** 2026-04-22 (update)
- **V1 API key toegevoegd:** **ja** — inhoud uit `L:\!Nova V2\secrets\N8n WorkHorse.txt` naar regel `N8N_V1_API_KEY=` in `nova_v2_passwords.txt` gezet (niet in git).
- **V1 connectivity test:** **68** workflows via `GET /api/v1/workflows?limit=100` op `:5678` (`meets_50: True`).
- **V2 API key aanwezig:** **ja** (`N8N_V2_API_KEY=` in `nova_v2_passwords.txt`).
- **V2 connectivity test:** niet opnieuw in deze stap gedraaid.
- **Script:** `scripts/v1_workflow_count.py` gebruikt nu `limit=100` (hogere limit gaf **400** op deze n8n-versie).
- **Status:** **SUCCESS**
- **Next session klaar: 02 (Bridge fix):** **JA** (bridge was eerder al online; desgewenst alleen verifiëren).

## Bestanden in `L:\!Nova V2\secrets`

- **`nova_v2_passwords.txt`** — **canoniek** voor Cursor/scripts (`N8N_V1_API_KEY`, `N8N_V2_API_KEY`, URL-regels, overige secrets).
- **`N8n WorkHorse.txt`** — **alleen backup** van dezelfde V1 key; niet meer als bron voor merges tenzij je bewust herstelt. Sync handmatig als je de key in n8n roteert.
- `N8n Key.txt` — apart houden voor V2 of andere doeleinden indien nodig.
