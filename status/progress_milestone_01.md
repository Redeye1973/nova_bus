# Mega build — milestone (1/35)

**Datum:** 2026-04-19  
**Agents voltooid in deze batch:** 1 (01_sprite_jury)

## Agent 01 — Sprite Jury

- **Code:** `v2_services/01_sprite_jury/` (FastAPI POC), gespiegeld naar `infrastructure/services/sprite_jury/`.
- **Deploy:** Hetzner `/docker/nova-v2/services/sprite_jury`, compose service `sprite-jury-v2`.
- **Tests:** 4× pytest lokaal geslaagd.
- **n8n V2:** workflow geïmporteerd en geactiveerd; webhook `sprite-review-poc` E2E OK (`accept` op mock jury scores).
- **Fallback:** geen V1 orchestrator POST (geen bekend endpoint); implementatie door Cursor uit spec.

## Volgende stap

- Agent **02_code_jury** volgens dezelfde C.x-structuur (`v2_services/02_code_jury`, compose-service, workflow, status JSON).
