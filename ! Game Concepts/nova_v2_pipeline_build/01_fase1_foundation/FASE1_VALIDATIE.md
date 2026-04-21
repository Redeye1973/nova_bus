# Fase 1 Validatie Checklist

Na alle 10 prompts van Fase 1 (Agent 20, 02, 10, 21, 22, 23, 25, 26, 11, 17), valideer voordat je doorgaat.

## Automatische check

```powershell
.\utils\status_check.ps1 -Detailed
```

Verwacht: minstens 8/10 agents "active" of "fallback_mode".

## Handmatige checks

### Check 1: Infrastructure nog gezond

```powershell
# V1 nog OK (kritiek!)
curl -I http://178.104.207.194:5678
# Moet HTTP 200 of 401 returnen

# V2 N8n UI bereikbaar
curl -I http://178.104.207.194:5679
# Moet HTTP 200 of 401 returnen

# V2 webhook bereikbaar
curl -I http://178.104.207.194:5680
# Moet HTTP 200 returnen

# Alle containers running
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps --format json | grep -c '\"State\":\"running\"'"
# Verwacht: minstens 12 (infra + agents)
```

### Check 2: Design pipeline werkt

Test dat sprite productie keten werkt:

```powershell
# Test Agent 20 Design Fase
$body = @{theme="industrial_neutral"; faction_count=3} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/design-fase" -Method POST -Body $body -ContentType "application/json"
Write-Host "Design Fase: $($r.master_palette.Count) kleuren"
# Verwacht: 32

# Test Agent 02 Code Jury
$code = "def hello(): print('world')"
$body = @{language="python"; code=$code} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/code-review" -Method POST -Body $body -ContentType "application/json"
Write-Host "Code Jury verdict: $($r.verdict)"
# Verwacht: accept/revise/reject

# Test Agent 10 Game Balance (simpele stats)
$body = @{stats=@{hp=100;damage=25;speed=5}} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/balance-review" -Method POST -Body $body -ContentType "application/json"
Write-Host "Balance verdict: $($r.verdict)"
```

### Check 3: Monitor + Error werken

```powershell
# Monitor status
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/monitor" -Method GET
Write-Host "Monitor observeert: $($r.agents_observed) agents"

# Error Agent test met fake error
$body = @{agent="test"; error_type="timeout"; simulate=$true} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/error-handler" -Method POST -Body $body -ContentType "application/json"
Write-Host "Error Agent: $($r.action)"
```

### Check 4: Git state

```powershell
cd "L:\!Nova V2"
git status
git log --oneline -20
```

Verwacht: laatste 10 commits zijn de agent builds.

### Check 5: Logs

```powershell
# Laatste log entries
Get-Content "L:\!Nova V2\logs\pipeline_build_$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 50
```

Verwacht: entries per agent, mostly SUCCESS.

## Checklist (vink af)

### Agents gebouwd
- [ ] Agent 20 Design Fase (active)
- [ ] Agent 02 Code Jury (active)
- [ ] Agent 10 Game Balance Jury (active)
- [ ] Agent 21 FreeCAD Parametric (active of fallback)
- [ ] Agent 22 Blender Game Renderer (active of fallback)
- [ ] Agent 23 Aseprite Processor (active of fallback)
- [ ] Agent 25 PyQt5 Assembly (active)
- [ ] Agent 26 Godot Import (active of fallback)
- [ ] Agent 11 Monitor (active)
- [ ] Agent 17 Error (active)

### Infrastructure
- [ ] V1 nog 100% functioneel (CRITICAL)
- [ ] V2 N8n UI bereikbaar
- [ ] V2 webhook responsief
- [ ] Alle containers running
- [ ] PostgreSQL + Redis + MinIO + Qdrant up

### Testing
- [ ] Design Fase returnt 32-color palette
- [ ] Code Jury kan Python review doen
- [ ] Balance Jury geeft verdict
- [ ] Monitor ziet andere agents
- [ ] Error Agent reageert

### Documentatie
- [ ] `L:\!Nova V2\status\` bevat 10 status files
- [ ] `L:\!Nova V2\logs\` heeft pipeline log
- [ ] Git commits zijn aanwezig
- [ ] Geen uncommitted changes

## Scores

**Pass (ga door naar Fase 2):**
- 8+ agents active
- Alle infrastructure checks groen
- V1 intact

**Partial (fix eerst, dan door):**
- 6-7 agents active
- Niet-kritieke fails
- Plan gemaakt voor fix

**Fail (stop, debug):**
- < 6 agents active
- V1 geraakt
- Infrastructure issues

## Fix volgorde bij fails

1. V1 issues → onmiddellijk herstellen
2. Infrastructure issues → docker compose restart
3. Individuele agents → `utils\reset_failed_agent.ps1` + re-run prompt
4. Dependency issues → check `docs\AGENT_DEPENDENCIES.md`

## Documenteer

Schrijf `L:\!Nova V2\status\milestone_fase1.md`:

```markdown
# Fase 1 Compleet - [datum]

## Agents Status
- Active: X/10
- Fallback: Y
- Failed: Z

## Test Resultaten
- Design pipeline: PASS/FAIL
- Code jury: PASS/FAIL
- Infrastructure: PASS/FAIL

## Known Issues
- [lijst]

## Next
Fase 2 gestart op [datum]
```

Commit dit.

## Wanneer door naar Fase 2

Go als:
- 8+ agents active
- V1 intact
- Geen blocking issues
- Je hebt 2-3 dagen voor Fase 2

Anders: fix eerst, dan door.
