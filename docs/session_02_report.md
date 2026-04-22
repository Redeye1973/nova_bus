# Sessie 02 Rapport

- **Timestamp:** 2026-04-22
- **Bridge location:** `L:\!Nova V2\nova_host_bridge` (FastAPI `main:app`, poort **8500**).
- **Pad-compat:** junction `L:\!Nova V2\bridge\nova_host_bridge` → echte map (lokaal; in `.gitignore` om dubbele git-index te vermijden).
- **Bridge mode:** **full** (v0.2.0 — adapters FreeCAD/QGIS/…; geen recovery-minimal build nodig).
- **Python 3.14:** pydantic/fastapi stack geüpgraded zodat `import main` slaagt (zie eerdere `docs/BRIDGE_FIX_REPORT.md`).
- **Runtime check (deze run):** `GET /health` → **200**, `GET /tools` → **200**; JSON bevat tool-keys: `freecad`, `qgis`, `aseprite`, `krita`, `blender`, `godot`.
- **TB-001 Task Scheduler (`NOVA_Bridge`):** **niet geregistreerd** — eerdere `Register-ScheduledTask` gaf **Toegang geweigerd** zonder elevated shell. Startscript staat wel klaar: `scripts/start_bridge.ps1` (werkt met `nova_host_bridge`, niet met fictief `bridge\nova_host_bridge`-alleen-pad).
- **Status:** **PARTIAL** — bridge online; automatische start bij logon nog **handmatig als Administrator** uit `02_BRIDGE_FIX.md` stappen Fase 5.
- **Next session:** **03** — V1 orchestrator brief (`briefings/master_build_brief.md` + delegatie volgens mega-plan).

## Admin-stappen voor TB-001 (eenmalig)

In **PowerShell als Administrator**:

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"L:\!Nova V2\scripts\start_bridge.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit 0
Register-ScheduledTask -TaskName "NOVA_Bridge" -Action $action -Trigger $trigger -Settings $settings -Force
```

Daarna testen: `Start-ScheduledTask NOVA_Bridge` en opnieuw `curl.exe http://localhost:8500/health`.
