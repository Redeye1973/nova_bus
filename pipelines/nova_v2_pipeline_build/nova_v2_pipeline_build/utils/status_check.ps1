# NOVA v2 Pipeline Status Check
# Toont overzicht van alle agents en hun status

param(
    [switch]$Detailed,
    [switch]$FallbackOnly,
    [switch]$FailedOnly,
    [string]$AgentNumber
)

$statusDir = "L:\!Nova V2\status"

if (-not (Test-Path $statusDir)) {
    Write-Host "Status directory niet gevonden: $statusDir" -ForegroundColor Red
    exit 1
}

$files = Get-ChildItem -Path $statusDir -Filter "agent_*_status.json"

if ($files.Count -eq 0) {
    Write-Host "Geen agent status files gevonden" -ForegroundColor Yellow
    exit 0
}

$agents = @()
foreach ($file in $files) {
    try {
        $s = Get-Content $file.FullName -Raw | ConvertFrom-Json
        $agents += $s
    } catch {
        Write-Warning "Kan $($file.Name) niet parsen: $_"
    }
}

# Filter
if ($AgentNumber) {
    $agents = $agents | Where-Object { $_.agent_number -eq $AgentNumber }
}
if ($FallbackOnly) {
    $agents = $agents | Where-Object { $_.fallback_mode -eq $true }
}
if ($FailedOnly) {
    $agents = $agents | Where-Object { $_.status -eq "failed" }
}

# Sorteer op agent_number
$agents = $agents | Sort-Object { [int]$_.agent_number }

# Summary
$total = $agents.Count
$active = ($agents | Where-Object { $_.status -eq "active" }).Count
$fallback = ($agents | Where-Object { $_.fallback_mode -eq $true }).Count
$failed = ($agents | Where-Object { $_.status -eq "failed" }).Count

Write-Host ""
Write-Host "=== NOVA v2 Pipeline Status ===" -ForegroundColor Cyan
Write-Host "Total agents: $total"
Write-Host "Active: $active" -ForegroundColor Green
Write-Host "Fallback mode: $fallback" -ForegroundColor Yellow
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

# Per agent
if ($Detailed) {
    foreach ($a in $agents) {
        $color = switch ($a.status) {
            "active" { if ($a.fallback_mode) { "Yellow" } else { "Green" } }
            "failed" { "Red" }
            default { "Gray" }
        }
        
        Write-Host "Agent $($a.agent_number) - $($a.name)" -ForegroundColor $color
        Write-Host "  Status: $($a.status)$(if ($a.fallback_mode) { ' (FALLBACK)' })"
        Write-Host "  Built: $($a.built_at)"
        Write-Host "  Webhook: $($a.webhook_url)"
        if ($a.notes) { Write-Host "  Notes: $($a.notes)" -ForegroundColor Gray }
        Write-Host ""
    }
} else {
    # Compact view
    Write-Host "# | Agent Name | Status | Mode | Webhook"
    Write-Host ("-" * 80)
    foreach ($a in $agents) {
        $statusText = switch ($a.status) {
            "active" { "[OK]" }
            "failed" { "[FAIL]" }
            default { "[???]" }
        }
        $modeText = if ($a.fallback_mode) { "fallback" } else { "full" }
        $webhookShort = if ($a.webhook_url) { $a.webhook_url -replace "http://178\.104\.207\.194:5680", "" } else { "n/a" }
        
        $color = switch ($a.status) {
            "active" { if ($a.fallback_mode) { "Yellow" } else { "Green" } }
            "failed" { "Red" }
            default { "Gray" }
        }
        Write-Host ("{0,-3} | {1,-30} | {2,-6} | {3,-10} | {4}" -f $a.agent_number, $a.name, $statusText, $modeText, $webhookShort) -ForegroundColor $color
    }
}

Write-Host ""
Write-Host "Gebruik -Detailed voor uitgebreide info" -ForegroundColor Gray
Write-Host "Gebruik -FallbackOnly om alleen fallback agents te zien" -ForegroundColor Gray
Write-Host "Gebruik -AgentNumber XX voor specifieke agent" -ForegroundColor Gray
