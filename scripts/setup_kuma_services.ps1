#requires -RunAsAdministrator
# Installs two NSSM services:
#   NOVA_Kuma_Tunnel   - permanent SSH tunnel PC:3001 -> prod:127.0.0.1:3001
#   NOVA_Heartbeat     - pushes bridge /health to Uptime Kuma every 60s
# Idempotent: removes existing services first.
$ErrorActionPreference = 'Stop'

$nssm    = 'L:\tools\nssm\nssm.exe'
$python  = 'C:\Python314\python.exe'
$siteDir = 'C:\Users\awsme\AppData\Roaming\Python\Python314\site-packages'
$ssh     = 'C:\Windows\System32\OpenSSH\ssh.exe'
$sshKey  = 'C:\Users\awsme\.ssh\id_ed25519'
$logDir  = 'L:\!Nova V2\logs'
$toolDir = 'L:\tools\nova'

if (-not (Test-Path $nssm))   { throw "NSSM missing: $nssm" }
if (-not (Test-Path $python)) { throw "Python missing: $python" }
if (-not (Test-Path $ssh))    { throw "ssh.exe missing: $ssh" }
if (-not (Test-Path $sshKey)) { throw "SSH key missing: $sshKey" }

New-Item -ItemType Directory -Force -Path $toolDir, $logDir | Out-Null

function Remove-IfExists($name) {
    if (Get-Service $name -ErrorAction SilentlyContinue) {
        Write-Host "Removing existing service $name ..."
        Stop-Service $name -ErrorAction SilentlyContinue
        Start-Sleep 2
        & $nssm remove $name confirm | Out-Null
        Start-Sleep 1
    }
}

# ============================================================
# 1) NOVA_Kuma_Tunnel
# ============================================================
$svcTunnel = 'NOVA_Kuma_Tunnel'
Remove-IfExists $svcTunnel

# ssh args: -N (no command) -L (forward) + keepalive + accept-new + key + retry on fail
$sshArgs = @(
    '-N',
    '-L', '127.0.0.1:3001:127.0.0.1:3001',
    '-i', $sshKey,
    '-o', 'StrictHostKeyChecking=accept-new',
    '-o', 'ServerAliveInterval=30',
    '-o', 'ServerAliveCountMax=3',
    '-o', 'ExitOnForwardFailure=yes',
    '-o', 'BatchMode=yes',
    '-p', '22',
    'root@178.104.207.194'
) -join ' '

Write-Host "Installing $svcTunnel ..."
& $nssm install $svcTunnel $ssh $sshArgs                              | Out-Null
& $nssm set $svcTunnel AppDirectory      'C:\Windows\System32\OpenSSH' | Out-Null
& $nssm set $svcTunnel DisplayName       'NOVA Uptime Kuma SSH Tunnel' | Out-Null
& $nssm set $svcTunnel Description       'Forwards PC:3001 -> prod:3001 for Uptime Kuma access' | Out-Null
& $nssm set $svcTunnel Start             SERVICE_AUTO_START            | Out-Null
& $nssm set $svcTunnel AppStdout         (Join-Path $logDir 'kuma_tunnel_stdout.log') | Out-Null
& $nssm set $svcTunnel AppStderr         (Join-Path $logDir 'kuma_tunnel_stderr.log') | Out-Null
& $nssm set $svcTunnel AppRotateFiles    1                             | Out-Null
& $nssm set $svcTunnel AppRotateBytes    10485760                       | Out-Null
& $nssm set $svcTunnel AppExit           Default Restart               | Out-Null
& $nssm set $svcTunnel AppRestartDelay   5000                          | Out-Null
& $nssm set $svcTunnel AppThrottle       10000                         | Out-Null

# ============================================================
# 2) NOVA_Heartbeat
# ============================================================
$svcHeart = 'NOVA_Heartbeat'
Remove-IfExists $svcHeart

$srcScript  = 'L:\!Nova V2\scripts\bridge_heartbeat.py'
$prodScript = Join-Path $toolDir 'bridge_heartbeat.py'
if (-not (Test-Path $srcScript)) { throw "Heartbeat script missing: $srcScript" }
Copy-Item $srcScript $prodScript -Force
Write-Host "Copied heartbeat script to $prodScript"

Write-Host "Installing $svcHeart ..."
& $nssm install $svcHeart $python $prodScript                          | Out-Null
& $nssm set $svcHeart AppDirectory      $toolDir                       | Out-Null
& $nssm set $svcHeart DisplayName       'NOVA Bridge Heartbeat'        | Out-Null
& $nssm set $svcHeart Description       'Pushes bridge /health to Uptime Kuma every 60s' | Out-Null
& $nssm set $svcHeart Start             SERVICE_AUTO_START             | Out-Null
& $nssm set $svcHeart AppStdout         (Join-Path $logDir 'heartbeat_stdout.log') | Out-Null
& $nssm set $svcHeart AppStderr         (Join-Path $logDir 'heartbeat_stderr.log') | Out-Null
& $nssm set $svcHeart AppRotateFiles    1                              | Out-Null
& $nssm set $svcHeart AppRotateBytes    10485760                        | Out-Null
& $nssm set $svcHeart AppExit           Default Restart                | Out-Null
& $nssm set $svcHeart AppRestartDelay   5000                           | Out-Null
& $nssm set $svcHeart AppThrottle       10000                          | Out-Null
& $nssm set $svcHeart AppEnvironmentExtra "PYTHONPATH=$siteDir"        | Out-Null

# ============================================================
# Start services in correct order: tunnel first, then heartbeat
# ============================================================
Write-Host "Starting $svcTunnel ..."
Start-Service $svcTunnel -ErrorAction Continue
Start-Sleep 5

Write-Host "Starting $svcHeart ..."
Start-Service $svcHeart -ErrorAction Continue
Start-Sleep 5

Get-Service $svcTunnel, $svcHeart | Format-Table Name, Status, StartType -AutoSize

Write-Host '--- tunnel test ---'
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:3001/' -UseBasicParsing -TimeoutSec 5
    Write-Host ("kuma via tunnel http={0}" -f $r.StatusCode)
} catch {
    Write-Host ("tunnel test FAILED: {0}" -f $_.Exception.Message)
}

$hbLog = Join-Path $logDir 'heartbeat.log'
if (Test-Path $hbLog) {
    Write-Host '--- heartbeat.log tail ---'
    Get-Content $hbLog -Tail 5
} else {
    Write-Host 'heartbeat.log nog niet aangemaakt - geef de service ~70s'
}
