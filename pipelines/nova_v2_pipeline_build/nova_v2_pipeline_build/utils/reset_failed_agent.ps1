# Reset Failed Agent
# Rollback een specifieke agent zodat je opnieuw kunt proberen

param(
    [Parameter(Mandatory=$true)]
    [string]$AgentNumber,
    [switch]$KeepContainer,
    [switch]$Force
)

$agentNumPadded = $AgentNumber.PadLeft(2, '0')

Write-Host ""
Write-Host "=== Reset Agent $agentNumPadded ===" -ForegroundColor Cyan
Write-Host ""

# Check status
$statusFile = "L:\!Nova V2\status\agent_${agentNumPadded}_status.json"

if (-not (Test-Path $statusFile)) {
    Write-Host "Status file niet gevonden: $statusFile" -ForegroundColor Yellow
    Write-Host "Agent was mogelijk nooit gebouwd. Continue met cleanup." -ForegroundColor Yellow
} else {
    $status = Get-Content $statusFile -Raw | ConvertFrom-Json
    Write-Host "Huidige status:" -ForegroundColor Gray
    Write-Host "  Name: $($status.name)"
    Write-Host "  Status: $($status.status)"
    Write-Host "  Webhook: $($status.webhook_url)"
    Write-Host ""
}

# Confirm
if (-not $Force) {
    $confirm = Read-Host "Reset deze agent? (y/N)"
    if ($confirm -ne "y") {
        Write-Host "Geannuleerd." -ForegroundColor Yellow
        exit 0
    }
}

# Load V2 API key
try {
    $v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" | Where-Object { $_ -match "N8N_V2_API_KEY" } | Select-Object -First 1) -replace ".*N8N_V2_API_KEY\s*=\s*", ""
    $v2key = $v2key.Trim()
} catch {
    Write-Host "Kan V2 API key niet laden: $_" -ForegroundColor Red
    exit 1
}

# Step 1: Deactivate + delete N8n workflow
if ($status -and $status.workflow_id) {
    Write-Host "Stap 1: Deactiveer N8n workflow $($status.workflow_id)..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows/$($status.workflow_id)/deactivate" `
            -Method POST -Headers @{"X-N8N-API-KEY"=$v2key} -ErrorAction SilentlyContinue
        Write-Host "  Workflow deactivated" -ForegroundColor Green
    } catch {
        Write-Host "  Kan niet deactivaten: $_" -ForegroundColor Yellow
    }
    
    # Optional: delete workflow
    $deleteWf = Read-Host "Delete workflow ook? (y/N)"
    if ($deleteWf -eq "y") {
        try {
            Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows/$($status.workflow_id)" `
                -Method DELETE -Headers @{"X-N8N-API-KEY"=$v2key}
            Write-Host "  Workflow deleted" -ForegroundColor Green
        } catch {
            Write-Host "  Delete failed: $_" -ForegroundColor Yellow
        }
    }
}

# Step 2: Stop container
if (-not $KeepContainer) {
    Write-Host "Stap 2: Stop Docker container..." -ForegroundColor Cyan
    $containerPattern = "agent-$agentNumPadded"
    
    $sshCmd = "cd /docker/nova-v2 && docker compose ps --services | grep '$containerPattern' | head -1"
    $serviceName = ssh root@178.104.207.194 $sshCmd
    
    if ($serviceName) {
        $serviceName = $serviceName.Trim()
        Write-Host "  Service gevonden: $serviceName" -ForegroundColor Gray
        
        ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose stop $serviceName"
        Write-Host "  Container stopped" -ForegroundColor Green
        
        $removeContainer = Read-Host "Remove container? (y/N)"
        if ($removeContainer -eq "y") {
            ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose rm -f $serviceName"
            Write-Host "  Container removed" -ForegroundColor Green
        }
    } else {
        Write-Host "  Geen container gevonden voor pattern '$containerPattern'" -ForegroundColor Yellow
    }
}

# Step 3: Move status file
if (Test-Path $statusFile) {
    Write-Host "Stap 3: Archief status file..." -ForegroundColor Cyan
    $backupDir = "L:\!Nova V2\status\archive"
    if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Force -Path $backupDir | Out-Null }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $backupFile = "$backupDir\agent_${agentNumPadded}_status_${timestamp}.json"
    Move-Item $statusFile $backupFile
    Write-Host "  Status archived: $backupFile" -ForegroundColor Green
}

# Step 4: Log reset
Write-Host "Stap 4: Log reset actie..." -ForegroundColor Cyan
$logFile = "L:\!Nova V2\logs\pipeline_build_$(Get-Date -Format 'yyyy-MM-dd').log"
$logEntry = "$(Get-Date -Format 'o') | agent_${agentNumPadded} | RESET | User-initiated via reset_failed_agent.ps1"
Add-Content $logFile $logEntry
Write-Host "  Log entry added" -ForegroundColor Green

Write-Host ""
Write-Host "=== Reset compleet ===" -ForegroundColor Green
Write-Host "Agent $agentNumPadded is teruggezet. Je kunt nu de prompt opnieuw uitvoeren." -ForegroundColor Green
Write-Host ""
Write-Host "Volgende stappen:" -ForegroundColor Gray
Write-Host "  1. Open de relevante prompt file in nova_v2_pipeline_build/" -ForegroundColor Gray
Write-Host "  2. Plak in Cursor Composer" -ForegroundColor Gray
Write-Host "  3. Laat Cursor opnieuw bouwen" -ForegroundColor Gray
