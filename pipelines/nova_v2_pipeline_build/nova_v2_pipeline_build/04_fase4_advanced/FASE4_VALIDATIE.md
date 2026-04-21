# Fase 4 Validatie Checklist

Na alle prompts van Fase 4 (Advanced), valideer voordat je doorgaat.

## Automatische check

```powershell
.\utils\status_check.ps1 -Detailed
```

Verwacht: 7+/8 agents "active" of "fallback_mode".

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
# QGIS analysis
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/qgis-analysis" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# 3D mesh validation
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/3d-review" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# CAD validation
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/cad-review" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# Distribution package
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/distribute" -Method POST -Body $body -ContentType "application/json"
```

### Check 3: Git state

```powershell
cd "L:\!Nova V2"
git log --oneline -8
```

## Checklist

### Agents gebouwd
- [ ] Agent 31 QGIS Analysis
- [ ] Agent 32 GRASS GIS
- [ ] Agent 35 Raster 2D Processor
- [ ] Agent 09 2D Illustration Jury
- [ ] Agent 12 Bake Orchestrator
- [ ] Agent 04 3D Model Jury
- [ ] Agent 06 CAD Jury
- [ ] Agent 19 Distribution Agent

### Infrastructure
- [ ] V1 nog 100% functioneel (CRITICAL)
- [ ] V2 N8n UI bereikbaar
- [ ] Alle Fase 4 containers running

### Testing
- [ ] QGIS analysis: PASS
- [ ] 3D mesh validation: PASS
- [ ] CAD validation: PASS
- [ ] Distribution package: PASS


## Milestone

Schrijf `L:\!Nova V2\status\milestone_fase4.md`:

```markdown
# Fase 4 Compleet - [datum]

## Agents Status
- Active: X/8
- Fallback: Y
- Failed: Z

## Next
Fase 5 gestart op [datum]
```

## Wanneer door

Go als:
- 7+ agents active of fallback
- V1 intact
- Geen blocking issues

Anders: fix eerst volgens `docs/DEBUGGING_GUIDE.md`.
