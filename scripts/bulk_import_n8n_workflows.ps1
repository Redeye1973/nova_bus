# Import alle workflow.json onder infrastructure/services naar n8n V2 (eenmalig).
param(
    [string]$SecretsPath = "L:\!Nova V2\secrets\nova_v2_passwords.txt",
    [string]$BaseUrl = "http://178.104.207.194:5679",
    [string]$ServicesRoot = "L:\!Nova V2\infrastructure\services"
)

$line = Get-Content $SecretsPath | Where-Object { $_ -match '^N8N_V2_API_KEY=' } | Select-Object -First 1
$key = ($line -replace '^N8N_V2_API_KEY\s*=\s*', '').Trim()
$hdr = @{ "X-N8N-API-KEY" = $key; "Content-Type" = "application/json" }

Get-ChildItem -Path $ServicesRoot -Directory | ForEach-Object {
    $wf = Join-Path $_.FullName "workflow.json"
    if (-not (Test-Path $wf)) { return }
    $name = $_.Name
    try {
        $body = Get-Content $wf -Raw
        $r = Invoke-RestMethod -Uri "$BaseUrl/api/v1/workflows" -Method POST -Headers $hdr -Body $body -ErrorAction Stop
        $wid = $r.id
        Invoke-RestMethod -Uri "$BaseUrl/api/v1/workflows/$wid/activate" -Method POST -Headers $hdr -Body "{}" | Out-Null
        Write-Host "OK $name -> $wid"
    } catch {
        Write-Warning "FAIL $name : $($_.Exception.Message)"
    }
    Start-Sleep -Milliseconds 200
}
