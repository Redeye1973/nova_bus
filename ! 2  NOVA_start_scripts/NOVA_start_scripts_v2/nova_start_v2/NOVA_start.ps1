# NOVA_start.ps1
# Compatible met PowerShell 5.1 en 7.x
# Geen bash syntax, geen && of ||, geen complexe nested try-catch

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "NOVA Startup"

# ------------------ Helpers ------------------
function Say-Info($m)    { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Say-OK($m)      { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Say-Warn($m)    { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Say-Err($m)     { Write-Host "[FAIL] $m" -ForegroundColor Red }
function Say-Section($m) {
    Write-Host ""
    Write-Host "=== $m ===" -ForegroundColor Magenta
}

# ------------------ Config ------------------
$HetznerIP   = "178.104.207.194"
$V1_URL      = "http://" + $HetznerIP + ":5678"
$V2_URL      = "http://" + $HetznerIP + ":5679"
$BridgeURL   = "http://localhost:8500/health"
$OllamaURL   = "http://localhost:11434/api/tags"

$timeStart = Get-Date

Write-Host ""
Write-Host "=================================" -ForegroundColor Magenta
$timeNow = Get-Date -Format 'HH:mm:ss'
Write-Host " NOVA Startup - $timeNow" -ForegroundColor Magenta
Write-Host "=================================" -ForegroundColor Magenta

# ============================================================
# 1. Tailscale
# ============================================================
Say-Section "Tailscale"

$tailscaleBin = "C:\Program Files\Tailscale\tailscale.exe"
if (Test-Path $tailscaleBin) {
    $tsService = Get-Service -Name "Tailscale" -ErrorAction SilentlyContinue
    if ($tsService -and $tsService.Status -ne "Running") {
        Say-Info "Tailscale service starten..."
        Start-Service -Name "Tailscale" -ErrorAction SilentlyContinue
        Start-Sleep 3
    }
    try {
        $tsStatus = & $tailscaleBin status 2>&1
        if ($LASTEXITCODE -eq 0) {
            Say-OK "Tailscale actief"
            $tsStatus | Select-Object -First 3 | ForEach-Object {
                Write-Host "       $_" -ForegroundColor DarkGray
            }
        } else {
            Say-Info "Tailscale up command..."
            & $tailscaleBin up 2>&1 | Out-Null
            Start-Sleep 2
            Say-OK "Tailscale up gestuurd"
        }
    } catch {
        Say-Warn "Tailscale status check faalde"
    }
} else {
    Say-Warn "Tailscale niet gevonden op $tailscaleBin"
}

# ============================================================
# 2. Ollama
# ============================================================
Say-Section "Ollama"

$ollamaService = Get-Service -Name "Ollama" -ErrorAction SilentlyContinue
$ollamaProc = Get-Process -Name "ollama*" -ErrorAction SilentlyContinue

if ($ollamaService) {
    if ($ollamaService.Status -ne "Running") {
        Say-Info "Ollama service starten..."
        Start-Service -Name "Ollama" -ErrorAction SilentlyContinue
        Start-Sleep 3
    }
} elseif (-not $ollamaProc) {
    $ollamaBin = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaBin) {
        Say-Info "Ollama serve starten op achtergrond..."
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep 4
    } else {
        Say-Warn "Ollama niet in PATH, service ontbreekt"
    }
}

try {
    $resp = Invoke-WebRequest -Uri $OllamaURL -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $data = $resp.Content | ConvertFrom-Json
    $modelCount = $data.models.Count
    Say-OK "Ollama bereikbaar - $modelCount models"
    $data.models | Select-Object -First 5 | ForEach-Object {
        Write-Host "       - $($_.name)" -ForegroundColor DarkGray
    }
} catch {
    Say-Warn "Ollama niet bereikbaar op :11434"
}

# ============================================================
# 3. NOVA lokale services
# ============================================================
Say-Section "NOVA lokale services"

$novaServices = @("NOVA_Bridge_Service", "NOVA_Bridge_Watchdog", "NOVA_Heartbeat")
$anyInstalled = $false

foreach ($svcName in $novaServices) {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc) {
        $anyInstalled = $true
        if ($svc.Status -ne "Running") {
            Say-Info "$svcName starten..."
            Start-Service -Name $svcName -ErrorAction SilentlyContinue
            Start-Sleep 2
            $svc.Refresh()
            if ($svc.Status -eq "Running") {
                Say-OK "$svcName running"
            } else {
                Say-Err "$svcName start mislukt"
            }
        } else {
            Say-OK "$svcName al running"
        }
    } else {
        Say-Warn "$svcName niet geinstalleerd"
    }
}

# Fallback bridge als NSSM niet aanwezig
if (-not $anyInstalled) {
    Say-Info "Geen NSSM services. Fallback bridge start..."
    $startScript = "L:\!Nova V2\scripts\start_bridge.ps1"
    if (Test-Path $startScript) {
        $psArgs = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startScript`""
        Start-Process powershell.exe -ArgumentList $psArgs -WindowStyle Hidden
        Start-Sleep 5
        Say-OK "Bridge start commando gestuurd"
    } else {
        Say-Warn "start_bridge.ps1 niet gevonden"
    }
}

# ============================================================
# 4. Bridge health
# ============================================================
Say-Section "Bridge health"

$bridgeOK = $false
$tries = 0
while (-not $bridgeOK -and $tries -lt 3) {
    try {
        $r = Invoke-WebRequest -Uri $BridgeURL -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            Say-OK "Bridge online op :8500"
            $bridgeOK = $true
        }
    } catch {
        $tries++
        if ($tries -lt 3) {
            Say-Info "Wachten 3s... (poging $tries van 3)"
            Start-Sleep 3
        }
    }
}
if (-not $bridgeOK) {
    Say-Err "Bridge niet bereikbaar op :8500"
}

# ============================================================
# 5. SSH Hetzner test
# ============================================================
Say-Section "Hetzner SSH"

$sshOK = $false
try {
    $sshOut = & ssh "-o" "BatchMode=yes" "-o" "ConnectTimeout=5" "root@$HetznerIP" "echo OK" 2>&1
    $sshStr = [string]$sshOut
    if ($sshStr -match "OK") {
        Say-OK "SSH naar Hetzner werkt"
        $sshOK = $true
    } else {
        Say-Err "SSH output onverwacht: $sshStr"
    }
} catch {
    Say-Err "SSH command faalde"
}

# ============================================================
# 6. Hetzner containers check
# ============================================================
if ($sshOK) {
    Say-Section "Hetzner containers (V1 + V2)"
    try {
        $cmd = 'docker ps --format "{{.Names}}|{{.Status}}" | grep -E "nova-|n8n-"'
        $containers = & ssh "-o" "BatchMode=yes" "root@$HetznerIP" $cmd 2>&1
        if ($containers) {
            $lines = $containers -split "`n"
            foreach ($line in $lines) {
                if ($line -and $line.Trim() -ne "") {
                    $parts = $line -split '\|'
                    $name = $parts[0]
                    $status = $parts[1]
                    if ($status -match "Up") {
                        Say-OK "$name"
                    } else {
                        Say-Warn "$name - $status"
                    }
                }
            }
        } else {
            Say-Warn "Geen containers gevonden"
        }
    } catch {
        Say-Warn "Container check faalde"
    }
}

# ============================================================
# 7. V1 + V2 endpoint health
# ============================================================
Say-Section "V1 + V2 endpoint health"

$endpoints = @(
    @{ Name = "V1 N8n";      Url = $V1_URL },
    @{ Name = "V2 N8n";      Url = $V2_URL }
)

foreach ($ep in $endpoints) {
    try {
        $r = Invoke-WebRequest -Uri $ep.Url -UseBasicParsing -TimeoutSec 8 -ErrorAction Stop
        Say-OK "$($ep.Name) - HTTP $($r.StatusCode)"
    } catch {
        $errMsg = $_.Exception.Message
        if ($errMsg -match "401" -or $errMsg -match "403") {
            Say-OK "$($ep.Name) - service running (auth required)"
        } elseif ($errMsg -match "302" -or $errMsg -match "redirect") {
            Say-OK "$($ep.Name) - service running (redirect)"
        } else {
            Say-Err "$($ep.Name) niet bereikbaar"
        }
    }
}

# ============================================================
# Samenvatting
# ============================================================
$elapsed = (Get-Date) - $timeStart
$elapsedSec = [math]::Round($elapsed.TotalSeconds, 1)

Say-Section "Klaar"
Write-Host "Totale tijd: $elapsedSec sec" -ForegroundColor Cyan
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  V1 N8n:       $V1_URL" -ForegroundColor White
Write-Host "  V2 N8n:       $V2_URL" -ForegroundColor White
Write-Host "  Bridge tools: http://localhost:8500/tools" -ForegroundColor White
Write-Host "  Ollama:       http://localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "NOVA ready." -ForegroundColor Green
Write-Host ""
