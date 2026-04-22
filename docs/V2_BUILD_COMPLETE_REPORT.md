# NOVA v2 — Build complete report (Fase G)

**Datum:** 2026-04-22  
**Scope:** Codebase + Compose agents + pipelines F tooling (sessies 05–08).  
**Omgeving:** primair Hetzner `nova-v2` stack + dev PC host bridge (Tailscale).

---

## Agent-landschap (35 slots)

| Categorie | Aantal | IDs / opmerking |
|-----------|--------|------------------|
| **v2_services agents (02–35)** | **34** | Geen `agent_01` in `v2_services`; sprite jury = aparte `sprite_jury` service (= agent 01). |
| **Totaal logische agents** | **35** | 01 (sprite) + 02…35. |
| **Bridge-stub (`pending_full_bridge` / 503 op domein)** | **8** | 22, 23, 25, 26, 31, 32, 33, 35 |
| **Headless / QGIS-stub-achtig** | **2** | 14 (blender bake stub), 15 (QGIS process `pending_full_bridge` in body) |
| **Overige: POC / jury / operationeel** | **~25** | O.a. jury’s 02–10 (minus skips), operational 11–19, asset 20–21, 24, 27–30, 34, 12, 13, 16–19, enz. |

*Cijfers zijn engineering-estimates op basis van repo-health strings; geen live Hetzner-sweep in dit document.*

**Skipped / buiten batch:** oorspronkelijke skip-lijst (o.a. 01 orchestrator-stijl, 02/10 afhankelijk van plan); zie `to_build.md`.

---

## Pipelines F (sessie 08)

| Pipeline | Artefact | Status tooling |
|----------|----------|----------------|
| Shmup | `pipelines/pipeline_shmup_master.json` | Dry-run runner + N8n import-klaar |
| Bake | `pipelines/pipeline_bake_master.json` | Idem |
| Story | `pipelines/pipeline_story_master.json` | Idem; live E2E vereist judge+DB |

**Postgres DDL:** `scripts/create_session08_pipeline_tables.sql` (`pipeline_runs`, `pipeline_step_logs`).

**Validatie:** `python scripts/run_pipeline_validation.py` (dry-run) en `--execute` met `PIPELINE_USE_PUBLISHED_PORTS=1` wanneer poorten op localhost staan.

---

## Cost / API spending

Centraal **niet** geaggregeerd in dit rapport. Gebruik **Agent 16 Cost Guard** (`/cost/log`, `/budget`) en provider-consoles (ElevenLabs, cloud GPU, …) voor werkelijke kosten.

---

## Known issues

1. **Host bridge single point** — PC offline ⇒ FreeCAD/QGIS-paden via bridge weg; Agent 21 valt terug op trimesh.
2. **Bridge-stubs** — bake/shmup pipelines blokkeren op echte output tot bridge-adapter uitbreiding (zie `to_build.md`).
3. **N8n** — master workflows moeten nog geïmporteerd/geactiveerd worden op V2 UI (`:5679`).
4. **Pipeline metrics** — DDL klaar; inserts vanuit runner naar Postgres optioneel (nu JSON-artefact).

---

## Roadmap — Fase H (DAZ; Ren’Py **out of scope**)

| Item | Status |
|------|--------|
| DAZ Studio pad + `nova_host_bridge` adapter | Config + adapterbestand in repo; **wire in `main.py`** + tests volgen bij volgende bridge-sprint |
| Agents 38, 40–43 (DAZ / prompts) | Gepland; niet in deze baseline |
| Ren’Py 36–37 | **bewust niet** |

---

## Backup (sessie 09)

Zie **`scripts/hetzner_backup_cron_templates.sh`** voor cron-blokken (pg_dump → MinIO, mirror, weekly config tarball).  
Uitvoeren op server na invullen van `mc` aliases en container-namen.

---

## Status

**V2 core build: klaar voor productie-operatie** met de gebruikelijke voorbehouden (stubs, handmatige N8n-import, backup-job installatie).

**NOVA V2 BUILD COMPLETE** (rapport + handoff; infra-cron op server = handwerk).
