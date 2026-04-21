# Full NOVA v2 Backup
# Maakt complete backup van status, config, databases

param(
    [string]$BackupRoot = "L:\!Nova V2\backups",
    [switch]$IncludePostgres,
    [switch]$IncludeMinIO
)

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupDir = "$BackupRoot\full_$timestamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

Write-Host ""
Write-Host "=== NOVA v2 Full Backup ===" -ForegroundColor Cyan
Write-Host "Backup naar: $backupDir" -ForegroundColor Gray
Write-Host ""

# 1. Status files
Write-Host "Stap 1: Status files..." -ForegroundColor Cyan
$statusSrc = "L:\!Nova V2\status"
if (Test-Path $statusSrc) {
    Copy-Item -Path "$statusSrc\*" -Destination "$backupDir\status\" -Recurse -Force
    $count = (Get-ChildItem "$backupDir\status" -Filter "*.json" -Recurse).Count
    Write-Host "  $count status files" -ForegroundColor Green
}

# 2. Infrastructure config
Write-Host "Stap 2: Infrastructure config..." -ForegroundColor Cyan
$infraSrc = "L:\!Nova V2\infrastructure"
if (Test-Path $infraSrc) {
    New-Item -ItemType Directory -Force -Path "$backupDir\infrastructure" | Out-Null
    Copy-Item "$infraSrc\docker-compose.yml" "$backupDir\infrastructure\" -ErrorAction SilentlyContinue
    Copy-Item "$infraSrc\.env.template" "$backupDir\infrastructure\" -ErrorAction SilentlyContinue
    Copy-Item "$infraSrc\README.md" "$backupDir\infrastructure\" -ErrorAction SilentlyContinue
    # .env opslaan maar versleuteld flag
    if (Test-Path "$infraSrc\.env") {
        Copy-Item "$infraSrc\.env" "$backupDir\infrastructure\.env.SECRET"
        Write-Host "  docker-compose + .env (SECRET copy)" -ForegroundColor Green
    }
}

# 3. Secrets (met waarschuwing)
Write-Host "Stap 3: Secrets..." -ForegroundColor Cyan
$secretsSrc = "L:\!Nova V2\secrets"
if (Test-Path $secretsSrc) {
    New-Item -ItemType Directory -Force -Path "$backupDir\secrets" | Out-Null
    Copy-Item "$secretsSrc\*" "$backupDir\secrets\" -Recurse -Force
    Write-Host "  Secrets backed up - BEWAAR VEILIG!" -ForegroundColor Yellow
}

# 4. V2 services code
Write-Host "Stap 4: V2 services code..." -ForegroundColor Cyan
$servicesSrc = "L:\!Nova V2\v2_services"
if (Test-Path $servicesSrc) {
    # Excl. .venv en __pycache__
    $robocopy = robocopy "$servicesSrc" "$backupDir\v2_services" /E /XD .venv __pycache__ node_modules /XF *.pyc *.log /NFL /NDL /NJH /NJS /NP
    $count = (Get-ChildItem "$backupDir\v2_services" -Directory).Count
    Write-Host "  $count agent service directories" -ForegroundColor Green
}

# 5. Docs
Write-Host "Stap 5: Documentatie..." -ForegroundColor Cyan
$docsSrc = "L:\!Nova V2\docs"
if (Test-Path $docsSrc) {
    Copy-Item -Path "$docsSrc\*" -Destination "$backupDir\docs\" -Recurse -Force
    Write-Host "  Docs gekopieerd" -ForegroundColor Green
}

# 6. Logs (alleen laatste 7 dagen)
Write-Host "Stap 6: Recent logs..." -ForegroundColor Cyan
$logsSrc = "L:\!Nova V2\logs"
if (Test-Path $logsSrc) {
    New-Item -ItemType Directory -Force -Path "$backupDir\logs" | Out-Null
    $cutoff = (Get-Date).AddDays(-7)
    $recentLogs = Get-ChildItem -Path $logsSrc -Filter "*.log" | Where-Object { $_.LastWriteTime -gt $cutoff }
    foreach ($log in $recentLogs) {
        Copy-Item $log.FullName "$backupDir\logs\" -Force
    }
    Write-Host "  $($recentLogs.Count) recent log files" -ForegroundColor Green
}

# 7. PostgreSQL dump (optioneel)
if ($IncludePostgres) {
    Write-Host "Stap 7: PostgreSQL dump..." -ForegroundColor Cyan
    try {
        $dumpCmd = "cd /docker/nova-v2 && docker compose exec -T postgres-v2 pg_dumpall -U postgres | gzip"
        $dumpFile = "$backupDir\postgres_dump_$timestamp.sql.gz"
        
        # Run via SSH, capture output
        ssh root@178.104.207.194 $dumpCmd | Set-Content -Path $dumpFile -AsByteStream
        
        $size = (Get-Item $dumpFile).Length / 1MB
        Write-Host "  Postgres dump: $([math]::Round($size, 2)) MB" -ForegroundColor Green
    } catch {
        Write-Host "  Postgres backup failed: $_" -ForegroundColor Yellow
    }
}

# 8. MinIO data list (niet full backup, zou te groot zijn)
if ($IncludeMinIO) {
    Write-Host "Stap 8: MinIO inventory..." -ForegroundColor Cyan
    try {
        $inventoryFile = "$backupDir\minio_inventory.txt"
        ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose exec -T minio-v2 mc ls -r local/" | Set-Content $inventoryFile
        Write-Host "  MinIO inventory saved" -ForegroundColor Green
    } catch {
        Write-Host "  MinIO inventory failed: $_" -ForegroundColor Yellow
    }
}

# 9. Summary file
$summary = @{
    timestamp = (Get-Date -Format "o")
    backup_dir = $backupDir
    included = @{
        status = Test-Path "$backupDir\status"
        infrastructure = Test-Path "$backupDir\infrastructure"
        secrets = Test-Path "$backupDir\secrets"
        v2_services = Test-Path "$backupDir\v2_services"
        docs = Test-Path "$backupDir\docs"
        logs = Test-Path "$backupDir\logs"
        postgres = $IncludePostgres
        minio = $IncludeMinIO
    }
    total_size_mb = [math]::Round(((Get-ChildItem $backupDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB), 2)
}

$summary | ConvertTo-Json | Out-File "$backupDir\BACKUP_SUMMARY.json"

Write-Host ""
Write-Host "=== Backup Compleet ===" -ForegroundColor Green
Write-Host "Locatie: $backupDir" -ForegroundColor Green
Write-Host "Size: $($summary.total_size_mb) MB" -ForegroundColor Green
Write-Host ""

# Cleanup oude backups (ouder dan 30 dagen)
Write-Host "Cleanup oude backups..." -ForegroundColor Gray
$oldBackups = Get-ChildItem $BackupRoot -Directory | Where-Object { $_.Name -match "^full_" -and $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
foreach ($old in $oldBackups) {
    Write-Host "  Removing: $($old.Name)" -ForegroundColor Gray
    Remove-Item $old.FullName -Recurse -Force
}

Write-Host ""
Write-Host "Klaar!" -ForegroundColor Green
