<#
.SYNOPSIS
    Wrapper to start nova_host_bridge under Task Scheduler / NSSM.

.DESCRIPTION
    Sets working directory + env vars, then exec's uvicorn via Start-Process
    with stdout/stderr redirected to a dedicated uvicorn log file. The
    wrapper's own supervision messages (start/exit/PID) go to a small
    meta-log alongside.

    Two log files are produced:
      $LogPath              wrapper meta log (append, rotated at 10 MB)
      "$LogPath.uvicorn"    uvicorn stdout (truncated per start; small per run)
      "$LogPath.uvicorn.err" uvicorn stderr (truncated per start)

.NOTES
    Designed to be invoked by:
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File start_bridge_service.ps1
    Returns uvicorn's exit code so the supervisor (Task Scheduler / NSSM)
    can restart on failure.
#>
[CmdletBinding()]
param(
    [string]$BridgeRoot       = 'L:\!Nova V2\nova_host_bridge',
    [string]$ConfigPath       = 'L:\!Nova V2\nova_config.yaml',
    [string]$PythonExe        = 'C:\Python314\python.exe',
    [string]$BindHost         = '0.0.0.0',
    [int]   $BindPort         = 8500,
    [string]$LogPath          = 'L:\!Nova V2\nova_host_bridge.log',
    [int]   $LogRotateMb      = 10,
    # In-wrapper retry loop: if uvicorn exits non-zero, wait $RestartDelaySec
    # and try again, up to $MaxRestarts times. Task Scheduler's own
    # restart-on-failure is unreliable for mid-run process exits, so we
    # handle it here instead.
    [int]   $MaxRestarts      = 3,
    [int]   $RestartDelaySec  = 60,
    # If uvicorn runs longer than this many seconds, the attempt counter is
    # reset to 0 (we consider it a healthy run that later died). Prevents
    # a flaky service from looping forever across days.
    [int]   $HealthyRunSec    = 300
)

$ErrorActionPreference = 'Continue'

function Write-BridgeLog {
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

Write-BridgeLog "starting nova_host_bridge wrapper pid=$PID user=$env:USERNAME"
Write-BridgeLog "BridgeRoot=$BridgeRoot ConfigPath=$ConfigPath PythonExe=$PythonExe Bind=${BindHost}:${BindPort}"

$missing = @()
if (-not (Test-Path $BridgeRoot)) { $missing += "BridgeRoot=$BridgeRoot" }
if (-not (Test-Path $ConfigPath)) { $missing += "ConfigPath=$ConfigPath" }
if (-not (Test-Path $PythonExe))  { $missing += "PythonExe=$PythonExe" }
if ($missing.Count -gt 0) {
    Write-BridgeLog "wrapper_fatal: missing paths: $($missing -join ', ')" 'ERROR'
    exit 2
}

Set-Location -LiteralPath $BridgeRoot
$env:NOVA_CONFIG_PATH  = $ConfigPath
$env:PYTHONUNBUFFERED  = '1'
# Force ignoring user-site so the same deps are loaded whether the wrapper
# runs as SYSTEM (Task Scheduler) or as the desktop user. Without this, an
# interactive run would prefer C:\Users\<u>\AppData\Roaming\Python\... while
# SYSTEM only sees C:\Python314\Lib\site-packages.
$env:PYTHONNOUSERSITE   = '1'

$uviArgs = @(
    '-m', 'uvicorn', 'main:app',
    '--host', $BindHost,
    '--port', $BindPort,
    '--log-level', 'info',
    '--no-access-log'
)

$uviStdout = "$LogPath.uvicorn"
$uviStderr = "$LogPath.uvicorn.err"
Write-BridgeLog "exec: $PythonExe $($uviArgs -join ' ')"
Write-BridgeLog "uvicorn stdout -> $uviStdout"
Write-BridgeLog "uvicorn stderr -> $uviStderr"
Write-BridgeLog "retry policy: max=$MaxRestarts delay=${RestartDelaySec}s healthy_after=${HealthyRunSec}s"

$attempt = 0
$code    = 0
while ($true) {
    $attempt++
    $runStart = Get-Date
    Write-BridgeLog "attempt $attempt of $($MaxRestarts + 1): launching uvicorn"

    # Start-Process with separate redirection files: bullet-proof, supervisor-friendly.
    # Files truncate each start (acceptable: logs stream append via our wrapper meta).
    $proc = Start-Process -FilePath $PythonExe `
        -ArgumentList $uviArgs `
        -WorkingDirectory $BridgeRoot `
        -NoNewWindow `
        -RedirectStandardOutput $uviStdout `
        -RedirectStandardError  $uviStderr `
        -PassThru

    if ($null -eq $proc) {
        Write-BridgeLog "wrapper_fatal: Start-Process returned null" 'ERROR'
        exit 3
    }

    Write-BridgeLog "uvicorn pid=$($proc.Id)"
    $proc.WaitForExit()
    $code = $proc.ExitCode
    if ($null -eq $code) { $code = -1 }
    $runSec = [int]((Get-Date) - $runStart).TotalSeconds
    Write-BridgeLog "uvicorn exited code=$code after ${runSec}s (see $uviStdout / $uviStderr)" 'WARN'

    if ($code -eq 0) {
        Write-BridgeLog "clean exit: not restarting"
        break
    }

    if ($runSec -ge $HealthyRunSec) {
        Write-BridgeLog "run lasted >${HealthyRunSec}s -> treating as healthy; resetting attempt counter"
        $attempt = 0
    }

    if ($attempt -gt $MaxRestarts) {
        Write-BridgeLog "max_restarts=$MaxRestarts exceeded; giving up so Task Scheduler can take over" 'ERROR'
        break
    }

    Write-BridgeLog "retrying in ${RestartDelaySec}s (attempt $($attempt + 1) of $($MaxRestarts + 1))"
    Start-Sleep -Seconds $RestartDelaySec
}

exit $code
