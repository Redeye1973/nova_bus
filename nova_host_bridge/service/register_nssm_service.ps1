<#
.SYNOPSIS
    Register the NovaHostBridge Windows service via NSSM.

.DESCRIPTION
    NSSM (Non-Sucking Service Manager) wraps the Python uvicorn process as a
    proper Windows service with auto-restart, log rotation, and Service Control
    Manager integration. More robust than Task Scheduler for long-running
    daemons.

    Run from an elevated PowerShell prompt:
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File register_nssm_service.ps1

.NOTES
    Requires nssm.exe in PATH or set $NssmExe explicitly. Download:
        https://nssm.cc/release/nssm-2.24.zip
    Extract win64\nssm.exe to e.g. C:\Tools\nssm.exe and either add to PATH
    or pass via -NssmExe.
#>
[CmdletBinding()]
param(
    [string]$ServiceName = 'NovaHostBridge',
    [string]$DisplayName = 'NOVA Host Bridge (FreeCAD/QGIS over Tailscale)',
    [string]$Description = 'FastAPI service on :8500 exposing local FreeCAD + QGIS to Hetzner agents over the Tailscale tailnet.',
    [string]$NssmExe     = 'nssm.exe',
    [string]$BridgeRoot  = 'L:\!Nova V2\nova_host_bridge',
    [string]$ConfigPath  = 'L:\!Nova V2\nova_config.yaml',
    [string]$PythonExe   = 'C:\Python314\python.exe',
    [int]   $BindPort    = 8500,
    [string]$LogDir      = 'L:\!Nova V2'
)

$ErrorActionPreference = 'Stop'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run from an elevated (Administrator) PowerShell."
    exit 2
}

$nssm = (Get-Command $NssmExe -ErrorAction SilentlyContinue)?.Source
if (-not $nssm) {
    Write-Error @"
nssm.exe not found in PATH. Install via:
  1. Download https://nssm.cc/release/nssm-2.24.zip
  2. Extract win64\nssm.exe to e.g. C:\Tools\nssm.exe
  3. Add C:\Tools to PATH OR pass -NssmExe 'C:\Tools\nssm.exe'
"@
    exit 3
}

foreach ($p in @($BridgeRoot, $ConfigPath, $PythonExe)) {
    if (-not (Test-Path $p)) { Write-Error "missing_path: $p"; exit 4 }
}

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$stdoutLog = Join-Path $LogDir 'nova_host_bridge.log'
$stderrLog = Join-Path $LogDir 'nova_host_bridge.err.log'

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Write-Host "Existing service '$ServiceName' found - stopping + removing." -ForegroundColor Yellow
    & $nssm stop   $ServiceName confirm | Out-Null
    & $nssm remove $ServiceName confirm | Out-Null
    Start-Sleep -Seconds 1
}

Write-Host "Installing NSSM service '$ServiceName' ..." -ForegroundColor Cyan
& $nssm install $ServiceName $PythonExe `
    '-m' 'uvicorn' 'main:app' '--host' '0.0.0.0' '--port' $BindPort `
    '--log-level' 'info' '--no-access-log' | Out-Null

& $nssm set $ServiceName AppDirectory          $BridgeRoot                       | Out-Null
& $nssm set $ServiceName AppEnvironmentExtra   "NOVA_CONFIG_PATH=$ConfigPath"    "PYTHONUNBUFFERED=1" | Out-Null
& $nssm set $ServiceName DisplayName           $DisplayName                      | Out-Null
& $nssm set $ServiceName Description           $Description                      | Out-Null
& $nssm set $ServiceName Start                 SERVICE_AUTO_START                | Out-Null
& $nssm set $ServiceName ObjectName            'LocalSystem'                     | Out-Null

& $nssm set $ServiceName AppStdout             $stdoutLog                        | Out-Null
& $nssm set $ServiceName AppStderr             $stderrLog                        | Out-Null
& $nssm set $ServiceName AppRotateFiles        1                                 | Out-Null
& $nssm set $ServiceName AppRotateOnline       1                                 | Out-Null
& $nssm set $ServiceName AppRotateBytes        10485760                          | Out-Null

& $nssm set $ServiceName AppExit               'Default' 'Restart'               | Out-Null
& $nssm set $ServiceName AppRestartDelay       60000                             | Out-Null
& $nssm set $ServiceName AppThrottle           5000                              | Out-Null

Write-Host "Starting service ..." -ForegroundColor Cyan
& $nssm start $ServiceName | Out-Null
Start-Sleep -Seconds 3

Write-Host "Status:" -ForegroundColor Green
Get-Service -Name $ServiceName | Format-List Name, DisplayName, Status, StartType
Write-Host ""
Write-Host "Logs:        $stdoutLog (rotated at 10 MB)" -ForegroundColor Cyan
Write-Host "Stderr:      $stderrLog" -ForegroundColor Cyan
Write-Host "Stop:        nssm stop   $ServiceName" -ForegroundColor Cyan
Write-Host "Remove:      nssm remove $ServiceName confirm" -ForegroundColor Cyan
Write-Host "Edit GUI:    nssm edit   $ServiceName" -ForegroundColor Cyan
