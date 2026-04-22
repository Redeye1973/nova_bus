# NOVA v2 — Bridge fix rapport

**Datum:** 2026-04-22  
**Doel:** Bridge weer bereikbaar op `http://localhost:8500` (o.a. `/tools`), pad-correctie, daarna night-run voorbereiding.

## Wat was er mis

1. **Verwacht pad** `L:\!Nova V2\bridge\nova_host_bridge` bestond niet — de echte service staat in **`L:\!Nova V2\nova_host_bridge`** (FastAPI `main:app`, geen `app.main`).
2. **Python 3.14:** eerste import faalde met `ImportError: cannot import name 'BaseModel' from 'pydantic'` (mismatch user-site vs base install).
3. **Proces:** geen listener op poort **8500** → `curl` gaf “geen verbinding met externe server”.

## Diagnose (Fase 2)

- `python -c "import main"` in `nova_host_bridge` → na **`pip install pydantic`** (upgrade naar 2.13.3 + pydantic-core) → **OK**.
- Poort **8500** was vrij (`netstat` leeg).
- **`/tools`:** zonder `BRIDGE_TOKEN` is er geen Bearer-verplichting → **200** na start.

## Oplossing (Fase 3 — succes)

- Uvicorn gestart (achtergrond):

  `WorkingDirectory: L:\!Nova V2\nova_host_bridge`  
  `python -m uvicorn main:app --host 0.0.0.0 --port 8500`

- Verificatie:
  - `GET http://localhost:8500/health` → **200**
  - `GET http://localhost:8500/tools` → **200** (auth uit)

## Pad-compatibiliteit

- **Junction** aangemaakt: `L:\!Nova V2\bridge\nova_host_bridge` → `L:\!Nova V2\nova_host_bridge`  
  (documentatie en scripts die `bridge\nova_host_bridge` noemen kloppen nu op schijf.)

## TB-001 Task Scheduler (Fase 5)

- Script toegevoegd: **`L:\!Nova V2\scripts\start_bridge.ps1`** (start + `pip` quiet check + log append).
- **`Register-ScheduledTask -TaskName NOVA_Bridge`:** **mislukt — “Toegang geweigerd”** (geen elevated shell).  
  **Actie Alex:** Taak handmatig aanmaken als Administrator, of één keer in verhoogde PowerShell:

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"L:\!Nova V2\scripts\start_bridge.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "NOVA_Bridge" -Action $action -Trigger $trigger -Settings $settings -Force
```

## Night-run (Fase 6)

- **`mega_plan/NOVA_V2_NIGHT_RUN_PROMPT.md`** gekopieerd vanuit `!CCChat Starter` voor vast pad.
- **`status/baseline.json`:** `bridge_online` → **true**.
- Volledige Fase A–G in deze sessie niet opnieuw doorlopen; night-run kan verder zodra Composer de night-prompt plakt (bridge is nu geen blocker meer).

## Bridge-modus

- **Full** — bestaande `nova_host_bridge` met adapters (FreeCAD, QGIS, …), geen recovery-minimal uit Fase 4.

## Logs

- **`L:\!Nova V2\logs\bridge_fix.log`** — fase-1 inventaris + acties.
- **`L:\!Nova V2\logs\bridge_stdout.log`** / **`bridge_stderr.log`** — uvicorn output huidige proces.

## Bekende restpunten

1. Scheduled task **NOVA_Bridge** nog registreren als admin.
2. Na reboot: opnieuw starten of taak laten lopen; controleer `Get-NetTCPConnection -LocalPort 8500`.
3. Optioneel: `BRIDGE_TOKEN` in omgeving zetten — dan `/tools` alleen met `Authorization: Bearer …`.

## Drie vervolgstappen voor Alex

1. **Als admin:** Task **NOVA_Bridge** registreren (zie hierboven) en een reboot-test doen.
2. **Night-run:** plak opnieuw de night-run prompt in Composer; **O.11** bridge-offline is nu **niet** meer van toepassing.
3. **Commit/push:** volgende sessie `git pull` op andere machines zodat `scripts/start_bridge.ps1` en junction mee komen.
