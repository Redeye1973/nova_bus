# NOVA v2 Debugging Guide

Systematische aanpak voor problemen tijdens pipeline build.

## Flowchart: agent werkt niet

```
Agent webhook response fout?
│
├─ Timeout (>60s geen response)
│  └─ Check container: docker compose logs agent-XX
│     ├─ Container draait niet: restart docker compose up -d agent-XX
│     ├─ Container in restart loop: check logs voor error
│     └─ Container OK maar hangt: kill + restart
│
├─ 500 Internal Server Error
│  └─ docker compose logs agent-XX --tail 100
│     ├─ Python exception: fix code + rebuild
│     ├─ Missing dependency: update requirements.txt
│     └─ External tool missing: check host installatie
│
├─ 404 Not Found  
│  └─ N8n workflow niet active
│     ├─ Check in UI: http://178.104.207.194:5679/workflows
│     ├─ Activate handmatig of via API
│     └─ Verify webhook path matches
│
└─ 401/403 Unauthorized
   └─ Check V2 API key in .env matches secrets file
```

## Per stap debug procedures

### STAP 3 (code generation) faalt

Cursor genereert geen werkende code:

```powershell
# Check of spec bestand bestaat
Test-Path "L:\!Nova V2\agents\nova_v2_agents\jury_judge\XX_*.md"
Test-Path "L:\!Nova V2\extensions\nova_v2_extensions\*\XX_*.md"

# Als niet: spec ontbreekt, extract uit zip opnieuw
cd "L:\!Nova V2"
Expand-Archive -Path "nova_v2_agents.zip" -DestinationPath "agents_temp" -Force
```

### STAP 5 (unit tests) falen

```powershell
cd "L:\!Nova V2\v2_services\agent_XX_name"

# Activate venv
.venv\Scripts\Activate.ps1

# Run met verbose
pytest tests/ -v -s

# Specific test
pytest tests/test_agent.py::test_specific_thing -v

# Check dependencies
pip list | findstr "fastapi pydantic"

# Reinstall if needed
pip install -r requirements.txt --force-reinstall
```

### STAP 6 (docker build) faalt

```powershell
cd "L:\!Nova V2\v2_services\agent_XX_name"

# Build met verbose
docker build --no-cache -t test-agent-XX . --progress=plain

# Common issues:
# - Basis image niet beschikbaar: docker pull python:3.11-slim
# - requirements.txt conflict: check versions
# - Copy failures: check .dockerignore
```

### STAP 7 (deploy naar Hetzner) faalt

```powershell
# Check SSH werkt
ssh root@178.104.207.194 "echo ok"

# Check disk space
ssh root@178.104.207.194 "df -h /"

# Als vol: cleanup
ssh root@178.104.207.194 "docker system prune -a --volumes -f"

# Check docker compose syntax
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose config"

# Handmatig deploy
scp -r .\v2_services\agent_XX_*\ root@178.104.207.194:/docker/nova-v2/services/
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose build agent-XX && docker compose up -d agent-XX"
```

### STAP 8 (N8n workflow import) faalt

```powershell
# Test API key
$v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" | Where-Object { $_ -match "N8N_V2_API_KEY" } | Select-Object -First 1) -replace ".*N8N_V2_API_KEY\s*=\s*", ""
$v2key = $v2key.Trim()
Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows" -Headers @{"X-N8N-API-KEY"=$v2key}

# Verwacht: {data: [...]}
# Als 401: key invalid, regenereer in UI

# Valideer workflow.json
Get-Content "L:\!Nova V2\v2_services\agent_XX\workflow.json" | Test-Json

# Als syntax error: open in editor, fix JSON

# Handmatig import
$workflow = Get-Content "L:\!Nova V2\v2_services\agent_XX\workflow.json" -Raw
$response = Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows" -Method POST -Headers @{"X-N8N-API-KEY"=$v2key; "Content-Type"="application/json"} -Body $workflow
Write-Host "Created: $($response.id)"
```

### STAP 9 (end-to-end test) faalt

```powershell
# Check webhook bereikbaar
Invoke-RestMethod -Uri "http://178.104.207.194:5680" -Method GET

# Test webhook met minimal payload
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/XXXXX" -Method POST -Body $body -ContentType "application/json"

# Als 404: workflow niet active of wrong path
# Als 500: agent container issue

# Follow de chain in N8n UI:
# http://178.104.207.194:5679/workflows
# Find workflow, click op execution → zie failure point
```

## Specifieke problemen

### Ollama calls falen

```powershell
# Check Ollama draait op PC
ollama list

# Check via tailscale bereikbaar vanaf Hetzner
ssh root@178.104.207.194 "curl -s http://<jouw-tailnet-ip>:11434/api/tags"

# Als niet: Tailscale down of Ollama niet gestart
```

### Blender/FreeCAD/etc niet gevonden

```powershell
# Check paths via nova_config.yaml
Get-Content "L:\!Nova V2\nova_config.yaml" | Select-String "blender|freecad"

# Test tool
& "L:\UE_5.7\..." --version  # vul in juist pad

# Als ontbreekt: run software discovery opnieuw (zie CURSOR_SOFTWARE_DISCOVERY_PROMPT uit eerdere zip)
```

### V2 infrastructure down

```powershell
# Check containers
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps"

# Als down: start opnieuw
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose up -d"

# Als blijft crashen: check logs per service
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs"
```

### V1 breekt (kritiek)

Dit zou NOOIT mogen gebeuren. Als wel:

```powershell
# Check V1 status
curl -I http://178.104.207.194:5678

# Als niet respond:
ssh root@178.104.207.194 "cd /docker/nova/ && docker compose ps"  # of andere pad

# Herstel vanuit backup als aangetast
# Zie vorige deploy logs voor V1 pad
```

STOP onmiddellijk met V2 werk als V1 geraakt is. Eerst V1 herstellen, dan V2 door.

## Logging

### Pipeline log bekijken

```powershell
# Laatste 20 regels
Get-Content "L:\!Nova V2\logs\pipeline_build_$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 20

# Live follow
Get-Content "L:\!Nova V2\logs\pipeline_build_$(Get-Date -Format 'yyyy-MM-dd').log" -Wait

# Search voor agent
Select-String -Path "L:\!Nova V2\logs\*.log" -Pattern "agent_22"
```

### Container logs

```powershell
# Specific agent
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs agent-XX-name --tail 100"

# Live follow
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs -f agent-XX-name"

# All services
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs --tail 20"
```

## Emergency procedures

### Alles terugdraaien (rollback pipeline)

```powershell
# Stop alle v2 agent containers, behoud infrastructure
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose stop `$(docker compose ps --services | grep agent-)"

# Of nuclear option: stop alles behalve v1
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose down"

# V1 check
curl -I http://178.104.207.194:5678
```

### Status reset

```powershell
# Backup current status
Copy-Item "L:\!Nova V2\status\*.json" "L:\!Nova V2\backups\status_$(Get-Date -Format 'yyyy-MM-dd_HH-mm')\"

# Clear failed statuses voor retry
Get-ChildItem "L:\!Nova V2\status\" -Filter "agent_*_status.json" | ForEach-Object {
    $status = Get-Content $_.FullName | ConvertFrom-Json
    if ($status.status -eq "failed") {
        Remove-Item $_.FullName
        Write-Host "Cleared: $($_.Name)"
    }
}
```

### Cursor loop detectie

Als Cursor dezelfde fout blijft maken:

1. Stop Cursor (Ctrl+C in Composer)
2. Open nieuwe Composer
3. Plak:
```
Ik was bezig met prompt XX (agent YY).
Stop met huidige aanpak.
Lees status uit L:\!Nova V2\status\agent_YY_status.json
Als status "failed": markeer en ga naar volgende prompt.
Als status "active": we zijn klaar met deze, volgende prompt.
```

## Wanneer hulp vragen

Escaleer naar mij (nieuwe Claude sessie) als:
- Same fout na 3 retries verschillende approaches
- V1 geraakt (kritiek)
- Infrastructure fundamentele fout (database corruption, disk fail)
- Security incident (onauthorized access)
- Onbegrip over spec interpretation

Geef mij mee:
- Welke prompt
- Welke agent
- Full error log (geen secrets)
- Wat al geprobeerd
- Current status
