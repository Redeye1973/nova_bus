# Archive Old Handoffs
# Verplaats voltooide handoffs ouder dan X dagen naar archive

param(
    [int]$DaysOld = 30
)

$bridgeRoot = Split-Path -Parent $PSScriptRoot
$script = Join-Path $bridgeRoot "scripts\bridge_watcher.py"

Write-Host "Archiveer handoffs ouder dan $DaysOld dagen..." -ForegroundColor Cyan
python $script --cleanup

Write-Host "Klaar." -ForegroundColor Green
