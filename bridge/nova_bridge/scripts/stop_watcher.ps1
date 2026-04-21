# Stop NOVA Bridge Watcher

$bridgeRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $bridgeRoot "watcher.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "Geen PID file gevonden. Watcher niet actief?" -ForegroundColor Yellow
    exit 0
}

$pidValue = Get-Content $pidFile
$proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue

if (-not $proc) {
    Write-Host "Proces met PID $pidValue niet gevonden. Cleanup PID file." -ForegroundColor Yellow
    Remove-Item $pidFile -Force
    exit 0
}

try {
    Stop-Process -Id $pidValue -Force
    Remove-Item $pidFile -Force
    Write-Host "Watcher gestopt (PID $pidValue)" -ForegroundColor Green
} catch {
    Write-Host "Kon watcher niet stoppen: $_" -ForegroundColor Red
    exit 1
}
