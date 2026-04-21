# START HIER - NOVA v2 Pipeline Build

Voor jij begint met de prompts, doe deze setup eenmalig.

## Stap 1: Valideer voorwaarden

Open PowerShell en run deze checks:

```powershell
# 1. Check V2 infrastructure bereikbaar
curl -sI http://178.104.207.194:5679 | Select-Object -First 1
# Verwacht: HTTP/1.1 200 OK (of 401)

# 2. Check V1 nog werkt  
curl -sI http://178.104.207.194:5678 | Select-Object -First 1
# Verwacht: HTTP/1.1 200 OK (of 401)

# 3. Check V2 API key werkt
$v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" | Where-Object { $_ -match "N8N_V2_API_KEY" } | Select-Object -First 1) -replace ".*N8N_V2_API_KEY\s*=\s*", ""
$v2key = $v2key.Trim()
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows" -Headers @{"X-N8N-API-KEY"=$v2key}
Write-Host "V2 workflows: $($r.data.Count)"
# Verwacht: minstens 1 (agent 01 Sprite Jury)

# 4. Check SSH key werkt
ssh -o BatchMode=yes root@178.104.207.194 "echo OK"
# Verwacht: OK
```

Als alle 4 slagen: ga door naar Stap 2.
Als iets faalt: fix dat eerst.

## Stap 2: Backup maken

Voor je begint, maak backup van huidige staat:

```powershell
# Backup infrastructure (.env etc.)
cd "L:\!Nova V2"
$backup_dir = "backups\pre_pipeline_build_$(Get-Date -Format 'yyyy-MM-dd_HH-mm')"
New-Item -ItemType Directory -Force -Path $backup_dir
Copy-Item "infrastructure\.env" "$backup_dir\"
Copy-Item "secrets\nova_v2_passwords.txt" "$backup_dir\"
Copy-Item "status\*.json" "$backup_dir\" -ErrorAction SilentlyContinue

# Backup Hetzner v2 database
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose exec -T postgres-v2 pg_dumpall -U postgres | gzip > /root/backup_pre_pipeline_$(date +%Y%m%d).sql.gz"

Write-Host "Backup klaar in $backup_dir"
```

## Stap 3: Directory structuur check

```powershell
# Maak alle benodigde submappen aan
$base = "L:\!Nova V2"
$dirs = @("v2_services", "status", "logs", "docs", "backups", "workflows_imported")
foreach ($d in $dirs) {
    $p = "$base\$d"
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
    Write-Host "OK: $p"
}
```

## Stap 4: V1 orchestrator webhook check (optional)

V1 heeft een orchestrator met 68 agents. Als we die kunnen gebruiken: voordeel. Anders: fallback naar Cursor zelf.

```powershell
# Test of V1 webhook voor build tasks bestaat
$v1key = Get-Content "L:\!Nova V2\secrets\N8n WorkHorse.txt" -Raw
$v1key = $v1key.Trim()
try {
    $probe = Invoke-RestMethod -Uri "http://178.104.207.194:5678/webhook/nova-session-load" -Method POST -Headers @{"X-N8N-API-KEY"=$v1key} -Body '{"probe": true}' -ContentType "application/json" -TimeoutSec 5
    Write-Host "V1 webhook werkt: $probe"
} catch {
    Write-Host "V1 webhook niet direct bruikbaar - geen probleem, fallback mode actief"
}
```

## Stap 5: Eerste prompt klaarmaken

Open deze bestanden in volgorde, gebruik dat als leidraad:

1. `00_master/MASTER_PLAN.md` - overall plan doorlezen
2. `00_master/PROMPT_INDEX.md` - overzicht van alle 36 prompts
3. `01_fase1_foundation/README.md` - fase 1 uitleg
4. `01_fase1_foundation/prompt_01_agent_20_design_fase.md` - eerste prompt

## Stap 6: Werk workflow

**Per prompt:**

1. Lees de prompt volledig
2. Check voorwaarden aan top van bestand
3. Kopieer prompt blok (tussen ``` markers)
4. Plak in Cursor Composer
5. Laat Cursor werken (2-3 uur typisch)
6. Check status file: `L:\!Nova V2\status\agent_XX_status.json`
7. Run validatie tests
8. Als OK: git commit, volgende prompt
9. Als fail: debug, fix, retry of skip

**Per fase:**

- Na alle prompts van een fase: run FASEX_VALIDATIE.md checklist
- Schrijf milestone naar status/milestone_faseX.md
- Commit alles

## Stap 7: 24/7 PC setup (aanbevolen)

Voor optimale workflow:

```powershell
# Installeer Tailscale (als nog niet)
# Download: https://tailscale.com/download/windows
# Run installer, login met email
# Op Hetzner: curl -fsSL https://tailscale.com/install.sh | sh && tailscale up

# Verify Tailscale connectie
Get-NetAdapter | Where-Object { $_.Name -match "Tailscale" }
```

Hiermee kan Hetzner direct jouw PC bereiken voor Ollama calls.

## Hulp bij problemen

**Prompt werkt niet?**
Zie: `docs/DEBUGGING_GUIDE.md`

**Cursor raakt in loop?**
Open nieuwe Composer met: "Resume agent build, lees status uit ./status/"

**Agent faalt consistent?**
Skip die agent, markeer in status, continue met volgende. Zie: `docs/FALLBACK_PROCEDURES.md`

**V1 of V2 down?**
Eerst infrastructuur herstellen. Pipeline build blokkeert niet v1 productie.

## Klaar?

Als Stap 1-5 groen zijn, open `01_fase1_foundation/prompt_01_agent_20_design_fase.md` en begin.

Tijd voor volledige build: 2-3 weken autonoom met 24/7 PC, of 4-6 weken als je alleen overdag laat draaien.
