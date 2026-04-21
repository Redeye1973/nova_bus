# Sync from_cursor responses naar Claude project
# Kopieert recente cursor responses naar een map die je in Claude project kan uploaden

param(
    [string]$OutputDir = "$HOME\Desktop\nova_bridge_upload",
    [int]$DaysBack = 1
)

$bridgeRoot = Split-Path -Parent $PSScriptRoot
$fromCursor = Join-Path $bridgeRoot "handoff\from_cursor"
$sharedState = Join-Path $bridgeRoot "handoff\shared_state"

if (-not (Test-Path $fromCursor)) {
    Write-Host "from_cursor directory niet gevonden" -ForegroundColor Red
    exit 1
}

# Maak output dir schoon
if (Test-Path $OutputDir) {
    Remove-Item "$OutputDir\*" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

# Copy recente responses
$cutoff = (Get-Date).AddDays(-$DaysBack)
$recent = Get-ChildItem -Path $fromCursor -Filter "*.md" | 
    Where-Object { $_.LastWriteTime -gt $cutoff }

$count = 0
foreach ($f in $recent) {
    Copy-Item $f.FullName $OutputDir
    $count++
}

# Copy shared state
if (Test-Path $sharedState) {
    $stateDir = Join-Path $OutputDir "shared_state"
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    Copy-Item "$sharedState\*" $stateDir -Force -ErrorAction SilentlyContinue
}

# Maak index
$indexPath = Join-Path $OutputDir "INDEX.md"
@"
# NOVA Bridge Upload - $(Get-Date -Format 'yyyy-MM-dd HH:mm')

$count responses sinds $($cutoff.ToString('yyyy-MM-dd'))

## Responses
$(($recent | ForEach-Object { "- $($_.Name) ($(Get-Date $_.LastWriteTime -Format 'HH:mm'))" }) -join "`n")

## Shared state
Huidige baseline + blockers + decisions in shared_state/ subfolder.

## Upload instructie
Drag-drop alle .md files in een Claude chat of voeg toe aan Claude project.
"@ | Set-Content $indexPath

Write-Host ""
Write-Host "$count responses gekopieerd naar: $OutputDir" -ForegroundColor Green
Write-Host "Upload deze folder naar je Claude project (via project settings → Add files)" -ForegroundColor Cyan
Write-Host ""

# Open de folder
Start-Process explorer.exe $OutputDir
