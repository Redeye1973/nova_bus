# NOVA v2 — Software Inventory

> Gegenereerd: 2026-04-25 | Discovery scan van L:\ZZZ Software\ + externe locaties

---

## L:\ZZZ Software\ Tools

### SuperCollider
- **Locatie:** `L:\ZZZ Software\Super Collider\`
- **Executable:** `scsynth.exe`, `sclang.exe`, `scide.exe`
- **Versie:** 3.14.1
- **In NOVA:** Nieuw (audio stack)
- **Bridge adapter:** Ontbreekt (nog te bouwen)
- **Agent(s):** Geen (toekomstig: agent 54+)
- **Status:** ACTIEF

### SoX
- **Locatie:** `L:\ZZZ Software\SoX\sox-14.4.2\`
- **Executable:** `sox.exe`
- **Versie:** 14.4.2
- **In NOVA:** Nieuw (audio stack)
- **Bridge adapter:** Ontbreekt (nog te bouwen)
- **Agent(s):** Geen (toekomstig)
- **Status:** ACTIEF

### GIMP 3
- **Locatie:** `L:\ZZZ Software\GIMP 3\`
- **Executable:** `bin\gimp-3.2.exe`, `bin\gimp-console-3.2.exe`
- **Versie:** 3.2.4
- **In NOVA:** Nee (nieuw gevonden)
- **Bridge adapter:** Ontbreekt → **BOUWEN (Agent 51)**
- **CLI support:** Ja (Script-Fu + Python-Fu via gimp-console)
- **Agent(s):** Agent 51 GIMP Processor (nieuw)
- **Status:** NIEUW — KANDIDAAT VOOR INTEGRATIE

### Inkscape
- **Locatie:** `L:\ZZZ Software\InkScape\`
- **Executable:** `bin\inkscape.exe`
- **Versie:** 1.4.2
- **In NOVA:** Nee (nieuw gevonden)
- **Bridge adapter:** Ontbreekt → **BOUWEN**
- **CLI support:** Ja (uitstekend: SVG→PNG, batch export, PDF)
- **Agent(s):** Toekomstig: vector/SVG processing
- **Status:** NIEUW — KANDIDAAT VOOR INTEGRATIE

### LDtk (Level Design Toolkit)
- **Locatie:** `L:\ZZZ Software\ldtk\`
- **Executable:** `LDtk.exe`
- **Versie:** Onbekend (Electron app)
- **In NOVA:** Nee
- **Bridge adapter:** Ontbreekt
- **CLI support:** Beperkt (Electron, geen standaard CLI)
- **Agent(s):** Toekomstig: Level Director (Agent 52)
- **Status:** NIEUW GEVONDEN — DEELS GESCHIKT (JSON output leesbaar)

### PyxelEdit
- **Locatie:** `L:\ZZZ Software\PyxelEdit\`
- **Executable:** `PyxelEdit.exe`
- **Versie:** Onbekend
- **In NOVA:** Nee
- **Bridge adapter:** N.v.t.
- **CLI support:** **NEE** (Adobe AIR, GUI-only)
- **Agent(s):** Geen — niet geschikt voor autonome pipeline
- **Status:** AFGEWEZEN (geen CLI/API)

### FreeCAD
- **Locatie:** `L:\ZZZ Software\FreeCad\`
- **Executable:** `bin\FreeCAD.exe`
- **In NOVA:** Ja (Agent 21 FreeCAD Parametric)
- **Bridge adapter:** `nova_host_bridge/adapters/freecad.py`
- **Status:** ACTIEF

### Godot
- **Locatie:** `L:\ZZZ Software\Godot\`
- **Executable:** `Godot_v4.6.2-stable_win64_console.exe`
- **In NOVA:** Ja (Agent 26 Godot Import)
- **Bridge adapter:** `nova_host_bridge/adapters/godot.py`
- **Status:** ACTIEF

### DAZ Studio (Dazz)
- **Locatie:** `L:\ZZZ Software\Dazz\` (shortcuts/manifests)
- **In NOVA:** Ja (Bridge adapter daz.py)
- **Bridge adapter:** `nova_host_bridge/adapters/daz.py`
- **Status:** ACTIEF

### Audiocraft
- **Locatie:** `L:\ZZZ Software\Audiocraft\`
- **Type:** Python venv
- **Versie:** 1.4.0a2
- **Status:** PARTIAL (import fails, PyTorch version conflicts)

---

## Externe Tools (niet in ZZZ Software)

### Aseprite
- **Locatie:** `L:\SteamLibrary\steamapps\common\Aseprite\Aseprite.exe`
- **In NOVA:** Ja (Agent 23)
- **Bridge adapter:** `nova_host_bridge/adapters/aseprite.py`
- **Status:** ACTIEF

### Blender
- **Locatie:** `C:\Program Files\Blender Foundation\Blender 4.3\blender.exe`
- **In NOVA:** Ja (Agent 14, 22, 33)
- **Bridge adapter:** `nova_host_bridge/adapters/blender.py`
- **Status:** ACTIEF

### Krita
- **Locatie:** `C:\Program Files\Krita (x64)\bin\krita.exe`
- **In NOVA:** Ja (Bridge adapter krita.py)
- **Bridge adapter:** `nova_host_bridge/adapters/krita.py`
- **Status:** ACTIEF (CLI fallback)

### QGIS
- **Locatie:** Auto-discover
- **In NOVA:** Ja (Agent 15, 31)
- **Bridge adapter:** `nova_host_bridge/adapters/qgis.py`
- **Status:** ACTIEF

### Unreal Engine
- **Locatie:** `L:\UE_5.7\`
- **In NOVA:** Stub (Agent 34)
- **Status:** GEPLAND

---

## Samenvatting

| Tool | CLI | In NOVA | Bridge | Status |
|------|-----|---------|--------|--------|
| SuperCollider | Ja | Nieuw | Ontbreekt | ACTIEF |
| SoX | Ja | Nieuw | Ontbreekt | ACTIEF |
| GIMP 3 | Ja | Nee | **Bouwen** | NIEUW |
| Inkscape | Ja | Nee | **Bouwen** | NIEUW |
| LDtk | Beperkt | Nee | — | NIEUW |
| PyxelEdit | Nee | Nee | N.v.t. | AFGEWEZEN |
| FreeCAD | Ja | Ja | Bestaat | ACTIEF |
| Godot | Ja | Ja | Bestaat | ACTIEF |
| Aseprite | Ja | Ja | Bestaat | ACTIEF |
| Blender | Ja | Ja | Bestaat | ACTIEF |
| Krita | Beperkt | Ja | Bestaat | ACTIEF |
| QGIS | Ja | Ja | Bestaat | ACTIEF |
| DAZ | DazScript | Ja | Bestaat | ACTIEF |
| Audiocraft | Python | Partial | N.v.t. | PARTIAL |
| Unreal | Ja | Stub | N.v.t. | GEPLAND |
