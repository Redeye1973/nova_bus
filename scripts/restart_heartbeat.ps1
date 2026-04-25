#requires -RunAsAdministrator
# Refreshes heartbeat script + push_url.txt (no BOM) and restarts service.
$ErrorActionPreference = 'Stop'

$srcScript  = 'L:\!Nova V2\scripts\bridge_heartbeat.py'
$prodScript = 'L:\tools\nova\bridge_heartbeat.py'
$urlFile    = 'L:\tools\nova\secrets\push_url.txt'
$secrets    = 'L:\!Nova V2\secrets\nova_v2_passwords.txt'

# Refresh heartbeat script
Copy-Item $srcScript $prodScript -Force
Write-Host "Refreshed $prodScript"

# Rewrite push_url.txt WITHOUT BOM
$pushUrl = (Select-String -Path $secrets -Pattern '^UPTIME_KUMA_PUSH_URL=' |
            Select-Object -First 1).Line -replace '^UPTIME_KUMA_PUSH_URL=', ''
if (-not $pushUrl) { throw "UPTIME_KUMA_PUSH_URL is empty" }
$enc = New-Object System.Text.UTF8Encoding $false   # false = no BOM
[System.IO.File]::WriteAllText($urlFile, $pushUrl, $enc)
icacls $urlFile /inheritance:r | Out-Null
icacls $urlFile /grant 'SYSTEM:(R)' 'Administrators:(F)' | Out-Null
Write-Host "Rewrote $urlFile (no BOM)"

# Truncate heartbeat log so we can see fresh entries
Clear-Content 'L:\!Nova V2\logs\heartbeat.log' -ErrorAction SilentlyContinue

Write-Host 'Restarting NOVA_Heartbeat ...'
Restart-Service NOVA_Heartbeat -Force
Start-Sleep 8

Get-Service NOVA_Heartbeat | Format-Table Name, Status, StartType -AutoSize

Write-Host '--- heartbeat.log (fresh) ---'
Get-Content 'L:\!Nova V2\logs\heartbeat.log' -Tail 10 -ErrorAction SilentlyContinue
