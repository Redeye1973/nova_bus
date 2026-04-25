# Current Baseline - NOVA V2

**Last update:** 2026-04-22 (sessie 09 — production handoff)  
**Status:** **V2 productie-baseline** (code + Compose + pipeline masters; Hetzner backup-cron = handwerk op server).

## Samenvatting

- **Agents:** 35 logische services (01 = `sprite_jury`, 02–35 onder `v2_services` / compose).  
- **Operationeel / POC:** jury’s, monitor, cost guard, bake orchestratie, PDOK, story/asset agents, enz.  
- **Bridge-stubs (503 / pending_full_bridge):** 22, 23, 25, 26, 31, 32, 33, 35 (+ 14/15 bake/QGIS paden grotendeels stub).  
- **Pipelines F:** master JSON in `pipelines/` + `scripts/run_pipeline_validation.py` + Postgres DDL `scripts/create_session08_pipeline_tables.sql`.  
- **Backup:** sjablonen in `scripts/hetzner_backup_cron_templates.sh` (pg_dump → MinIO, mirror, weekly config tarball).

## Infrastructure (referentie)

- **V2 N8n:** `http://178.104.207.194:5679`  
- **PostgreSQL / Redis / MinIO / Qdrant:** compose stack op Hetzner  
- **NOVA Host Bridge:** Tailscale naar dev PC (`nova_config.yaml` + `nova_host_bridge/`)

## Documentatie

| Document | Doel |
|----------|------|
| `docs/V2_BUILD_COMPLETE_REPORT.md` | Volledig build-overzicht (sessie 09) |
| `docs/session_08_report.md` | Pipeline-validatie |
| `bridge/.../shared_state/to_build.md` | Openstaand werk |

## Secrets & paden

- `L:\!Nova V2\secrets\nova_v2_passwords.txt`  
- `L:\!Nova V2\infrastructure\docker-compose.yml`  
- Server: `/docker/nova-v2/docker-compose.yml`

## Volgende stap

1. Server: backup-cron installeren (`hetzner_backup_cron_templates.sh`).  
2. N8n: `pipeline_*_master` importeren.  
3. Bridge: stubs afwerken volgens `to_build.md`.
