# Fase 2 Validatie Checklist

Na alle prompts van Fase 2 (Story + GIS), valideer voordat je doorgaat.

## Automatische check

```powershell
.\utils\status_check.ps1 -Detailed
```

Verwacht: 5+/6 agents "active" of "fallback_mode".

## Handmatige checks

### Check 1: Infrastructure nog gezond

```powershell
# V1 nog OK (kritiek!)
curl -I http://178.104.207.194:5678

# V2 services running
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps | grep agent- | wc -l"
```

### Check 2: Agent-specific tests

```powershell
# Narrative query
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/narrative-review" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# PDOK download
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/pdok-download" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# QGIS process
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/qgis-process" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# GIS validation
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/gis-review" -Method POST -Body $body -ContentType "application/json"
```

### Check 3: Git state

```powershell
cd "L:\!Nova V2"
git log --oneline -6
```

## Checklist

### Agents gebouwd
- [ ] Agent 07 Narrative Jury
- [ ] Agent 28 Story Text Integration
- [ ] Agent 13 PDOK Downloader
- [ ] Agent 15 QGIS Processor
- [ ] Agent 14 Blender Baker
- [ ] Agent 05 GIS Jury

### Infrastructure
- [ ] V1 nog 100% functioneel (CRITICAL)
- [ ] V2 N8n UI bereikbaar
- [ ] Alle Fase 2 containers running

### Testing
- [ ] Narrative query: PASS
- [ ] PDOK download: PASS
- [ ] QGIS process: PASS
- [ ] GIS validation: PASS


## Milestone

Schrijf `L:\!Nova V2\status\milestone_fase2.md`:

```markdown
# Fase 2 Compleet - [datum]

## Agents Status
- Active: X/6
- Fallback: Y
- Failed: Z

## Next
Fase 3 gestart op [datum]
```

## Wanneer door

Go als:
- 5+ agents active of fallback
- V1 intact
- Geen blocking issues

Anders: fix eerst volgens `docs/DEBUGGING_GUIDE.md`.
