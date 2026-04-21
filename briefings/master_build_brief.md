# NOVA v2 Mega Build — Master briefing (V1 orchestrator / Cursor)

**Gegenereerd:** 2026-04-19 (autonome Fase B-brief)  
**Werkmap:** `L:\!Nova V2\`  
**Doel:** 35 v2 agents volgens `mega_plan/agent_volgorde.md` bouwen, testen, op V2 (n8n :5679 + infra Hetzner) landen.

## Scope

- **Bronnen:** `agents/nova_v2_agents/` (01–19), `extensions/nova_v2_extensions/` (20–35), `shmup/shmup_pipeline/`.
- **Target:** V2 n8n `http://178.104.207.194:5679`, Docker onder `/docker/nova-v2/`.
- **V1:** `http://178.104.207.194:5678` — alleen **read/delegatie**, geen wijzigingen aan productie-workflows zonder expliciete goedkeuring.

## Bouwvolgorde (35)

Zie `mega_plan/agent_volgorde.md` voor rationale. Nummers:

01–10 jury-reeks, 11–19 operationeel, 20–26 game asset, 27–28 story, 29–30 audio, 31–32 GIS, 33–34 arch/UE, 35 raster 2D.

## Delegatie naar V1 (indien beschikbaar)

Formaat: zie `mega_plan/v1_delegation_format.md`.  
Per agent: `task_type: build_v2_agent`, `agent_number`, `agent_spec` (inhoud `.md`), `target_path: L:\\!Nova V2\\v2_services\\<name>\\`.

## Fallback (als V1 orchestrator geen code genereert)

- Cursor (of handmatige sessies) gebruikt de **Cursor prompts** in de `.md` specs om `v2_services/<agent>/` te vullen (FastAPI, Dockerfile, tests, workflow JSON).
- Deploy volgens `mega_plan/00_MASTER_PROMPT.md` Fase C (SSH/compose/n8n import).

## Rapportage

- Per agent: `status/agent_<NN>_status.json`
- Milestones: `status/progress_milestone_<N>.md` elke 5 agents
- Log: `logs/mega_build_<timestamp>.txt`

## Escalaties

Zie `mega_plan/error_escalation.md`.  
**Huidige blocker (Fase A meting):** V2 n8n API vereist geldige **N8N_V2_API_KEY** (na admin-setup in UI). Zonder key: geen workflow-import/automation tegen :5679.
