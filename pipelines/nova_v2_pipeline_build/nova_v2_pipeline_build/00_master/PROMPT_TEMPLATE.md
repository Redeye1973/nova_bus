# Agent Build Template

Dit is de standaard structuur voor elk prompt bestand. Consistent = voorspelbaar = debugbaar.

## File structuur per prompt

```markdown
# Prompt NN: Agent XX - [Agent Naam]

## Wat deze prompt bouwt

[1-2 zinnen over wat de agent doet]

## Voorwaarden

- [ ] Vorige prompts in fase compleet
- [ ] [specifieke vereisten voor deze agent]

## Voor plakken in Cursor

1. Verifieer voorwaarden
2. Kopieer prompt block hieronder
3. Plak in Cursor Composer (Ctrl+I)
4. Enter, laat Cursor werken
5. Monitor: `Get-Content "L:\!Nova V2\status\agent_XX_status.json"`

## De prompt

[Hier komt het prompt block dat Cursor uitvoert]

## Verwachte output

[Wat Cursor geleverd moet hebben]

## Validatie

[Hoe je handmatig test]

## Debug als het faalt

[Specifieke debug stappen]

## Commit message

[Git commit message formaat]
```

## Universele prompt template

Elk prompt heeft deze elementen in de Cursor prompt zelf:

```
Bouw Agent XX - [NAAM] voor NOVA v2.

CONTEXT:
- Spec: [pad naar .md bestand]
- Target: L:\!Nova V2\v2_services\agent_XX_naam\
- Deploy: /docker/nova-v2/services/agent_XX/ op Hetzner
- V2 N8n: http://178.104.207.194:5679
- Language: Python 3.11, FastAPI
- Secrets: L:\!Nova V2\secrets\nova_v2_passwords.txt

STAP 1: SPEC LEZEN
Open [agent spec path]
Extract: doel, scope, jury leden, endpoints, dependencies

STAP 2: V1 DELEGATION (OPTIONEEL)
Try: curl -X POST http://178.104.207.194:5678/webhook/[indien beschikbaar]
Als V1 capability missing: skip, gebruik fallback Cursor generation

STAP 3: GENEREER SERVICE STRUCTUUR
Maak in L:\!Nova V2\v2_services\agent_XX_naam\:
- main.py (FastAPI app)
- requirements.txt
- Dockerfile
- tests/test_agent.py
- workflow.json (N8n import)
- README.md

STAP 4: IMPLEMENTEER LOGIC
Per spec:
- Endpoints (meestal POST /review, /process, etc)
- Jury members (indien jury-judge agent)
- Helper modules
- Dependencies (Ollama, MinIO, Qdrant indien relevant)

STAP 5: UNIT TESTS
Minimaal 4 tests via pytest:
- test_healthcheck
- test_happy_path (valid input → expected output)
- test_edge_case (invalid input → error)
- test_integration (cross-component)

Run lokaal: `cd v2_services\agent_XX && pytest tests/ -v`
Verwacht: alle tests passed.

STAP 6: DOCKER BUILD
Dockerfile werkt: `docker build -t nova-v2-agent-XX .`
Indien Ollama nodig: extra_hosts voor host.docker.internal

STAP 7: DEPLOY NAAR HETZNER
Via SSH:
- scp -r ./v2_services/agent_XX/ root@178.104.207.194:/docker/nova-v2/services/
- Update /docker/nova-v2/docker-compose.yml met nieuwe service
- ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose up -d agent-XX"
- Wacht 15s, verify container running: docker compose ps

STAP 8: IMPORT N8N WORKFLOW
Lees N8N_V2_API_KEY uit secrets:
$v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" | Where-Object { $_ -match "N8N_V2_API_KEY" } | Select-Object -First 1) -replace ".*N8N_V2_API_KEY\s*=\s*", ""
$v2key = $v2key.Trim()

Upload workflow:
Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows" -Method POST -Headers @{"X-N8N-API-KEY"=$v2key; "Content-Type"="application/json"} -Body (Get-Content workflow.json -Raw)

Note workflow_id uit response.

Activate workflow:
Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows/$workflow_id/activate" -Method POST -Headers @{"X-N8N-API-KEY"=$v2key}

STAP 9: END-TO-END TEST
curl -X POST http://178.104.207.194:5680/webhook/[webhook_path] -d [test payload]

Verwacht: 200 response met expected shape.

STAP 10: STATUS FILE
Schrijf L:\!Nova V2\status\agent_XX_status.json:
{
  "agent_number": XX,
  "name": "agent_name",
  "status": "active|failed|fallback_mode",
  "built_at": "YYYY-MM-DDTHH:MM:SS",
  "deployed_at": "YYYY-MM-DDTHH:MM:SS",
  "workflow_id": "n8n_workflow_id",
  "webhook_url": "http://178.104.207.194:5680/webhook/...",
  "tests_passed": true/false,
  "fallback_mode": true/false,
  "notes": "any issues encountered"
}

STAP 11: LOG
Append naar L:\!Nova V2\logs\pipeline_build_YYYY-MM-DD.log:
[timestamp] | agent_XX | built | SUCCESS/FAIL
[timestamp] | agent_XX | deployed | SUCCESS/FAIL
[timestamp] | agent_XX | tested | SUCCESS/FAIL

REGELS:
- Max 2 retries per stap
- Bij STAP 7 (deploy) failure: rollback container + rapporteer
- Bij STAP 9 (test) failure: markeer fallback_mode: true, continue
- NOOIT V1 op 5678 raken
- Secrets nooit in chat of logs
- Als iets kritisch faalt: stop, wacht op instructie

Na compleet: toon summary:
- Agent naam + webhook URL
- Test resultaat
- Status (active/fallback/failed)
- Wat volgende prompt is (next_prompt_number)
```

## Checks

Elke prompt moet resulteren in:
- ✓ Container draait op Hetzner
- ✓ Workflow geïmporteerd in V2 N8n
- ✓ Webhook responsive
- ✓ Status file geschreven
- ✓ Tests minstens 70% passed
- ✓ Log bijgewerkt

Als één mist: retry tot max 2x, dan markeer failed en ga door.

## Volgend prompt

Aan einde van elke prompt, Cursor toont:
- Klaar met prompt X
- Volgende prompt: `path/naar/prompt_Y.md`

Dit helpt jou de workflow volgen.
