<#
.SYNOPSIS
    Wrapper to start nova_host_bridge in USER-context on port 8501.

.DESCRIPTION
    Sidecar variant of start_bridge_service.ps1. Runs as the interactive
    desktop user so that tools needing a user profile work:
      - Aseprite (Steam DRM, requires user session)
      - Krita    (Qt profile, D-Bus/COM on user desktop)
      - (future) other GUI-ish tools

    The main bridge runs on 8500 as SYSTEM and proxies /aseprite/* and
    /krita/* requests to this sidecar at 127.0.0.1:8501. Agents keep
    talking to one URL.

    Triggered by Task Scheduler "at user logon", so no stored password
    is needed. Starts within seconds of login and stays up until logout.

.NOTES
    Runs same FastAPI app as the main bridge; differentiation is only
    port + workdir/log paths + the fact that in user context the full
    set of tools is actually functional.
#>
[CmdletBinding()]
param(
    [string]$BridgeRoot       = 'L:\!Nova V2\nova_host_bridge',
    [string]$ConfigPath       = 'L:\!Nova V2\nova_config.yaml',
    [string]$PythonExe        = 'C:\Python314\python.exe',
    [string]$BindHost         = '127.0.0.1',  # loopback only - proxied from main bridge on 8500
    [int]   $BindPort         = 8501,
    [string]$LogPath          = 'L:\!Nova V2\nova_host_bridge_sidecar.log',
    [int]   $LogRotateMb      = 10,
    [int]   $MaxRestarts      = 3,
    [int]   $RestartDelaySec  = 30,  # shorter than main bridge - user tools often flaky
    [int]   $HealthyRunSec    = 180
)

$ErrorActionPreference = 'Continue'

function Write-SidecarLog {
    param([string]$Message, [string]$Level = 'INFO')
    $ts = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')
    $line = "[$ts] [$Level] $Message"
    $logDir = Split-Path -Parent $LogPath
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir -ErrorAction SilentlyContinue | Out-Null
    }
    if ((Test-Path $LogPath) -and ((Get-Item $LogPath -ErrorAction SilentlyContinue).Length -gt ($LogRotateMb * 1MB))) {
        $bak = "$LogPath.1"
        if (Test-Path $bak) { Remove-Item $bak -Force -ErrorAction SilentlyContinue }
        Move-Item $LogPath $bak -Force -ErrorAction SilentlyContinue
    }
    Add-Content -Path $LogPath -Value $line -Encoding UTF8 -ErrorAction SilentlyContinue
    Write-Host $line
}

Write-SidecarLog "starting nova_host_bridge SIDECAR pid=$PID user=$env:USERNAME"
Write-SidecarLog "BridgeRoot=$BridgeRoot ConfigPath=$ConfigPath PythonExe=$PythonExe Bind=${BindHost}:${BindPort}"

$missing = @()
if (-not (Test-Path $BridgeRoot)) { $missing += "BridgeRoot=$BridgeRoot" }
if (-not (Test-Path $ConfigPath)) { $missing += "ConfigPath=$ConfigPath" }
if (-not (Test-Path $PythonExe))  { $missing += "PythonExe=$PythonExe" }
if ($missing.Count -gt 0) {
    Write-SidecarLog "wrapper_fatal: missing paths: $($missing -join ', ')" 'ERROR'
    exit 2
}

Set-Location -LiteralPath $BridgeRoot
$env:NOVA_CONFIG_PATH  = $ConfigPath
$env:PYTHONUNBUFFERED  = '1'
# Role flag so the FastAPI app can differentiate its /health + /tools output.
$env:BRIDGE_ROLE       = 'sidecar_user'

$uviArgs = @(
    '-m', 'uvicorn', 'main:app',
    '--host', $BindHost,
    '--port', $BindPort,
    '--log-level', 'warning',
    '--no-access-log'
)

$uviStdout = "$LogPath.uvicorn"
$uviStderr = "$LogPath.uvicorn.err"
Write-SidecarLog "exec: $PythonExe $($uviArgs -join ' ')"
Write-SidecarLog "uvicorn stdout -> $uviStdout"
Write-SidecarLog "uvicorn stderr -> $uviStderr"
Write-SidecarLog "retry policy: max=$MaxRestarts delay=${RestartDelaySec}s healthy_after=${HealthyRunSec}s"

$attempt = 0
$code    = 0
while ($true) {
    $attempt++
    $runStart = Get-Date
    Write-SidecarLog "attempt $attempt of $($MaxRestarts + 1): launching uvicorn"

    $proc = Start-Process -FilePath $PythonExe `
        -ArgumentList $uviArgs `
        -WorkingDirectory $BridgeRoot `
        -NoNewWindow `
        -RedirectStandardOutput $uviStdout `
        -RedirectStandardError  $uviStderr `
        -PassThru

    if ($null -eq $proc) {
        Write-SidecarLog "wrapper_fatal: Start-Process returned null" 'ERROR'
        exit 3
    }

    Write-SidecarLog "uvicorn pid=$($proc.Id)"
    $proc.WaitForExit()
    $code = $proc.ExitCode
    if ($null -eq $code) { $code = -1 }
    $runSec = [int]((Get-Date) - $runStart).TotalSeconds
    Write-SidecarLog "uvicorn exited code=$code after ${runSec}s (see $uviStdout / $uviStderr)" 'WARN'

    if ($code -eq 0) { Write-SidecarLog "clean exit: not restarting"; break }
    if ($runSec -ge $HealthyRunSec) { Write-SidecarLog "run lasted >${HealthyRunSec}s -> treating as healthy; resetting attempt counter"; $attempt = 0 }
    if ($attempt -gt $MaxRestarts) { Write-SidecarLog "max_restarts=$MaxRestarts exceeded; giving up" 'ERROR'; break }

    Write-SidecarLog "retrying in ${RestartDelaySec}s (attempt $($attempt + 1) of $($MaxRestarts + 1))"
    Start-Sleep -Seconds $RestartDelaySec
}

exit $code
