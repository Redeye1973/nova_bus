# Current Baseline - NOVA V2

**Last update**: 2026-04-19 by Cursor  
**Updated by**: Cursor (via batch 1 deployment)

## Actieve agents (verified E2E)

| Agent | Name | Webhook | Response time | Notes |
|-------|------|---------|---------------|-------|
| 01 | Sprite Jury POC | /webhook/sprite-review-poc | 174ms | Verdict: accept (placeholder) |
| 02 | Code Jury | /webhook/code-review | 354ms | Full jury: radon + pycodestyle + bandit + GDScript |
| 10 | Game Balance Jury | /webhook/balance-review | 82ms | Reject verdict op minimal payload (correct) |
| 20 | Design Fase | /webhook/design-fase | 78ms | 32-color palette + 3 faction palettes |

## Stub agents (containers healthy, logica leeg)

29 agents: 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 35

## Infrastructure

- **V2 N8n**: http://178.104.207.194:5679 (Up, geen healthcheck maar responsief)
- **V2 Webhook**: http://178.104.207.194:5680 (Up)
- **PostgreSQL**: healthy
- **Redis**: healthy
- **MinIO**: healthy, ports 19000/19001
- **Qdrant**: Up (geen healthcheck definitie)

## V1 status (baseline, niet aangeraakt)

- Poort 5678
- 68 productieworkflows
- Up 2+ dagen
- MCP integratie met Cursor werkt

## Bekende issues (niet blockers)

1. Agent 20 `industrial_neutral` thema mist entry in palette_manager.py theme_hues, valt terug op default hue 220. Low priority polish.
2. N8n services hebben geen docker healthcheck definitie. Cosmetisch, responsief wel.
3. Docker Compose v5 syntax: `--parallel` werkt zonder getal, niet `--parallel N`.

## Resources

- Pipeline Build package: L:\!Nova V2\pipelines\nova_v2_pipeline_build\nova_v2_pipeline_build\
- Status files: L:\!Nova V2\status\
- Secrets: L:\!Nova V2\secrets\nova_v2_passwords.txt
- Docker compose lokaal: L:\!Nova V2\infrastructure\docker-compose.yml
- Docker compose Hetzner: /docker/nova-v2/docker-compose.yml

## Volgende verwachte stap

Batch 2 per Pipeline Build plan: Agents 11 (Monitor), 17 (Error), 21 (FreeCAD Parametric).
