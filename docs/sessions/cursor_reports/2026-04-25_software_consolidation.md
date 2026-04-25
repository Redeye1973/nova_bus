# Software Consolidatie Rapport

- **Datum:** 25 april 2026  
- **Status:** **SUCCESS (documentatie + YAML)** — geen fysieke bestandsverplaatsingen (beleid eerste run)

## Discovery

| Item | Waarde |
|------|--------|
| Drives aanwezig | C:, D:, E:, G:, H:, L: |
| Methode | `scripts/find_software.ps1` — **begrensde wortels** (geen volledige C:\-recursie; eerste poging daarmee geannuleerd na timeout) |
| Output | `docs/software_discovery_full.json` |
| Tools met minstens één hit | 17 (o.a. Aseprite, Blender, Krita, GIMP, Inkscape, DAZ, FreeCAD, Godot, QGIS, GRASS-bundel indicator, SuperCollider, SoX, LDtk, Audacity, Unreal, PyxelEdit, Audiocraft venv-python) |

### Categorisatie (samenvatting)

| Categorie | Betekenis | Richtaantal |
|-----------|-----------|-------------|
| **A** | Al in `L:\ZZZ Software` | 10 |
| **B** | Portable elders → ZZZ mogelijk | **0** |
| **C** | Program Files (niet verplaatsen) | 5 |
| **D** | Steam / Epic-style engine | 2 |
| **E** | Niet geïnstalleerd / browser | 5 + ChipTone |

Details: `docs/software_consolidation_plan.md`

## Verplaatsingen

| Actie | Aantal |
|-------|--------|
| Geslaagde moves | **0** |
| Gefaalde moves | **0** |
| Kopieën naar ZZZ | **0** |
| Origineel verwijderd | **0** |

Log: `docs/software_move_log.md` (NO_OP)

## tool_paths.yaml

- **Versie-metadata:** `version: 1.1`, `last_inventory: 2026-04-25`
- **Uitbreidingen:** `location`, `move_to_zzz`, `reason_no_move`, `install_priority`, expliciete **QGIS** GUI+CLI, **UnrealEditor**-pad, **Audacity**, ontbrekende tools als `not_installed`, **ChipTone** als browser tool, noot over **L:\ZZZ Software\Dazz\** (DIM vs DAZ Studio exe)

## Niet gevonden door script (verwacht)

- **OBS Studio**, **MakeHuman**, **Tiled**, **Poser** — geen hits in gescande paden → `not_install` in YAML

## Volgende stappen

1. Optioneel installers voor OBS / MakeHuman / Tiled volgens prioriteit in YAML.  
2. **Audiocraft:** venv op Python 3.11 rebuilden.  
3. Software test framework (Agent 64) later koppelen aan `tool_paths.yaml` voor padresolutie.  
4. Bij wijziging QGIS-versie: map `C:\Program Files\QGIS *` opnieuw in discovery-plan zetten (nu vast `3.40.13`).

## Git

Aanbevolen commit message:

`software consolidation: discovery JSON, consolidation plan, tool_paths.yaml`

---

*Einde rapport.*
