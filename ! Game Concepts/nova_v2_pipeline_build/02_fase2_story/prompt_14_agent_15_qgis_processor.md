# Prompt 14: Agent 15 - QGIS Processor

## Wat deze prompt bouwt

QGIS Processor voor NOVA v2 pipeline.

## Voorwaarden

- [ ] Prompt 13 compleet
- [ ] agent_13_status.json toont "active" of "fallback_mode"

## De prompt

```
Bouw Agent 15 - QGIS Processor voor NOVA v2.

CONTEXT:
- Spec: L:\!Nova V2\agents\nova_v2_agents\operational\15_qgis_processor.md
- Target: L:\!Nova V2\v2_services\agent_15_qgis_processor\
- Hetzner: /docker/nova-v2/services/agent_15_qgis_processor/
- Webhook: http://178.104.207.194:5680/webhook/qgis-process
- Port intern: 8115
- V2 N8n: http://178.104.207.194:5679
- Language: Python 3.11, FastAPI
- Referentie: L:\!Nova V2\v2_services\agent_20_design_fase\ voor structuur

TYPE: Operational agent (geen jury, pure functionaliteit)
N/A (operational)

ENDPOINTS:
/process/dem, /process/vector, /convert/format

DEPENDENCIES:
gdal geopandas (QGIS on host)

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
10. Status file schrijven naar L:\!Nova V2\status\agent_15_status.json
11. Log naar pipeline_build_YYYY-MM-DD.log

SPECIFIEK VOOR DEZE AGENT:
- Main.py met 3 endpoints uit ENDPOINTS lijst
- Geen jury, direct functionaliteit
- Geen judge
- Dockerfile expose port 8115
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
- Agent 15 QGIS Processor status
- Webhook URL
- Test resultaten  
- Status: active/fallback/failed
- Volgende prompt: 15
```

## Verwachte output

Service met meerdere Python modules, deployed op Hetzner, N8n workflow active.

## Validatie

```powershell
# Test webhook
$testBody = @{} | ConvertTo-Json  # Vul in met relevante test data uit spec
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/qgis-process" -Method POST -Body $testBody -ContentType "application/json"

# Check status
Get-Content "L:\!Nova V2\status\agent_15_status.json" | ConvertFrom-Json
```

Verwacht: status "active" of "fallback_mode".

## Debug bij fouten

Zie `docs/DEBUGGING_GUIDE.md`. Specifiek voor deze agent:
- Check container logs: `ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs agent-15-qgis_processor"`
- Check dependencies geïnstalleerd als host tools nodig zijn


## Volgende prompt

`02_fase2_story/prompt_15_agent_*.md` (zie PROMPT_INDEX.md)
