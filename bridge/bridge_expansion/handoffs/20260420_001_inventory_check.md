# 20260420_001 - Bridge Software Inventory Check

**Van**: claude.ai  
**Naar**: Cursor  
**Prioriteit**: high (blocker voor volgende bridge expansion stappen)  
**Expected duration**: 30 min

## Context

Bridge draait met FreeCAD + QGIS. Voor volgende batches (3 en 4) zijn meer tools nodig.
Voordat we adapters bouwen, willen we weten wat al geïnstalleerd is op PC `alex-main-1`.

Deze handoff scant alleen, installeert niks.

## Doel

Complete software inventory van PC genereren voor NOVA bridge planning.

## Opdracht

1. **Run inventory script** op PC via bridge of direct PowerShell:
   
   Gebruik `scripts/inventory_scan.ps1` uit deze expansion package.
   
   Het script checkt deze tools:
   - FreeCAD (baseline - moet aanwezig)
   - QGIS (baseline - moet aanwezig)
   - Blender (Fase 1, 4)
   - Aseprite (Fase 1)
   - PyQt5 Python package (Fase 1)
   - Godot (Fase 1)
   - GRASS GIS (Fase 4)
   - GIMP (Fase 4)
   - Krita (Fase 4)
   - Inkscape (Fase 4)
   - Ollama (LLM inference)
   - Python (3.9+)
   - Node.js (MCP)
   - Git

2. **Output format**: CSV + markdown report naar:
   - `L:\!Nova V2\bridge\nova_bridge\handoff\shared_state\software_inventory.csv`
   - `L:\!Nova V2\bridge\nova_bridge\handoff\shared_state\software_inventory.md`

3. **Voor elke tool vermelden**:
   - Installed: ja/nee
   - Path: waar executable staat
   - Version: output van --version
   - PATH registered: bereikbaar vanuit willekeurige cwd ja/nee

4. **Update** `shared_state/current_baseline.md`:
   - Voeg sectie "## PC Software" toe
   - Lijst met installed/missing tools
   - Verwijzing naar volledige inventory CSV

## Constraints

- Geen installaties in deze stap (alleen scan)
- Geen secrets naar CSV (geen API keys, paths naar secrets)
- Script mag maximaal 2 minuten duren

## Success criteria

- `software_inventory.csv` bestaat met ≥14 tool entries
- `software_inventory.md` heeft leesbaar overzicht
- `current_baseline.md` bijgewerkt
- Git commit met message "bridge expansion: software inventory scan"

## Rapporteer terug

Schrijf `handoff/from_cursor/20260420_001_response.md` met:

1. Samenvatting inventory (X installed, Y missing)
2. Aanbeveling welke tools het eerst te installeren
3. Eventuele issues tijdens scan
4. Verwijzing naar CSV + markdown locatie
5. Go/no-go voor handoff 002 (install missing)

## Notities voor Cursor

Script `inventory_scan.ps1` zit in expansion pakket onder `scripts/`.
Als tool check commando faalt: markeer als "not installed" - niet crashen.
PATH registration checken via: `Get-Command <tool> -ErrorAction SilentlyContinue`
