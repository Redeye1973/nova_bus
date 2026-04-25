# Sessie D3 Rapport — Bridge NSSM Service + Watchdog

- **Datum:** 2026-04-25
- **Sessie:** Day Build D3
- **Status:** **SUCCESS**

## Tooling

- `nssm.exe` 2.24 op `L:\tools\nssm\nssm.exe` (verplaatst van C: naar L: ivm schijfruimte op C:).
- Python 3.14 op `C:\Python314\python.exe`, `requests 2.33.1`, `fastapi`/`uvicorn` aanwezig in user site-packages van `awsme`.

## Services

| Service | Status | StartType | Application |
|---------|--------|-----------|-------------|
| `NOVA_Bridge_Service` | Running | Automatic | `python.exe -m uvicorn main:app --host 0.0.0.0 --port 8500` |
| `NOVA_Bridge_Watchdog` | Running | Automatic | `python.exe L:\tools\nova\bridge_watchdog.py` |

NSSM auto-restart config:
- `AppExit Default Restart` (proces crashed → herstart automatisch).
- `AppRestartDelay 5000` (5 sec).
- `AppThrottle 10000` (voorkomt restart-loops).
- `AppEnvironmentExtra` zet `PYTHONPATH=C:\Users\awsme\AppData\Roaming\Python\Python314\site-packages` zodat LocalSystem service de user site-packages kan vinden.

Logs:
- `L:\!Nova V2\logs\bridge_service_stdout.log` + `bridge_service_stderr.log` (auto-rotate 10 MB)
- `L:\!Nova V2\logs\watchdog_stdout.log` + `watchdog_stderr.log`
- `L:\!Nova V2\logs\watchdog.log` (Python logging output van watchdog zelf)

Task Scheduler `NOVA_Bridge`: niet aanwezig op systeem, geen conflict.

## Watchdog

- Bron: `L:\!Nova V2\scripts\bridge_watchdog.py`
- Production copy: `L:\tools\nova\bridge_watchdog.py` (kopie zonder spaties; NSSM kan paden met spaties in `AppParameters` niet correct quoten).
- Check interval: 60s, max consecutive failures: 3.
- Bij 3 fails → `sc stop` + `sc start NOVA_Bridge_Service`, daarna 30s grace period.

## Failure simulation (live test)

```
=== Failure simulation start 2026-04-25T02:21:02 ===
Stopping NOVA_Bridge_Service ...
Bridge stopped at 2026-04-25T02:21:03
RESTORED after 192s, http=200
```

Watchdog log:
```
02:19:50 Watchdog started (interval=60s, max_fail=3)
02:21:58 health check failed (Bridge down 1/3)
02:23:02 health check failed (Bridge down 2/3)
02:24:06 health check failed (Bridge down 3/3)
02:24:06 Restarting NOVA_Bridge_Service ...
```

Total time from kill to fully restored: **192 seconden** (3 × 60s health check + ~12s restart). Komt overeen met design (3 × CHECK_INTERVAL + restart marge).

## Iteraties tot werkende setup (debug log)

| Stap | Probleem | Fix |
|------|----------|-----|
| 1 | UAC popup uit Cursor terminal werkte niet betrouwbaar | Setup scripts naar `L:\!Nova V2\scripts\` geschreven, gebruiker draait via rechts-klik → Run as admin |
| 2 | Service crashte: `ModuleNotFoundError: No module named 'requests'` (LocalSystem zag user site-packages niet) | `nssm set AppEnvironmentExtra PYTHONPATH=C:\Users\awsme\AppData\Roaming\Python\Python314\site-packages` |
| 3 | Watchdog crashte met `can't open file 'L:\\!Nova'` (NSSM stript quotes uit AppParameters) | Watchdog gekopieerd naar `L:\tools\nova\bridge_watchdog.py` (geen spaties) |
| 4 | Watchdog had nog geen PYTHONPATH (eerdere fix-script bailde half-way) | PYTHONPATH ook op watchdog gezet |
| 5 | Failure simulation → bridge in 192s terug | PASS |

## Setup scripts (idempotent, herbruikbaar)

| Script | Doel |
|--------|------|
| `L:\!Nova V2\scripts\setup_bridge_services.ps1` | Volledige setup vanaf scratch (inclusief PYTHONPATH + watchdog op spaceless path) |
| `L:\!Nova V2\scripts\start_bridge_services.ps1` | Start beide services + truncate stderr logs |
| `L:\!Nova V2\scripts\simulate_bridge_failure.ps1` | Stop bridge en wacht max 5 min op auto-recovery |
| `L:\!Nova V2\scripts\bridge_watchdog.py` | Master copy van watchdog (gekopieerd naar `L:\tools\nova\`) |

Alle scripts vereisen `#requires -RunAsAdministrator`.

## Belangrijk

- Bij Windows reboot starten beide services automatisch (`Start SERVICE_AUTO_START`).
- Geen login vereist — services draaien als `LocalSystem`.
- Bij stroomuitval / PC crash: bridge komt vanzelf weer up zonder dat Alex hoeft in te loggen.

## Volgende sessie

**D4** — UptimeRobot externe monitoring + Uptime Kuma self-hosted (60-90 min, handwerk: UptimeRobot account aanmaken).
