#requires -RunAsAdministrator
# Stage SSH key and Kuma push URL in C:\ProgramData\nova so the
# LocalSystem-owned NSSM services can read them. Then restart services.
$ErrorActionPreference = 'Stop'

$nssm    = 'L:\tools\nssm\nssm.exe'
$srcKey  = 'C:\Users\awsme\.ssh\id_ed25519'
$dataDir = 'L:\tools\nova\secrets'
$dstKey  = Join-Path $dataDir 'id_ed25519'
$urlFile = Join-Path $dataDir 'push_url.txt'
$secrets = 'L:\!Nova V2\secrets\nova_v2_passwords.txt'
$toolDir = 'L:\tools\nova'
$srcScript  = 'L:\!Nova V2\scripts\bridge_heartbeat.py'
$prodScript = Join-Path $toolDir 'bridge_heartbeat.py'

if (-not (Test-Path $srcKey))  { throw "SSH key missing: $srcKey" }
if (-not (Test-Path $secrets)) { throw "Secrets missing: $secrets" }

# 1) Stage directory + key
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
Copy-Item $srcKey $dstKey -Force
Write-Host "Copied key to $dstKey"

# 2) Lock down ACL: only SYSTEM + Administrators can access
icacls $dstKey /inheritance:r | Out-Null
icacls $dstKey /grant 'SYSTEM:(R)' 'Administrators:(F)' | Out-Null
Write-Host "ACL locked: SYSTEM=Read, Administrators=Full"

# 3) Extract push URL from secrets and write standalone file
$pushUrl = (Select-String -Path $secrets -Pattern '^UPTIME_KUMA_PUSH_URL=' |
            Select-Object -First 1).Line -replace '^UPTIME_KUMA_PUSH_URL=', ''
if (-not $pushUrl) { throw "UPTIME_KUMA_PUSH_URL is empty in $secrets" }
Set-Content -Path $urlFile -Value $pushUrl -NoNewline -Encoding utf8
icacls $urlFile /inheritance:r | Out-Null
icacls $urlFile /grant 'SYSTEM:(R)' 'Administrators:(F)' | Out-Null
Write-Host "Push URL written: $urlFile"

# 4) Refresh production heartbeat script copy
Copy-Item $srcScript $prodScript -Force
Write-Host "Refreshed $prodScript"

# 5) Update tunnel service to use new key path
Stop-Service NOVA_Kuma_Tunnel -ErrorAction SilentlyContinue
Stop-Service NOVA_Heartbeat   -ErrorAction SilentlyContinue
Start-Sleep 2

$sshArgs = @(
    '-N',
    '-L', '127.0.0.1:3001:127.0.0.1:3001',
    '-i', $dstKey,
    '-o', 'StrictHostKeyChecking=accept-new',
    '-o', 'ServerAliveInterval=30',
    '-o', 'ServerAliveCountMax=3',
    '-o', 'ExitOnForwardFailure=yes',
    '-o', 'BatchMode=yes',
    '-p', '22',
    'root@178.104.207.194'
) -join ' '
& $nssm set NOVA_Kuma_Tunnel AppParameters $sshArgs | Out-Null
Write-Host "Updated tunnel AppParameters with key $dstKey"

# 6) Start in correct order
Write-Host 'Starting NOVA_Kuma_Tunnel ...'
Start-Service NOVA_Kuma_Tunnel -ErrorAction Continue
Start-Sleep 5

Write-Host 'Starting NOVA_Heartbeat ...'
Start-Service NOVA_Heartbeat -ErrorAction Continue
Start-Sleep 5

Get-Service NOVA_Kuma_Tunnel, NOVA_Heartbeat | Format-Table Name, Status, StartType -AutoSize

Write-Host '--- tunnel test ---'
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:3001/' -UseBasicParsing -TimeoutSec 5
    Write-Host ("kuma via tunnel http={0}" -f $r.StatusCode)
} catch {
    Write-Host ("tunnel test FAILED: {0}" -f $_.Exception.Message)
}

$tunLog = 'L:\!Nova V2\logs\kuma_tunnel_stderr.log'
if (Test-Path $tunLog) {
    Write-Host '--- kuma_tunnel_stderr.log tail ---'
    Get-Content $tunLog -Tail 5
}

$hbLog = 'L:\!Nova V2\logs\heartbeat.log'
if (Test-Path $hbLog) {
    Write-Host '--- heartbeat.log tail ---'
    Get-Content $hbLog -Tail 5
}
