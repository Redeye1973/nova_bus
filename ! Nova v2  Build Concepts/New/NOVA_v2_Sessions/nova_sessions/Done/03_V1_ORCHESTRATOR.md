# SESSIE 03 — V1 Orchestrator Brief + Capability Test

**Doel:** V1 opzetten als bouwmachine voor V2 agents.
**Tijd:** 30-45 min
**Afhankelijkheden:** Sessies 01, 02 compleet

---

### ===SESSION 03 START===

```
SESSIE 03 van 7 — V1 orchestrator brief + capability test.

## Doel
Vaststellen welke V1 capabilities beschikbaar zijn voor V2 agent bouw.
Zo niet genoeg: fallback mode vastleggen (Cursor self-gen).

## Stap 1: V1 workflows inventariseren

Load V1 key:
$v1key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" |
  Select-String "^N8N_V1_API_KEY=").ToString().Split("=",2)[1]

Haal alle workflows:
$workflows = Invoke-RestMethod `
  -Uri "http://178.104.207.194:5678/api/v1/workflows" `
  -Headers @{"X-N8N-API-KEY"=$v1key}

Filter op actieve workflows met webhook-triggers:
$active = $workflows.data | Where-Object { $_.active -eq $true }

Schrijf naar briefings/v1_workflow_inventory.json:
{
  "total": <count>,
  "active": <count>,
  "workflows": [
    {"id": "...", "name": "...", "active": true, "webhook_paths": [...]}
  ]
}

## Stap 2: zoek build-gerelateerde agents

Zoek in workflows naar namen die passen bij:
- code generation / codegen
- scaffold / boilerplate
- FastAPI / Python service
- test writer / pytest
- docker / deploy
- orchestrator / dispatcher

Log matching workflows. Als je ze vindt: noteer hun webhook-paths.
Deze gebruiken we in sessie 05-07 voor delegatie.

## Stap 3: capability test — simpele codegen via V1

Als een code generation workflow gevonden: test met minimale opdracht.

Voorbeeld payload:
$payload = @{
    task_type = "capability_check"
    prompt = "Generate a Python function that adds two integers."
    language = "python"
} | ConvertTo-Json

POST naar gevonden webhook. Tijd-out 30 sec.

Response analyseren:
- Als het code teruggeeft: V1 codegen werkt
- Als capability_missing: V1 heeft die workflow niet zoals gehoopt
- Als timeout: V1 mogelijk overbelast

Als GEEN code generation workflow gevonden in V1:
  Schakel fallback mode in. Noteer in briefings\v1_capabilities.json:
  {"codegen": "fallback_to_cursor", "reason": "no suitable workflow"}

## Stap 4: maak master briefing document

File: L:\!Nova V2\briefings\master_build_brief.md

Inhoud:
# NOVA v2 Master Build Brief

## Skip-lijst (al gebouwd, niet aanraken)
- Agent 01 Sprite Jury POC (/webhook/sprite-review-poc)
- Agent 02 Code Jury (/webhook/code-review)
- Agent 10 Game Balance Jury (/webhook/balance-review)
- Agent 20 Design Fase (/webhook/design-fase)
- Agent 21 FreeCAD Parametric (/webhook/freecad-parametric)

## Te bouwen (30 agents in volgorde)
[volledige lijst uit unified mega prompt deel 5]

## V1 capabilities
- Codegen: <beschikbaar via workflow X> | <fallback to Cursor>
- FastAPI scaffold: <...>
- Test generation: <...>
- Docker build: <...>
- SSH deploy: <...>

## Delegation format
[uit unified mega prompt deel 6]

## Escalatie paden
[uit unified mega prompt deel 7]

## Stap 5: Docker compose V2 validatie

SSH naar Hetzner, check compose file bestaat + services runnend:

ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps --format json"

Parse output. Voor elke service log status.
Verwacht minimaal:
- postgres-v2 (healthy)
- redis-v2 (healthy)
- n8n-v2-main (healthy)
- n8n-v2-worker-1 (healthy)
- n8n-v2-webhook (healthy)
- minio-v2 (healthy)
- qdrant-v2 (healthy)

Unhealthy containers loggen. Geen restart forceren (te risky).

## Stap 6: rapport + commit

File: L:\!Nova V2\docs\session_03_report.md
# Sessie 03 Rapport
- Timestamp: <iso>
- V1 totaal workflows: <n>
- V1 actieve workflows: <n>
- V1 build-capable workflows: <lijst>
- V1 codegen test: SUCCESS / FALLBACK / FAILED
- V2 infra gezondheid: <X/7 healthy>
- Master briefing geschreven: ja
- Status: SUCCESS / PARTIAL / FAILED
- Next session: 04 (Judge + self-heal deploy)

git add briefings/ docs/session_03_report.md
git commit -m "session 03: V1 orchestrator brief + capabilities vastgesteld"
git push origin main

Print "SESSION 03 COMPLETE — next: sessie 04 judge layer"

REGELS:
- Max 2 pogingen op V1 codegen test, dan fallback
- V1 workflow-lijst NIET publiek loggen (kan interne info bevatten)
- Schema van workflows OK in briefings/ (Alex's eigen repo)

Ga.
```

### ===SESSION 03 EINDE===

---

## OUTPUT

- `briefings/v1_workflow_inventory.json`
- `briefings/v1_capabilities.json`
- `briefings/master_build_brief.md`
- `docs/session_03_report.md`
- Git commit

## VERIFIEREN

```powershell
Get-Content "L:\!Nova V2\briefings\master_build_brief.md"
Get-Content "L:\!Nova V2\docs\session_03_report.md"
```

Ook kijken of V2 infra gezond is, anders sessie 04 niet kunnen starten.
