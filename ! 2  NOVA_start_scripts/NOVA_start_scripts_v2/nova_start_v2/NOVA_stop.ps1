# NOVA_stop.ps1
# Stopt lokale services, remote blijft draaien

$ErrorActionPreference = "Continue"

function Say-Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Say-OK($m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Say-Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }

Write-Host ""
Write-Host "=== NOVA Stop (lokaal) ===" -ForegroundColor Magenta
Write-Host ""

$services = @("NOVA_Heartbeat", "NOVA_Bridge_Watchdog", "NOVA_Bridge_Service")

foreach ($svc in $services) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($s) {
        if ($s.Status -eq "Running") {
            Say-Info "$svc stoppen..."
            Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
            Say-OK "$svc gestopt"
        } else {
            Say-OK "$svc was al gestopt"
        }
    } else {
        Say-Warn "$svc niet geinstalleerd"
    }
}

# Cleanup losse python processen (bridge/watchdog/heartbeat)
Say-Info "Cleanup check..."
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
foreach ($p in $pythonProcs) {
    try {
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId = $($p.Id)" -ErrorAction SilentlyContinue
        if ($cim) {
            $cmd = $cim.CommandLine
            if ($cmd -and ($cmd -match "uvicorn.*8500" -or $cmd -match "bridge_watchdog" -or $cmd -match "bridge_heartbeat")) {
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                Say-OK "PID $($p.Id) gestopt"
            }
        }
    } catch {}
}

Write-Host ""
Write-Host "Lokale services gestopt. Remote Hetzner blijft draaien." -ForegroundColor Green
Write-Host ""
