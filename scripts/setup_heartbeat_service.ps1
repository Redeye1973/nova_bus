#requires -RunAsAdministrator
# Installs NOVA_Heartbeat NSSM service.
# Idempotent: removes existing service first.
$ErrorActionPreference = 'Stop'

$nssm   = 'L:\tools\nssm\nssm.exe'
$python = 'C:\Python314\python.exe'
$siteDir = 'C:\Users\awsme\AppData\Roaming\Python\Python314\site-packages'

$srcScript = 'L:\!Nova V2\scripts\bridge_heartbeat.py'
$prodScript = 'L:\tools\nova\bridge_heartbeat.py'
$logDir   = 'L:\!Nova V2\logs'
$svc = 'NOVA_Heartbeat'

if (-not (Test-Path $nssm))   { throw "NSSM missing: $nssm" }
if (-not (Test-Path $python)) { throw "Python missing: $python" }
if (-not (Test-Path $srcScript)) { throw "Heartbeat script missing: $srcScript" }

New-Item -ItemType Directory -Force -Path 'L:\tools\nova', $logDir | Out-Null
Copy-Item $srcScript $prodScript -Force
Write-Host "Copied script to $prodScript"

if ((Get-Service $svc -ErrorAction SilentlyContinue)) {
    Write-Host "Removing existing $svc service ..."
    Stop-Service $svc -ErrorAction SilentlyContinue
    Start-Sleep 2
    & $nssm remove $svc confirm | Out-Null
    Start-Sleep 1
}

Write-Host "Installing $svc ..."
& $nssm install $svc $python $prodScript | Out-Null
& $nssm set $svc AppDirectory      'L:\tools\nova'                          | Out-Null
& $nssm set $svc DisplayName       'NOVA Bridge Heartbeat (Uptime Kuma push)' | Out-Null
& $nssm set $svc Description       'Pushes bridge /health status to Uptime Kuma every 60s' | Out-Null
& $nssm set $svc Start             SERVICE_AUTO_START                       | Out-Null
& $nssm set $svc AppStdout         (Join-Path $logDir 'heartbeat_stdout.log') | Out-Null
& $nssm set $svc AppStderr         (Join-Path $logDir 'heartbeat_stderr.log') | Out-Null
& $nssm set $svc AppRotateFiles    1                                        | Out-Null
& $nssm set $svc AppRotateBytes    10485760                                  | Out-Null
& $nssm set $svc AppExit           Default Restart                          | Out-Null
& $nssm set $svc AppRestartDelay   5000                                     | Out-Null
& $nssm set $svc AppThrottle       10000                                    | Out-Null
& $nssm set $svc AppEnvironmentExtra "PYTHONPATH=$siteDir"                  | Out-Null

Write-Host "Starting $svc ..."
Start-Service $svc -ErrorAction Continue
Start-Sleep 5
Get-Service $svc | Format-Table Name,Status,StartType -AutoSize

$tail = Join-Path $logDir 'heartbeat.log'
if (Test-Path $tail) {
    Write-Host '--- heartbeat.log tail ---'
    Get-Content $tail -Tail 5
}
