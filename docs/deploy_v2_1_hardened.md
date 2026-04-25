# NOVA v2.1-hardened Deploy Report

- **Deploy timestamp:** 2026-04-25 09:17 – 09:50 CET
- **Branch merged:** `cursor/host-tools-daz-config-session-bundles` → `main`
- **Commits merged:** 21
- **Merge commit:** `d8dc749`
- **Tag:** `v2.1-hardened`

## Deploy resultaat

- Methode: SCP (per-agent file sync) + `docker compose build --parallel` + `docker compose up -d`
- Server: `178.104.207.194` (Hetzner)
- Container status: **52 up** / **52 healthy** / **0 unhealthy**
- Failed containers: geen (agent 33 had initieel `httpx` dependency issue, direct gefixt)
- Rollback gedaan: **nee**

### Gedeployde agents (13 bijgewerkt)

| Agent | Wijziging |
|-------|-----------|
| 11 Monitor | H06 pipeline observability |
| 12 Bake Orchestrator | H09 asset lineage tracking |
| 16 Cost Guard | H10 cost reporting aggregation |
| 17 Error Handler | H11 error pattern auto-learning |
| 18 Prompt Director | H13 prompt registry |
| 22 Blender Renderer | H07 bridge stub → proxy |
| 23 Aseprite Processor | H07 bridge stub → proxy |
| 25 PyQt Assembly | H07 bridge stub → proxy |
| 26 Godot Import | H07 bridge stub → proxy |
| 31 QGIS Analysis | H07 bridge stub → proxy |
| 32 GRASS GIS | H07 bridge stub → proxy |
| 33 Blender Arch Walkthrough | H07 bridge stub → proxy (nieuw op server) |
| 35 Raster 2D | H07 bridge stub → proxy |

## Health check

| Endpoint | Status |
|----------|--------|
| N8n V1 (5678) | 200 |
| N8n V2 (5679) | 200 |
| Agent 19 Distribution | 403 (auth required, normaal) |
| Overige agents | Docker-internal only (niet exposed op host) |

**Docker container health: 52/52 healthy**

## MinIO backup integratie

- mc client geinstalleerd: `RELEASE.2025-08-13`
- Aliases geconfigureerd: `local-minio` (port 9000), `minio-nova-v2-minio` (port 19000)
- Backup script (`/root/nova-backup.sh`) bijgewerkt: **ja**
- MinIO buckets momenteel: **leeg** (geen data om te mirroren)
- Zodra buckets data bevatten, wordt het automatisch meegenomen in Borg backups

## Fix tijdens deploy

- **Agent 33 crashte** op `ModuleNotFoundError: httpx`
  - Oorzaak: `requirements.txt` miste `httpx` dependency na bridge stub upgrade
  - Fix: `httpx>=0.27.0` toegevoegd, rebuild, restart → healthy

## Volgende stappen

- `HETZNER_SSH_KEY` toevoegen in GitHub Secrets (handmatig door Alex, voor GitHub Actions deploy)
- Audiocraft venv herinstalleren met Python 3.11 (optioneel, niet kritiek)
- MinIO buckets vullen met assets → backup pipeline test herhalen
