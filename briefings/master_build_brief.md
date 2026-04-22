# NOVA v2 Master Build Brief

**Bijgewerkt:** 2026-04-22 (sessie 03 — V1 orchestrator + capabilities)  
**Werkmap:** `L:\!Nova V2\`  
**Doel:** 30 agents bouwen volgens Deel 5 van `mega_plan/NOVA_V2_UNIFIED_MEGA_PROMPT.md`, deploy naar V2 (n8n :5679 + Docker op Hetzner).

## Bronnen en paden

- Agent specs: `agents/nova_v2_agents/`, `extensions/nova_v2_extensions/`, `shmup/shmup_pipeline/` waar van toepassing.
- **V2 target:** `http://178.104.207.194:5679` — workflows importeren / automation (API key: secrets).
- **V1:** `http://178.104.207.194:5678` — **read + delegatie**; geen wijzigingen aan productie-workflows zonder expliciete goedkeuring.
- Machine-leesbare V1-snapshot: `briefings/v1_workflow_inventory.json`, `briefings/v1_capabilities.json` (regenereer met `scripts/build_session_03_briefings.py`).

## Skip-lijst (al gebouwd of vastgelegd als skip — niet opnieuw als leeg-stub overschrijven zonder review)

- Agent 01 Sprite Jury POC — `/webhook/sprite-review-poc`
- Agent 02 Code Jury — `/webhook/code-review`
- Agent 10 Game Balance Jury — `/webhook/balance-review`
- Agent 20 Design Fase — `/webhook/design-fase`
- Agent 21 FreeCAD Parametric — `/webhook/freecad-parametric`

## Te bouwen (30 agents, volgorde Deel 5)

Volgorde en parallel-markers: zie `mega_plan/NOVA_V2_UNIFIED_MEGA_PROMPT.md` (DEEL 5). Samenvatting:

| # | Agent | Groep / opmerking |
|---|--------|-------------------|
| E1 | 03 Audio Jury | PARALLEL met 04 |
| E2 | 04 3D Model Jury | PARALLEL met 03 |
| E3 | 05 GIS Jury | PARALLEL met 06 |
| E4 | 06 CAD Jury | PARALLEL met 05 |
| E5 | 07 Narrative Jury | na E1–E4 |
| E6 | 08 Character Art Jury | PARALLEL met 09 |
| E7 | 09 2D Illustration Jury | PARALLEL met 08 |
| E8 | 11 Monitor Agent | eerst (backbone) |
| E9 | 13 PDOK Downloader | PARALLEL met 14, 15 |
| E10 | 14 Blender Baker | PARALLEL met 13, 15 |
| E11 | 15 QGIS Processor | PARALLEL met 13, 14 |
| E12 | 12 Bake Orchestrator | na E9–E11 |
| E13 | 16 Cost Guard | |
| E14 | 17 Error Agent | na 11 |
| E15 | 18 Prompt Director | |
| E16 | 19 Distribution Agent | |
| E17 | 22 Blender Game Renderer | depends op 21 output |
| E18 | 23 Aseprite Processor | depends op 22 |
| E19 | 24 Aseprite Animation Jury | depends op 23 |
| E20 | 25 PyQt5 Assembly | depends op 23, 24 |
| E21 | 26 Godot Import | depends op 25 |
| E22 | 27 Storyboard Visual Agent | depends op 08, 09 |
| E23 | 28 Story Text Integration | depends op 07 |
| E24 | 29 ElevenLabs Audio Agent | PARALLEL met 30 |
| E25 | 30 Audio Asset Jury | PARALLEL met 29; depends op 03 |
| E26 | 31 QGIS Analysis | depends op 15 |
| E27 | 32 GRASS GIS Analysis | PARALLEL met 31 |
| E28 | 33 Blender Architecture Walkthrough | depends op 22, 04 |
| E29 | 34 Unreal Engine Import | depends op 33 |
| E30 | 35 Raster 2D Processor | bridge utilities |

## V1 capabilities (sessie 03)

- **Workflows (API `limit=100`):** totaal **68**, waarvan **52** actief — volledige lijst met id/naam/webhook_paths in `briefings/v1_workflow_inventory.json`.
- **Build-gerelateerde kandidaten (keyword-heuristiek):** **40** workflows in `briefings/v1_capabilities.json` → `build_related_workflows` (geen garantie dat elk item echte codegen doet).
- **Orchestrator / unified build webhook:** documentatie noemt `POST …/webhook/nova-orchestrator` (DEEL 6) en soms `nova_v2_build_task`. Sessie 03-probe: **geen succesvolle codegen-response** binnen 2 pogingen → **`codegen`: `fallback_to_cursor`** (Cursor genereert uit `.md` specs; zie DEEL 6 fallback).
- **FastAPI-scaffold / pytest / Docker / SSH-deploy:** niet automatisch bevestigd als aparte V1-webhooks; behandel als **niet vastgesteld** tot een workflow expliciet is gekoppeld en getest.
- **Delegatie:** gebruik payload-contract uit DEEL 6 (hieronder samengevat); bevestig in V1 UI welke webhook-path actief is voordat je bulk-delegatie draait.

## Delegation format (samenvatting — volledig in mega DEEL 6)

```text
POST http://178.104.207.194:5678/webhook/nova-orchestrator
Headers: Content-Type: application/json, X-N8N-API-KEY: <v1_key>,
         X-Task-Source: cursor_unified_build, X-Task-Priority: normal
```

Body: JSON met o.a. `task_id`, `task_type: build_v2_agent`, `v2_agent` (number, name, category, spec pad/inhoud, target_directory), `requirements` (Python 3.11, FastAPI, tests, Dockerfile, n8n workflow, judge, self_heal), `dependencies`, `output_format`, `deadline_minutes`, `escalation_contact`.

## Escalatie (samenvatting — volledig: `mega_plan/error_escalation.md`)

- **Level 1:** log, doorgaan (retry ok, kleine warnings).
- **Level 2:** pauzeer agent, `needs_manual_review`, andere agents door.
- **Level 3:** stop nieuwe tasks — V1/V2 infra down, secrets corrupt, disk kritiek, V1 15 min niet responsive → `status/critical_halt.md`.
- **Level 4:** emergency — V1 per ongeluk gewijzigd, V2 breekt V1, data corruption → stop alles, alleen V2 down indien nodig, restore, `status/emergency.md`.

## Fallback (geen V1-codegen)

Zelfde als DEEL 6: Cursor vult `v2_services/<agent>/` o.b.v. agent-`.md` specs (FastAPI, Dockerfile, tests, workflow JSON); deploy volgens `mega_plan/00_MASTER_PROMPT.md` Fase C.

## Rapportage

- Per agent: `status/agent_<NN>_status.json`
- Milestones: `status/progress_milestone_<N>.md` elke 5 agents
- Log: `logs/mega_build_<timestamp>.txt`

## Blocker uit eerdere brief (sessie 01)

- V2 n8n API vereist geldige **N8N_V2_API_KEY** voor import/automation op :5679; zonder key blijft dat beperkt.
