param(
    [string]$WebhookUrl = "http://127.0.0.1:8088/lifecycle"
)

$ErrorActionPreference = "SilentlyContinue"
$logDir = "C:\nova\logs"
$logPath = Join-Path $logDir "lifecycle.log"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

# Give network/docker a short stabilization window after boot.
Start-Sleep -Seconds 30

$payload = @{
    event = "startup"
    host = "nova-desktop"
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Compress

try {
    Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 5 | Out-Null
    Add-Content -Path $logPath -Value "[$((Get-Date).ToString('s'))] startup notify sent"
} catch {
    Add-Content -Path $logPath -Value "[$((Get-Date).ToString('s'))] startup notify failed: $($_.Exception.Message)"
}
exit 0
