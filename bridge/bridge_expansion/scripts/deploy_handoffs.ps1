# Bridge Expansion - Deploy handoffs to bridge

Write-Host ""
Write-Host "=== NOVA Bridge Expansion Deploy ===" -ForegroundColor Cyan
Write-Host ""

$bridgeBase = "L:\!Nova V2\bridge\nova_bridge"
$handoffDir = Join-Path $bridgeBase "handoff\to_cursor"
$adaptersBackupDir = Join-Path $bridgeBase "expansion_resources\adapters"
$testsBackupDir = Join-Path $bridgeBase "expansion_resources\tests"
$docsBackupDir = Join-Path $bridgeBase "expansion_resources\docs"

# Check bridge bestaat
if (-not (Test-Path $bridgeBase)) {
    Write-Host "Bridge folder niet gevonden: $bridgeBase" -ForegroundColor Red
    Write-Host "Installeer eerst nova_bridge package" -ForegroundColor Yellow
    exit 1
}

# Determine where this script is
$expansionRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Expansion package: $expansionRoot" -ForegroundColor Gray
Write-Host "Bridge folder:     $bridgeBase" -ForegroundColor Gray
Write-Host ""

# Stap 1: Copy handoffs naar to_cursor/
Write-Host "Stap 1: Handoffs deployen..." -ForegroundColor Cyan
$handoffSrc = Join-Path $expansionRoot "handoffs"
$handoffs = Get-ChildItem "$handoffSrc\*.md"
foreach ($h in $handoffs) {
    $target = Join-Path $handoffDir $h.Name
    Copy-Item $h.FullName $target -Force
    Write-Host "  Copied: $($h.Name)" -ForegroundColor Green
}

# Stap 2: Copy adapters naar bridge expansion_resources (referentie, niet direct install)
Write-Host "Stap 2: Adapter templates deployen als referentie..." -ForegroundColor Cyan
if (-not (Test-Path $adaptersBackupDir)) {
    New-Item -ItemType Directory -Force -Path $adaptersBackupDir | Out-Null
}
Copy-Item "$expansionRoot\adapters\*" $adaptersBackupDir -Force
Write-Host "  Templates beschikbaar in: $adaptersBackupDir" -ForegroundColor Green

# Stap 3: Copy tests
Write-Host "Stap 3: Tests deployen..." -ForegroundColor Cyan
if (-not (Test-Path $testsBackupDir)) {
    New-Item -ItemType Directory -Force -Path $testsBackupDir | Out-Null
}
Copy-Item "$expansionRoot\tests\*" $testsBackupDir -Force
Write-Host "  Tests beschikbaar in: $testsBackupDir" -ForegroundColor Green

# Stap 4: Copy docs
Write-Host "Stap 4: Docs deployen..." -ForegroundColor Cyan
if (-not (Test-Path $docsBackupDir)) {
    New-Item -ItemType Directory -Force -Path $docsBackupDir | Out-Null
}
Copy-Item "$expansionRoot\docs\*" $docsBackupDir -Force
Write-Host "  Docs beschikbaar in: $docsBackupDir" -ForegroundColor Green

# Stap 5: Copy inventory script voor direct gebruik
Write-Host "Stap 5: Inventory script deployen..." -ForegroundColor Cyan
$scriptsBackupDir = Join-Path $bridgeBase "scripts"
Copy-Item "$expansionRoot\scripts\inventory_scan.ps1" $scriptsBackupDir -Force
Write-Host "  Script: $scriptsBackupDir\inventory_scan.ps1" -ForegroundColor Green

Write-Host ""
Write-Host "=== Deploy Compleet ===" -ForegroundColor Green
Write-Host ""
Write-Host "Handoffs gedetecteerd door bridge watcher (als draait)." -ForegroundColor Cyan
Write-Host ""
Write-Host "Volgende stappen:" -ForegroundColor Gray
Write-Host "  1. Run inventory: .\scripts\inventory_scan.ps1" -ForegroundColor Gray
Write-Host "  2. Check watcher: .\scripts\handoff_status.ps1" -ForegroundColor Gray
Write-Host "  3. Cursor pikt handoffs automatisch op" -ForegroundColor Gray
Write-Host ""
Write-Host "Handoff volgorde:" -ForegroundColor Gray
Write-Host "  001 - Inventory check (doe eerst zelf)" -ForegroundColor Gray
Write-Host "  002 - Install missing tools" -ForegroundColor Gray
Write-Host "  003 - Blender + Aseprite + PyQt adapters" -ForegroundColor Gray
Write-Host "  004 - Godot adapter" -ForegroundColor Gray
Write-Host "  005 - GRASS + GIMP + Krita + Inkscape adapters" -ForegroundColor Gray
Write-Host ""
