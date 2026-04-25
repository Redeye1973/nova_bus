# Software Consolidatie Plan

**Datum:** 25 april 2026  
**Bron:** `docs/software_discovery_full.json` (begrensde scan) + handmatige verificatie kernpaden  
**Beleid:** Geen fysieke verplaatsingen in deze run — alleen plan + YAML. Verplaatsen alleen na expliciete copy/test/approve (zie `software_move_log.md`).

---

## Categorie A — Al in `L:\ZZZ Software` (geen verplaatsing nodig)

| Tool | Primair pad | Opmerking |
|------|-------------|-----------|
| SuperCollider | `L:\ZZZ Software\Super Collider\` | sclang + scsynth |
| SoX | `L:\ZZZ Software\SoX\sox-14.4.2\sox.exe` | |
| GIMP 3 | `L:\ZZZ Software\GIMP 3\bin\` | console + GUI |
| Inkscape | `L:\ZZZ Software\InkScape\bin\inkscape.exe` | |
| LDtk | `L:\ZZZ Software\ldtk\LDtk.exe` | |
| FreeCAD | `L:\ZZZ Software\FreeCad\bin\` | portable-achtige layout op L: |
| Godot | `L:\ZZZ Software\Godot\` | console + export binary |
| PyxelEdit | `L:\ZZZ Software\PyxelEdit\` | GUI-only; niet voor pipeline |
| Audiocraft | `L:\ZZZ Software\Audiocraft\venv\` | partial / Python issues |
| DAZ support | `L:\ZZZ Software\Dazz\` | **DAZ Install Manager / DLLs**, géén `DAZStudio.exe` — runtime blijft Program Files |

---

## Categorie B — Elders portable, veilig naar ZZZ te verplaatsen

**Geen kandidaten gevonden** in deze inventarisatie:

- D:, E:, G:, H: tonen geen bruikbare top-level softwaretrees (leeg of niet gebruikt voor tools).
- Geen dubbele portable installs in Downloads/AppData die al onder ZZZ staan.
- Eventuele toekomstige ZIP-extracts: eerst hier documenteren vóór move.

---

## Categorie C — `C:\Program Files` (registry / installer; **niet verplaatsen**)

| Tool | Pad |
|------|-----|
| Blender | `C:\Program Files\Blender Foundation\Blender 4.3\blender.exe` |
| Krita | `C:\Program Files\Krita (x64)\bin\krita.exe` |
| DAZ Studio | `C:\Program Files\DAZ 3D\DAZStudio4\DAZStudio.exe` |
| QGIS | `C:\Program Files\QGIS 3.40.13\` — GUI: `bin\qgis-ltr-bin.exe`, CLI: `apps\qgis-ltr\bin\qgis_process.exe` |
| Audacity | `C:\Program Files\Audacity\Audacity.exe` |

---

## Categorie D — Externe launcher / engine-root (**niet verplaatsen**)

| Tool | Pad |
|------|-----|
| Aseprite | `L:\SteamLibrary\steamapps\common\Aseprite\Aseprite.exe` (Steam) |
| Unreal Engine | `L:\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe` (Epic-style tree op L:, launcher beheert updates) |

---

## Categorie E — Niet gevonden / niet van toepassing

| Item | Status | Prioriteit |
|------|--------|------------|
| OBS Studio | Niet geïnstalleerd (geen `obs64.exe` in standaard paden) | medium |
| MakeHuman | Niet geïnstalleerd | medium |
| Tiled | Niet geïnstalleerd | laag |
| Poser | Niet geïnstalleerd | laag (alternatief: DAZ) |
| GRASS GIS standalone | Niet op PATH; **GRASS-modules wel gebundeld in QGIS-install** | laag (gebruik QGIS-bundel) |
| ChipTone | Browser/web tool — geen exe | n.v.t. |

---

## Audiocraft

- Venv aanwezig onder ZZZ; bekende **Python 3.13 / torch**-problemen — rebuild op 3.11 aanbevolen (zie bestaande `tool_paths` note).

---

## Samenvatting tellingen

| Categorie | Aantal tools/entries |
|-----------|---------------------|
| A (ZZZ) | 10 |
| B (verplaatsbaar) | 0 |
| C (Program Files) | 5 |
| D (Steam/Epic-style) | 2 |
| E (ontbreekt) | 5 + ChipTone (browser) |
