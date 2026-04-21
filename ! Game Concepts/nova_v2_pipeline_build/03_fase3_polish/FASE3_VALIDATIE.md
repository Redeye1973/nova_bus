# Fase 3 Validatie Checklist

Na alle prompts van Fase 3 (Polish + Audio), valideer voordat je doorgaat.

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
# Audio generation (cached)
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/audio-generate" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# Audio review
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/audio-review" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# Prompt directing
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/prompt-direct" -Method POST -Body $body -ContentType "application/json"
```

```powershell
# Cost tracking
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/cost-track" -Method POST -Body $body -ContentType "application/json"
```

### Check 3: Git state

```powershell
cd "L:\!Nova V2"
git log --oneline -8
```

## Checklist

### Agents gebouwd
- [ ] Agent 24 Aseprite Animation Jury
- [ ] Agent 29 ElevenLabs Audio
- [ ] Agent 03 Audio Jury
- [ ] Agent 30 Audio Asset Jury
- [ ] Agent 18 Prompt Director
- [ ] Agent 16 Cost Guard
- [ ] Agent 27 Storyboard Visual
- [ ] Agent 08 Character Art Jury

### Infrastructure
- [ ] V1 nog 100% functioneel (CRITICAL)
- [ ] V2 N8n UI bereikbaar
- [ ] Alle Fase 3 containers running

### Testing
- [ ] Audio generation (cached): PASS
- [ ] Audio review: PASS
- [ ] Prompt directing: PASS
- [ ] Cost tracking: PASS


## Milestone

Schrijf `L:\!Nova V2\status\milestone_fase3.md`:

```markdown
# Fase 3 Compleet - [datum]

## Agents Status
- Active: X/8
- Fallback: Y
- Failed: Z

## Next
Fase 4 gestart op [datum]
```

## Wanneer door

Go als:
- 7+ agents active of fallback
- V1 intact
- Geen blocking issues

Anders: fix eerst volgens `docs/DEBUGGING_GUIDE.md`.
