# Prompt 10: Agent 17 - Error Agent

## Wat deze prompt bouwt

Error Agent voor NOVA v2 pipeline.

## Voorwaarden

- [ ] Prompt 09 compleet
- [ ] agent_09_status.json toont "active" of "fallback_mode"

## De prompt

```
Bouw Agent 17 - Error Agent voor NOVA v2.

CONTEXT:
- Spec: L:\!Nova V2\agents\nova_v2_agents\operational\17_error_agent.md
- Target: L:\!Nova V2\v2_services\agent_17_error\
- Hetzner: /docker/nova-v2/services/agent_17_error/
- Webhook: http://178.104.207.194:5680/webhook/error-handler
- Port intern: 8117
- V2 N8n: http://178.104.207.194:5679
- Language: Python 3.11, FastAPI
- Referentie: L:\!Nova V2\v2_services\agent_20_design_fase\ voor structuur

TYPE: Operational agent (geen jury, pure functionaliteit)
N/A (operational, auto-repair)

ENDPOINTS:
/error/report, /error/resolve, /repair/history

DEPENDENCIES:
requests (needs V1 knowledge base)

VOLG PROMPT TEMPLATE uit 00_master/PROMPT_TEMPLATE.md voor alle 11 stappen:
1. Spec lezen uit spec bestand
2. V1 delegation probeer (anders fallback Cursor solo)
3. Directory structuur + files maken
4. Logic implementeren per spec
5. Unit tests (minimaal 4)
6. Docker build + test
7. Deploy naar Hetzner via scp + docker compose up
8. N8n workflow import + activate via API
9. End-to-end test via webhook
10. Status file schrijven naar L:\!Nova V2\status\agent_17_status.json
11. Log naar pipeline_build_YYYY-MM-DD.log

SPECIFIEK VOOR DEZE AGENT:
- Main.py met 3 endpoints uit ENDPOINTS lijst
- Geen jury, direct functionaliteit
- Geen judge
- Dockerfile expose port 8117
- docker-compose.yml service entry toevoegen aan Hetzner compose
- N8n workflow met webhook -> HTTP request -> response pattern

FALLBACK MODE:
- Als dependencies externe tools nodig hebben (Blender, QGIS, GRASS, FreeCAD, Godot, Aseprite, GIMP, Krita, Inkscape): 
  implementeer met subprocess calls, vereist dat tool op host geinstalleerd is
- Als Ollama nodig: pointer naar lokale PC host.docker.internal:11434
- Als tests niet kunnen draaien zonder externe tool: mock tests, markeer fallback_mode: true

REGELS:
- Max 2 retries per stap
- Bij deploy failure: rollback, rapporteer, continue met status "failed"
- Bij test failure: markeer fallback_mode, continue
- NOOIT V1 op 5678 raken
- Secrets lezen uit L:\!Nova V2\secrets\nova_v2_passwords.txt
- Status file + log entry altijd schrijven

RAPPORT:
Aan einde toon samenvatting:
- Agent 17 Error Agent status
- Webhook URL
- Test resultaten  
- Status: active/fallback/failed
- Volgende prompt: 11 (Fase 2)
```

## Verwachte output

Service met meerdere Python modules, deployed op Hetzner, N8n workflow active.

## Validatie

```powershell
# Test webhook
$testBody = @{} | ConvertTo-Json  # Vul in met relevante test data uit spec
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/error-handler" -Method POST -Body $testBody -ContentType "application/json"

# Check status
Get-Content "L:\!Nova V2\status\agent_17_status.json" | ConvertFrom-Json
```

Verwacht: status "active" of "fallback_mode".

## Debug bij fouten

Zie `docs/DEBUGGING_GUIDE.md`. Specifiek voor deze agent:
- Check container logs: `ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs agent-17-error"`
- Check dependencies geïnstalleerd als host tools nodig zijn


## Volgende prompt

`01_fase1_foundation/prompt_11_agent_*.md` (zie PROMPT_INDEX.md)
