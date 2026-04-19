# Current Baseline - NOVA V2

**Last update**: 2026-04-19 by Cursor  
**Updated by**: Cursor (host bridge wired, Agent 21 promoted to real FreeCAD)

## Actieve agents (verified E2E)

| Agent | Name | Webhook | Response time | Notes |
|-------|------|---------|---------------|-------|
| 01 | Sprite Jury POC | /webhook/sprite-review-poc | 174ms | Verdict: accept (placeholder) |
| 02 | Code Jury | /webhook/code-review | 354ms | Full jury: radon + pycodestyle + bandit + GDScript |
| 10 | Game Balance Jury | /webhook/balance-review | 82ms | Reject verdict op minimal payload (correct) |
| 11 | Monitor | /webhook/monitor | <100ms | Sweeps peers, Prometheus /metrics, in-mem alerts |
| 17 | Error Handler | /webhook/error-handler | <100ms | YAML pattern classifier, retry plans, in-mem ledger |
| 20 | Design Fase | /webhook/design-fase | 78ms | 32-color palette + 3 faction palettes |
| 21 | FreeCAD Parametric | /webhook/freecad-parametric | ~560ms | Real FreeCAD 1.0.2 via host bridge over Tailscale; STEP+STL+FCStd; trimesh fallback |

## Stub agents (containers healthy, logica leeg)

26 agents: 03, 04, 05, 06, 07, 08, 09, 12, 13, 14, 15, 16, 18, 19, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 35

## Infrastructure

- **V2 N8n**: http://178.104.207.194:5679 (Up, healthcheck added)
- **V2 Webhook**: http://178.104.207.194:5680 (Up)
- **PostgreSQL**: healthy
- **Redis**: healthy
- **MinIO**: healthy, ports 19000/19001
- **Qdrant**: Up
- **NOVA Host Bridge**: http://100.64.0.2:8500 on PC `alex-main-1` over Tailscale, exposes FreeCAD 1.0.2 + QGIS 3.40.13 LTR. Hetzner -> bridge `/health`: ~120 ms; FreeCAD parametric: ~430-560 ms incl. STEP export.

## V1 status (baseline, niet aangeraakt)

- Poort 5678
- 68 productieworkflows
- Up 2+ dagen
- MCP integratie met Cursor werkt

## Bekende issues (niet blockers)

1. Agent 20 `industrial_neutral` thema mist entry in palette_manager.py theme_hues, valt terug op default hue 220. Low priority polish.
2. N8n services hebben nu een healthcheck. Geen actie nodig.
3. Bridge is single-point: als de PC offline is, valt agent 21 transparent terug op trimesh (geen STEP). Acceptabel voor nu.
4. Bridge files zijn alleen via PC bereikbaar (op Tailnet). Voor cross-Hetzner artifact-handoff moeten we ze later naar MinIO uploaden.

## Resources

- Pipeline Build package: L:\!Nova V2\pipelines\nova_v2_pipeline_build\nova_v2_pipeline_build\
- Status files: L:\!Nova V2\status\
- Secrets: L:\!Nova V2\secrets\nova_v2_passwords.txt
- Docker compose lokaal: L:\!Nova V2\infrastructure\docker-compose.yml
- Docker compose Hetzner: /docker/nova-v2/docker-compose.yml
- Host bridge code: L:\!Nova V2\nova_host_bridge\
- Host bridge config: L:\!Nova V2\nova_config.yaml
- Bridge start script: L:\!Nova V2\nova_host_bridge\start_bridge.ps1

## Volgende verwachte stap

Batch 3 (operationals/producers) volgens Pipeline Build plan, óf:
- Agent 22 (Blender Renderer) toevoegen aan host bridge zodra Blender CLI op PC geconfigureerd is.
- Bridge auto-start (Task Scheduler) zodat Agent 21 niet afhangt van handmatige start.
