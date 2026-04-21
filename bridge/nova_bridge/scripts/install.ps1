# NOVA Bridge - Eerste keer installatie

Write-Host ""
Write-Host "=== NOVA Bridge Installation ===" -ForegroundColor Cyan
Write-Host ""

$bridgeRoot = Split-Path -Parent $PSScriptRoot

# Stap 1: Python check
Write-Host "Stap 1: Python check..." -ForegroundColor Cyan
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "  Python niet gevonden. Installeer eerst Python 3.9+" -ForegroundColor Red
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Gray
    exit 1
}
$pyVersion = python --version 2>&1
Write-Host "  OK: $pyVersion" -ForegroundColor Green

# Stap 2: Dependencies
Write-Host "Stap 2: Python dependencies..." -ForegroundColor Cyan
pip install plyer requests 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK: plyer + requests installed" -ForegroundColor Green
} else {
    Write-Host "  Warning: dependencies install issue - toast notifications werken mogelijk niet" -ForegroundColor Yellow
}

# Stap 3: Directory structuur
Write-Host "Stap 3: Directory check..." -ForegroundColor Cyan
$dirs = @(
    "handoff\to_cursor",
    "handoff\from_cursor", 
    "handoff\shared_state",
    "handoff\archive"
)
foreach ($d in $dirs) {
    $full = Join-Path $bridgeRoot $d
    if (-not (Test-Path $full)) {
        New-Item -ItemType Directory -Force -Path $full | Out-Null
        Write-Host "  Created: $d" -ForegroundColor Yellow
    } else {
        Write-Host "  OK: $d" -ForegroundColor Green
    }
}

# Stap 4: Git init als nog niet done
Write-Host "Stap 4: Git init..." -ForegroundColor Cyan
Push-Location $bridgeRoot
try {
    if (-not (Test-Path ".git")) {
        git init -q
        
        # .gitignore
        @"
bridge_state.json
watcher.pid
bridge_watcher.log
watcher_process.log*
*.tmp
"@ | Set-Content .gitignore
        
        git add .
        git commit -m "NOVA Bridge initial setup" -q
        Write-Host "  OK: git initialized" -ForegroundColor Green
    } else {
        Write-Host "  OK: git repo exists" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

# Stap 5: Cursor rules reminder
Write-Host ""
Write-Host "Stap 5: Cursor configuratie..." -ForegroundColor Cyan
Write-Host "  HANDMATIGE ACTIE VEREIST:" -ForegroundColor Yellow
Write-Host "  1. Open Cursor → Settings → Rules for AI" -ForegroundColor White
Write-Host "  2. Voeg rules toe uit: $bridgeRoot\docs\CURSOR_SETUP.md" -ForegroundColor White
Write-Host ""

# Stap 6: Eerste handoff
Write-Host "Stap 6: Eerste handoff klaar?" -ForegroundColor Cyan
$firstHandoff = Get-ChildItem "$bridgeRoot\handoff\to_cursor\*.md" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($firstHandoff) {
    Write-Host "  OK: $($firstHandoff.Name)" -ForegroundColor Green
    Write-Host "  Klaar voor Cursor om op te pakken" -ForegroundColor Gray
} else {
    Write-Host "  Geen opdrachten in to_cursor/ - normaal voor eerste install" -ForegroundColor Gray
}

# Samenvatting
Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Volgende stappen:" -ForegroundColor Cyan
Write-Host "  1. Cursor rules instellen (zie docs\CURSOR_SETUP.md)"
Write-Host "  2. Start watcher:   .\scripts\start_watcher.ps1"
Write-Host "  3. Check status:    .\scripts\handoff_status.ps1"
Write-Host "  4. Open Cursor + begin met handoff"
Write-Host ""
Write-Host "Documentatie:" -ForegroundColor Gray
Write-Host "  - README.md (overzicht)"
Write-Host "  - docs\PROTOCOL.md (hoe handoffs werken)"
Write-Host "  - docs\CURSOR_SETUP.md (Cursor configuratie)"
Write-Host "  - docs\TROUBLESHOOTING.md (problemen)"
Write-Host ""
