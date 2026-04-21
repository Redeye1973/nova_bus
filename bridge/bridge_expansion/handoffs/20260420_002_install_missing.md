# 20260420_002 - Install Missing Tools

**Van**: claude.ai  
**Naar**: Cursor  
**Prioriteit**: normal  
**Expected duration**: 1-2 uur (afhankelijk van hoeveel ontbreekt)

## Context

Na handoff 001 weten we welke tools ontbreken op PC.
Deze handoff installeert alle ontbrekende tools die nodig zijn voor Fase 1-4.

## Doel

Alle NOVA V2 required software operationeel + in PATH op PC alex-main-1.

## Opdracht

Lees `shared_state/software_inventory.csv` voor huidige staat.

Installeer ontbrekende tools in deze prioriteit:

### Prioriteit 1 (Fase 1 blockers)

1. **Blender 4.x** als ontbreekt:
   - Download van blender.org (stable release)
   - Install met default options
   - Voeg toe aan PATH: `C:\Program Files\Blender Foundation\Blender 4.x\`
   - Test: `blender --version` moet werken vanuit any dir
   
2. **PyQt5** als ontbreekt:
   ```powershell
   pip install PyQt5
   ```
   - Als Python geen PATH heeft: waarschuwing geven, installeer python.org versie
   - Test: `python -c "from PyQt5 import QtCore"` moet geen error geven

3. **Aseprite** check:
   - Aseprite is paid tool, niet autonoom installeren
   - Als niet aanwezig: documenteer in response, user moet zelf installeren
   - Als wel aanwezig maar niet in PATH: voeg installation folder toe
   - Test: `aseprite --version`

### Prioriteit 2 (Fase 1 validator)

4. **Godot 4.6.2+** als ontbreekt:
   - Download Godot 4.6.2 standard (niet .NET) van godotengine.org
   - Extract naar `C:\Godot\`
   - Voeg `C:\Godot\` aan PATH
   - Hernoem binary naar `godot.exe` (van Godot_v4.6.2-stable_win64.exe)
   - Test: `godot --version`

### Prioriteit 3 (Fase 4 nice-to-have)

5. **GRASS GIS 8.x** als ontbreekt:
   - Download WinGRASS installer
   - Default install
   - PATH: `C:\Program Files\GRASS GIS 8.x\`
   - Test: `grass --version`

6. **GIMP 2.10+** als ontbreekt:
   - Download gimp.org
   - Default install
   - PATH automatisch via installer
   - Test: `gimp --version`

7. **Inkscape 1.3+** als ontbreekt:
   - Download inkscape.org
   - MSI installer met PATH optie aan
   - Test: `inkscape --version`

8. **Krita** al aanwezig volgens memory:
   - Verify path
   - Als niet in PATH: `C:\Program Files\Krita (x64)\bin\` toevoegen
   - Test: `krita --version`

### Prioriteit 4 (Python ecosystem)

9. **Python 3.11+** check:
   - Als <3.11: upgrade niet autonoom, waarschuwing
   - Als PyQt5 werkte in handoff 1: Python is OK

10. **Python packages** voor bridge:
    ```powershell
    pip install fastapi uvicorn pydantic pyyaml requests Pillow
    ```

## PATH management

Na elke install: `RefreshEnv` of restart bridge. Script voor refresh:

```powershell
# Refresh PATH zonder reboot
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

## Bridge restart

Na alle installs:
1. Stop bridge: `.\scripts\stop_watcher.ps1` (of specifieke bridge stop)
2. Bridge executable restarten (vermoedelijk `python nova_host_bridge.py` of service)
3. Verify: `curl http://alex-main-1:8500/tools` moet nieuwe tools tonen

## Constraints

- **Aseprite niet autonoom installeren** (paid)
- **Geen Python major version upgrades** autonoom (breakt veel)
- **Backup PATH voor wijziging**: `$env:Path > L:\!Nova V2\bridge\backups\path_backup_[date].txt`
- **Per install: log succes/fail** in installation log
- Geen installs als inventory laat zien dat tool al aanwezig is

## Success criteria

- Alle Prioriteit 1 tools installed (Blender, PyQt5)
- Godot available OF gedocumenteerd als later
- Inventory re-run bevestigt installaties
- Bridge herstart zonder errors
- `/tools` endpoint toont alle nieuwe tools als `available=true` (voor de geïnstalleerde)

## Rapporteer terug

Schrijf `handoff/from_cursor/20260420_002_response.md`:

1. Per tool: installed/skipped/failed + reden
2. Handmatige acties nodig voor gebruiker (Aseprite, etc)
3. Nieuwe PATH entries
4. Bridge status na herstart
5. Go/no-go handoff 003

Update `current_baseline.md` met nieuwe software state.

## Notities

- Installers kunnen user interaction vragen - gebruik `/S` silent flags waar mogelijk
- Als download faalt: retry 1x met exponential backoff, dan markeer failed
- Respect disk space: check `$freeGB = (Get-PSDrive C).Free / 1GB` voor grote installs
- Blender = 300MB, Godot = 90MB, GRASS = 400MB, GIMP = 250MB, Inkscape = 150MB
- Totaal download: ~1.5GB als alles moet
