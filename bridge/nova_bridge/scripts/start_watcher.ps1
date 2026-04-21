# Start NOVA Bridge Watcher in background

param(
    [int]$Interval = 30,
    [switch]$Foreground
)

$bridgeRoot = Split-Path -Parent $PSScriptRoot
$script = Join-Path $bridgeRoot "scripts\bridge_watcher.py"

if (-not (Test-Path $script)) {
    Write-Host "bridge_watcher.py niet gevonden: $script" -ForegroundColor Red
    exit 1
}

# Check of Python beschikbaar is
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python niet gevonden in PATH" -ForegroundColor Red
    exit 1
}

# Check voor plyer (voor notifications)
$plyerCheck = & python -c "import plyer" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "plyer niet geïnstalleerd - toasts werken mogelijk niet." -ForegroundColor Yellow
    Write-Host "Installeer met: pip install plyer" -ForegroundColor Yellow
    Write-Host ""
    $install = Read-Host "Nu installeren? (y/N)"
    if ($install -eq "y") {
        pip install plyer
    }
}

if ($Foreground) {
    # Draai in foreground voor debug
    Write-Host "Watcher foreground (Ctrl+C om te stoppen)..." -ForegroundColor Cyan
    & python $script --interval $Interval
} else {
    # Start in background via Start-Process
    $logFile = Join-Path $bridgeRoot "watcher_process.log"
    
    # Check of al draait
    $existingPid = $null
    $pidFile = Join-Path $bridgeRoot "watcher.pid"
    if (Test-Path $pidFile) {
        $existingPid = Get-Content $pidFile
        $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Watcher draait al (PID $existingPid)" -ForegroundColor Yellow
            Write-Host "Om te stoppen: .\scripts\stop_watcher.ps1" -ForegroundColor Gray
            exit 0
        }
    }
    
    $process = Start-Process -FilePath "python" -ArgumentList "`"$script`"", "--interval", $Interval `
        -WindowStyle Hidden -PassThru -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err"
    
    # Save PID
    $process.Id | Out-File $pidFile -NoNewline
    
    Write-Host ""
    Write-Host "NOVA Bridge Watcher gestart" -ForegroundColor Green
    Write-Host "  PID: $($process.Id)"
    Write-Host "  Log: $logFile"
    Write-Host "  Interval: ${Interval}s"
    Write-Host ""
    Write-Host "Monitor met: .\scripts\handoff_status.ps1" -ForegroundColor Gray
    Write-Host "Stop met:    .\scripts\stop_watcher.ps1" -ForegroundColor Gray
}
