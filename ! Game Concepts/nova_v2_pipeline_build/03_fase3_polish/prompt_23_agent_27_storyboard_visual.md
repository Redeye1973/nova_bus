# Prompt 23: Agent 27 - Storyboard Visual

## Wat deze prompt bouwt

Storyboard Visual voor NOVA v2 pipeline.

## Voorwaarden

- [ ] Prompt 22 compleet
- [ ] agent_22_status.json toont "active" of "fallback_mode"

## De prompt

```
Bouw Agent 27 - Storyboard Visual voor NOVA v2.

CONTEXT:
- Spec: L:\!Nova V2\extensions\nova_v2_extensions\storyboard\27_storyboard_visual_agent.md
- Target: L:\!Nova V2\v2_services\agent_27_storyboard_visual\
- Hetzner: /docker/nova-v2/services/agent_27_storyboard_visual/
- Webhook: http://178.104.207.194:5680/webhook/storyboard
- Port intern: 8127
- V2 N8n: http://178.104.207.194:5679
- Language: Python 3.11, FastAPI
- Referentie: L:\!Nova V2\v2_services\agent_20_design_fase\ voor structuur

JURY MEMBERS (5 leden):
composition, character_consistency, action_flow, camera_variety, canon_visual

ENDPOINTS:
/panels/generate, /storyboard/compose, /panels/review

DEPENDENCIES:
pillow opencv-python (Ollama vision on host)

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
10. Status file schrijven naar L:\!Nova V2\status\agent_27_status.json
11. Log naar pipeline_build_YYYY-MM-DD.log

SPECIFIEK VOOR DEZE AGENT:
- Main.py met 3 endpoints uit ENDPOINTS lijst
- Per jury member een Python module
- Judge module om scores te aggregeren
- Dockerfile expose port 8127
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
- Agent 27 Storyboard Visual status
- Webhook URL
- Test resultaten  
- Status: active/fallback/failed
- Volgende prompt: 24
```

## Verwachte output

Service met 6 Python modules, deployed op Hetzner, N8n workflow active.

## Validatie

```powershell
# Test webhook
$testBody = @{} | ConvertTo-Json  # Vul in met relevante test data uit spec
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/storyboard" -Method POST -Body $testBody -ContentType "application/json"

# Check status
Get-Content "L:\!Nova V2\status\agent_27_status.json" | ConvertFrom-Json
```

Verwacht: status "active" of "fallback_mode".

## Debug bij fouten

Zie `docs/DEBUGGING_GUIDE.md`. Specifiek voor deze agent:
- Check container logs: `ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs agent-27-storyboard_visual"`
- Check dependencies geïnstalleerd als host tools nodig zijn
- Check Ollama running op PC (tailscale bereikbaar)

## Volgende prompt

`03_fase3_polish/prompt_24_agent_*.md` (zie PROMPT_INDEX.md)
