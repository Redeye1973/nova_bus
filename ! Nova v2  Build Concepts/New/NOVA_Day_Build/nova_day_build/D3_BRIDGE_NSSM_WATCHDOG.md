# SESSIE D3 — Bridge als Windows Service + Lokale Watchdog

**Doel:** Bridge crasht = auto-restart binnen 5 sec. Draait zonder login.
**Tijd:** 45-60 min
**Handwerk:** NSSM downloaden (1 min)
**Afhankelijkheid:** Bridge draait minstens één keer (night-sessie 02)

---

## HANDWERK VOORAF

1. Open browser → https://nssm.cc/download
2. Download latest NSSM release (nssm-2.24.zip of nieuwer)
3. Unzip naar bijvoorbeeld `C:\tools\nssm\`
4. Noteer pad naar `nssm.exe` (in `win64\` subfolder voor 64-bit Windows)

Bijv: `C:\tools\nssm\win64\nssm.exe`

---

### ===SESSION D3 START===

```
SESSIE D3 — Bridge hardening: NSSM Windows Service + lokale watchdog.

Werk autonoom. Geen check-ins.

## Context

Bridge draait nu via Task Scheduler (TB-001 uit night-sessie 02) OF handmatig.
Probleem: stopt bij logoff, geen auto-restart bij crash.
Oplossing: NSSM Windows Service (draait zonder login, auto-restart).

## Stap 1: vraag NSSM locatie

Stel Alex ÉÉN vraag:
"Pad naar nssm.exe (bijv. C:\tools\nssm\win64\nssm.exe)"

Wacht op antwoord. Valideer Test-Path.

## Stap 2: locate bridge werkmap

$bridgeDir = "L:\!Nova V2\bridge\nova_host_bridge"
Test-Path $bridgeDir  # moet true zijn na night-sessie 02

# Locate python.exe explicitly (NSSM needs absolute path)
$pythonExe = (Get-Command python).Source
# Of fallback: "C:\Python314\python.exe"

## Stap 3: Task Scheduler NOVA_Bridge uitschakelen

(TB-001 zou conflicteren met NSSM)

Disable-ScheduledTask -TaskName "NOVA_Bridge"

Stop running bridge processes:
Get-Process python -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like "*uvicorn*app.main*8500*" } |
  Stop-Process -Force

## Stap 4: NSSM service installeren

$nssm = "<pad_van_alex>"
$serviceName = "NOVA_Bridge_Service"

# Remove existing als er een oude hangt
& $nssm remove $serviceName confirm 2>$null

# Install nieuwe service
& $nssm install $serviceName $pythonExe
& $nssm set $serviceName AppParameters "-m uvicorn app.main:app --host 0.0.0.0 --port 8500"
& $nssm set $serviceName AppDirectory $bridgeDir
& $nssm set $serviceName DisplayName "NOVA Host Bridge"
& $nssm set $serviceName Description "NOVA v2 local tool bridge op poort 8500"
& $nssm set $serviceName Start SERVICE_AUTO_START

# Logging
& $nssm set $serviceName AppStdout "L:\!Nova V2\logs\bridge_service_stdout.log"
& $nssm set $serviceName AppStderr "L:\!Nova V2\logs\bridge_service_stderr.log"
& $nssm set $serviceName AppRotateFiles 1
& $nssm set $serviceName AppRotateBytes 10485760  # 10MB

# Auto-restart config
& $nssm set $serviceName AppExit Default Restart
& $nssm set $serviceName AppRestartDelay 5000  # 5 sec delay
& $nssm set $serviceName AppThrottle 10000     # 10 sec throttle tussen snelle restarts

## Stap 5: service starten

Start-Service $serviceName
Start-Sleep 5

# Verify
$svc = Get-Service $serviceName
if ($svc.Status -ne "Running") {
    Write-Host "FAIL: service niet running, status=$($svc.Status)"
    # Show recent stderr log
    Get-Content "L:\!Nova V2\logs\bridge_service_stderr.log" -Tail 20
} else {
    # Test endpoint
    try {
        $r = Invoke-WebRequest http://localhost:8500/health -UseBasicParsing -TimeoutSec 5
        Write-Host "OK: bridge service running, health=$($r.StatusCode)"
    } catch {
        Write-Host "WARN: service running maar endpoint niet bereikbaar"
    }
}

## Stap 6: lokale watchdog script

File: L:\!Nova V2\scripts\bridge_watchdog.py

import time
import subprocess
import requests
import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(r"L:\!Nova V2\logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "watchdog.log",
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

BRIDGE_URL = "http://localhost:8500/health"
SERVICE_NAME = "NOVA_Bridge_Service"
CHECK_INTERVAL = 60  # sec
MAX_FAILURES = 3     # restart na 3 achtereenvolgende fails

def check_bridge():
    try:
        r = requests.get(BRIDGE_URL, timeout=5)
        return r.status_code == 200
    except Exception as e:
        logging.warning(f"health check failed: {e}")
        return False

def restart_service():
    logging.warning(f"Restarting {SERVICE_NAME}...")
    try:
        subprocess.run(["sc", "stop", SERVICE_NAME], check=False, timeout=30)
        time.sleep(3)
        subprocess.run(["sc", "start", SERVICE_NAME], check=False, timeout=30)
        time.sleep(5)
        logging.info(f"Service {SERVICE_NAME} restart command issued")
    except Exception as e:
        logging.error(f"restart failed: {e}")

def main():
    failures = 0
    logging.info("Watchdog started")
    
    while True:
        if check_bridge():
            if failures > 0:
                logging.info(f"Bridge recovered after {failures} failures")
            failures = 0
        else:
            failures += 1
            logging.warning(f"Bridge down ({failures}/{MAX_FAILURES})")
            
            if failures >= MAX_FAILURES:
                restart_service()
                failures = 0  # reset na restart poging
                time.sleep(30)  # extra wait na restart
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

## Stap 7: watchdog ook als NSSM service

& $nssm install "NOVA_Bridge_Watchdog" $pythonExe
& $nssm set "NOVA_Bridge_Watchdog" AppParameters "L:\!Nova V2\scripts\bridge_watchdog.py"
& $nssm set "NOVA_Bridge_Watchdog" AppDirectory "L:\!Nova V2\scripts"
& $nssm set "NOVA_Bridge_Watchdog" DisplayName "NOVA Bridge Watchdog"
& $nssm set "NOVA_Bridge_Watchdog" Description "Monitors bridge health, restarts service if 3x fail"
& $nssm set "NOVA_Bridge_Watchdog" Start SERVICE_AUTO_START
& $nssm set "NOVA_Bridge_Watchdog" AppStdout "L:\!Nova V2\logs\watchdog_stdout.log"
& $nssm set "NOVA_Bridge_Watchdog" AppStderr "L:\!Nova V2\logs\watchdog_stderr.log"
& $nssm set "NOVA_Bridge_Watchdog" AppExit Default Restart

Install requests package als nog niet:
pip install requests

Start service:
Start-Service "NOVA_Bridge_Watchdog"

## Stap 8: verificatie

Test failure simulation:
# Stop bridge service handmatig
Stop-Service NOVA_Bridge_Service
# Wacht 3 minuten (3x 60sec check + restart margin)
Start-Sleep 210
# Bridge zou weer up moeten zijn
$r = Invoke-WebRequest http://localhost:8500/health -UseBasicParsing -TimeoutSec 5
if ($r.StatusCode -eq 200) {
    Write-Host "OK: watchdog restarted bridge after manual stop"
} else {
    Write-Host "FAIL: watchdog failed to restart"
}

# Check watchdog log
Get-Content "L:\!Nova V2\logs\watchdog.log" -Tail 10
# Moet "Restarting" entry hebben

## Stap 9: rapport

File: L:\!Nova V2\docs\session_D3_report.md
# Sessie D3 Rapport
- Timestamp
- NSSM location: <pad>
- Task Scheduler NOVA_Bridge: disabled
- Service NOVA_Bridge_Service: installed, AUTO_START
- Service NOVA_Bridge_Watchdog: installed, AUTO_START
- Bridge URL health check: PASS
- Watchdog failure simulation: <resultaat>
- Auto-restart on crash: tested
- Status: SUCCESS / PARTIAL / FAILED
- Next: sessie D4 (external monitoring)

git add scripts/bridge_watchdog.py docs/session_D3_report.md
git commit -m "day session D3: bridge NSSM service + watchdog"
git push origin main

Print "SESSION D3 COMPLETE — bridge hardened, auto-restart active"

REGELS:
- Als NSSM install faalt: check running-as-admin (PowerShell)
- Als pip install requests faalt: probeer pip install --user requests
- Watchdog mag 24/7 draaien, consumpt <50MB RAM
- Service restart kan 10-15 sec duren, niet in paniek raken bij test

Ga.
```

### ===SESSION D3 EINDE===

---

## OUTPUT

- `NOVA_Bridge_Service` Windows Service (NSSM), AUTO_START
- `NOVA_Bridge_Watchdog` Windows Service (NSSM), AUTO_START
- `L:\!Nova V2\scripts\bridge_watchdog.py`
- Logs in `L:\!Nova V2\logs\watchdog.log`
- Task Scheduler NOVA_Bridge disabled (vermijd conflict)

## VERIFIEREN

```powershell
Get-Service NOVA_* | Format-Table Name, Status, StartType
Get-Content "L:\!Nova V2\logs\watchdog.log" -Tail 20
```

Beide services Running, StartType Automatic.

## BELANGRIJK

Bij Windows updates die reboot vereisen: services starten automatisch weer.
Bij PC crash / stroomuitval: services starten op bij boot, zonder dat Alex
moet inloggen. Dit is het grote verschil met Task Scheduler (die vereist login).
