# SESSIE 06 — Agent Bouw Batch 2: Operationele core (11-19)

**Doel:** 9 operationele agents bouwen.
**Tijd:** 90-150 min
**Afhankelijkheden:** 05 compleet (minstens 5/7 juries actief)

Te bouwen:
- 11 Monitor Agent (EERST — backbone voor rest)
- 12 Bake Orchestrator (na 13/14/15)
- 13 PDOK Downloader
- 14 Blender Baker
- 15 QGIS Processor
- 16 Cost Guard
- 17 Error Agent (na 11)
- 18 Prompt Director
- 19 Distribution Agent

---

### ===SESSION 06 START===

```
SESSIE 06 van 7 — Operationele core batch (agents 11-19).

Volgorde:
1. Monitor Agent (11) EERST — andere agents rapporteren hierheen
2. Error Agent (17) — catch-all voor andere bouw
3. Cost Guard (16) — voordat dure agents draaien
4. Data agents parallel: 13 PDOK, 14 Blender, 15 QGIS
5. Bake Orchestrator (12) — binds 13/14/15 samen
6. 18 Prompt Director + 19 Distribution Agent

## Per agent: zelfde template als sessie 05

## Agent-specifieke logic

### 11 Monitor Agent
- Health checks op alle andere services (ping elke 60s)
- PDOK wekelijkse delta check
- Feedback aggregator (REST endpoint voor bugs/requests)
- Cost tracking (leest van Cost Guard)
- Alerting via webhook naar Alex (email optional)
Functions:
- GET /status → totaal systeem health
- POST /feedback → gebruiker feedback inschieten
- GET /metrics → prometheus-compatible metrics

### 13 PDOK Downloader
- API client voor PDOK BAG, BGT, Top10NL, BRT
- Caching in MinIO bucket (nova-pdok-cache)
- Delta detection tegen vorige snapshot
- Webhook triggers: /download (met postcode + layers)
Pure data, geen AI nodig.

### 14 Blender Baker
- Receives PDOK input (GeoJSON)
- Runs Blender headless via bridge
- Template scenes voor stad/gebouwen/infra
- Output: glTF/GLB per tile
Stub eerst, volledige implementatie met bridge later.

### 15 QGIS Processor
- Runs QGIS headless via bridge
- Geometry processing (buffers, intersections, dissolve)
- Coordinate transformations
- Raster manipulations
Bridge-dependent. Als bridge recovery mode: skip volledige implementatie,
markeer "pending_full_bridge".

### 12 Bake Orchestrator
- N8n workflow die 13 → 15 → 14 chain maakt
- State management in Postgres bake_jobs tabel
- Progress tracking (0-100%)
- Resource management (max 1 bake tegelijk op Arc A770)

### 16 Cost Guard
- Monitors alle externe API calls
- Daily budget cap (configureerbaar, default €5/dag)
- Log naar Postgres cost_log tabel
- Hard stop als budget bereikt (returns 429)
- Dagelijks rapport via Monitor Agent
Postgres schema:
CREATE TABLE cost_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMP DEFAULT NOW(),
  service TEXT NOT NULL,
  operation TEXT,
  estimated_cost_eur NUMERIC,
  actual_cost_eur NUMERIC,
  agent_id TEXT,
  metadata JSONB
);

### 17 Error Agent
- Receives errors van andere agents
- Classificatie: transient (retry-able) vs permanent
- Auto-retry logic (delegated terug naar originating agent)
- Alert escalation naar Monitor Agent
- Error knowledge base (Qdrant voor similar error lookup)

### 18 Prompt Director
- Library van prompt templates
- Versioning
- A/B test ondersteuning
- API: GET /templates/:name → returns latest approved version

### 19 Distribution Agent
- Final delivery naar consumers
- Versioning + changelog generation
- MinIO distribution bucket
- Access control basis (API key per consumer)
- Webhook: /publish (met asset_id, consumer_id)

## Execution loop

Monitor Agent eerst (10 min work):
- Build + deploy
- Test /health endpoint
- Register alle andere services dat ze heartbeats moeten sturen

Dan parallel: 13, 14, 15 (40-60 min):
- Build alle drie
- Deploy alle drie
- Test individueel

Dan 12 Bake Orchestrator (20 min):
- Workflow die 13 → 15 → 14 chain
- Test end-to-end met dummy input (1 postcode, 1 tile)

Dan 16 + 17 parallel (20 min):
- Cost Guard (Postgres schema + service)
- Error Agent

Dan 18 + 19 parallel (15 min):
- Prompt Director (simpel template service)
- Distribution Agent (MinIO wrapper)

## Commits
Na Monitor (1), na PDOK/Blender/QGIS (3), na Orchestrator (1), na Cost+Error (2),
na Director+Distribution (2) → totaal 9 commits max.

## Rapport

File: docs\session_06_report.md
# Sessie 06 Rapport
- Agents: 11, 12, 13, 14, 15, 16, 17, 18, 19
- Active: <count>/9
- Bridge-dependent pending: <count> (14, 15 waarschijnlijk)
- Tests passed: <count>/9
- Total commits: <count>
- Status: SUCCESS (>=7/9) / PARTIAL / FAILED
- Next: sessie 07 (asset production batch)

git commit -m "session 06: operational core complete (X/9)"
git push origin main

Print "SESSION 06 COMPLETE — X/9 agents active — next: sessie 07"

REGELS:
- Monitor agent zonder fouten voordat rest (hij monitort alles)
- Cost Guard zonder fouten voordat externe API agents (29, 30) in sessie 07
- Bridge-afhankelijke agents: stub acceptable, noteer in status

Ga.
```

### ===SESSION 06 EINDE===

---

## OUTPUT

- 9 operationele agents gebouwd (volledige of stub)
- Postgres tabellen voor bake_jobs + cost_log
- Monitor + Cost Guard actief tegen rest
- `docs/session_06_report.md`
