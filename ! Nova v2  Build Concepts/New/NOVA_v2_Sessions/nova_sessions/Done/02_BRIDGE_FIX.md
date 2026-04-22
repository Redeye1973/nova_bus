# SESSIE 02 — Bridge Fix + Task Scheduler

**Doel:** Bridge op localhost:8500 online krijgen zodat tool-aanroepen werken.
**Tijd:** 45-90 min
**Afhankelijkheden:** Sessie 01 compleet

---

## Cursor Composer sessie

Plak tussen markers in Cursor Composer (Ctrl+I):

### ===SESSION 02 START===

```
SESSIE 02 van 7 — Bridge fix + TB-001 Task Scheduler entry.

Werk autonoom. Geen check-ins tenzij LEVEL 3/4.

## Context
- Bridge op localhost:8500 is offline
- Pad L:\!Nova V2\bridge\nova_host_bridge bestaat volgens eerdere memory
  maar eerder check suggereert dat 't er niet is
- Python 3.14 + uvicorn beschikbaar
- Bestaande logs in L:\!Nova V2\nova_host_bridge.log* suggereren dat bridge
  ooit gedraaid heeft

## Fase 1: locatie vinden (max 10 min)

Get-ChildItem "L:\!Nova V2" -Directory | Select Name
Get-ChildItem -Path "L:\!Nova V2" -Recurse -Depth 3 -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match "bridge|host" } | Select FullName
Get-ChildItem -Path "L:\!Nova V2" -Recurse -Filter "main.py" -ErrorAction SilentlyContinue |
  Select FullName

Log alles in logs\bridge_fix.log.

## Fase 2: diagnose indien gevonden (max 15 min)

Als bridge-map gevonden:
- Check app\main.py of main.py structuur
- Check requirements.txt
- Probeer: python -c "from app.main import app; print('OK')"
- Poort 8500 vrij? (Get-NetTCPConnection -LocalPort 8500)
- Laatste 50 regels van nova_host_bridge.log lezen voor error hints

## Fase 3: startpoging (max 15 min, max 2 pogingen)

cd <bridge_dir>
pip install -r requirements.txt 2>&1 | Tee-Object -FilePath logs\bridge_pip.log

Start-Process -FilePath "python" `
  -ArgumentList "-m","uvicorn","<entry>","--host","0.0.0.0","--port","8500" `
  -WorkingDirectory <bridge_dir> `
  -RedirectStandardOutput "L:\!Nova V2\logs\bridge_stdout.log" `
  -RedirectStandardError "L:\!Nova V2\logs\bridge_stderr.log" `
  -WindowStyle Hidden -PassThru

Start-Sleep 5
Test: Invoke-WebRequest http://localhost:8500/tools -UseBasicParsing -TimeoutSec 5

Als UP: Fase 5 overslaan naar 6.
Als DOWN na 2 pogingen: Fase 4.

## Fase 4: recovery bridge from scratch (laatste redmiddel)

Maak minimale FastAPI bridge:

mkdir "L:\!Nova V2\bridge\nova_host_bridge"
mkdir "L:\!Nova V2\bridge\nova_host_bridge\app"

Schrijf L:\!Nova V2\bridge\nova_host_bridge\app\__init__.py (leeg).

Schrijf L:\!Nova V2\bridge\nova_host_bridge\app\main.py:

from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(title="NOVA Host Bridge", version="0.1.0-recovery")

TOOL_PATHS = {
    "freecad":  [r"C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe",
                 r"C:\Program Files\FreeCAD 1.0.2\bin\FreeCAD.exe"],
    "qgis":     [r"C:\Program Files\QGIS 3.40.13\bin\qgis-bin.exe",
                 r"C:\Program Files\QGIS 3.40\bin\qgis-bin.exe"],
    "blender":  [r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
                 r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"],
    "aseprite": [r"C:\Program Files\Aseprite\Aseprite.exe",
                 r"C:\Users\awsme\AppData\Local\Aseprite\Aseprite.exe"],
    "godot":    [r"C:\Program Files\Godot\godot.exe",
                 r"C:\Users\awsme\AppData\Local\Programs\Godot\godot.exe"],
    "krita":    [r"C:\Program Files\Krita (x64)\bin\krita.exe"]
}

def find_tool(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

@app.get("/")
def root():
    return {"service": "nova_host_bridge", "mode": "recovery", "version": "0.1.0"}

@app.get("/health")
def health():
    return {"status": "ok", "mode": "recovery"}

@app.get("/tools")
def list_tools():
    tools = []
    for name, paths in TOOL_PATHS.items():
        path = find_tool(paths)
        tools.append({
            "name": name,
            "path": path,
            "status": "available" if path else "not_installed"
        })
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "tools": tools,
        "note": "Recovery mode. Adapters moeten via bridge_expansion 003-005 toegevoegd."
    }

Schrijf requirements.txt:
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0

Install + start:
cd "L:\!Nova V2\bridge\nova_host_bridge"
pip install -r requirements.txt
Start-Process python -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8500" `
  -WorkingDirectory (pwd) `
  -RedirectStandardOutput "L:\!Nova V2\logs\bridge_stdout.log" `
  -RedirectStandardError "L:\!Nova V2\logs\bridge_stderr.log" `
  -WindowStyle Hidden

Sleep 5. Test /tools endpoint.

## Fase 5: TB-001 Task Scheduler

Maak L:\!Nova V2\scripts\start_bridge.ps1:

$ErrorActionPreference = "Continue"
Set-Location "L:\!Nova V2\bridge\nova_host_bridge"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8500 *>> "L:\!Nova V2\logs\bridge.log"

Register task:

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File L:\!Nova V2\scripts\start_bridge.ps1"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit 0
Register-ScheduledTask -TaskName "NOVA_Bridge" -Action $action -Trigger $trigger `
  -Settings $settings -Force

Test task:
Start-ScheduledTask -TaskName "NOVA_Bridge"
Sleep 5
Invoke-WebRequest http://localhost:8500/tools -UseBasicParsing

## Fase 6: rapport + commit

File L:\!Nova V2\docs\session_02_report.md:
# Sessie 02 Rapport
- Timestamp: <iso>
- Bridge location: <pad of "created from scratch">
- Bridge mode: full / recovery
- Task Scheduler: NOVA_Bridge registered
- /tools endpoint: response
- Status: SUCCESS / PARTIAL / FAILED
- Tools detected: <lijst>
- Next session: 03 (V1 orchestrator brief)

git add bridge/ scripts/start_bridge.ps1 docs/session_02_report.md
git commit -m "session 02: bridge online + TB-001 task scheduler"
git push origin main

## Klaar

Print: "SESSION 02 COMPLETE — next: sessie 03 V1 orchestrator brief"

Ga.
```

### ===SESSION 02 EINDE===

---

## OUTPUT

- Bridge draait op localhost:8500
- Task Scheduler entry "NOVA_Bridge" actief (start bij login)
- `docs/session_02_report.md`
- Git commit "session 02: bridge online + TB-001 task scheduler"

## VERIFIEREN

```powershell
(Invoke-WebRequest http://localhost:8500/tools -UseBasicParsing).Content
Get-ScheduledTask -TaskName "NOVA_Bridge"
Get-Content "L:\!Nova V2\docs\session_02_report.md"
```

Bridge mode "recovery" is OK voor nu — adapters komen in latere sessie (bridge expansion 003-005).
