# NOVA Bridge Expansion - Stappenplan

Uitbreiding van `nova_host_bridge` met alle benodigde tools voor NOVA V2 agents (Fase 1-4 + Black Ledger).

## Huidige stand (baseline)

Bridge draait op PC `alex-main-1:8500` met:
- FreeCAD 1.0.2 ✓
- QGIS 3.40.13 LTR ✓

Hetzner bereikt bridge via Tailscale in ~120ms.

## Wat dit pakket bevat

- **5 handoffs** voor Cursor (stappenplan sequentieel)
- **Adapter templates** voor 9 tools
- **Inventory script** om installs te checken
- **Tests** per adapter
- **Docs** met config, troubleshooting

## Stappenplan overzicht

| Stap | Handoff | Tools | Prereq |
|------|---------|-------|--------|
| 1 | `20260420_001_inventory_check.md` | Scan PC voor wat aanwezig is | Niks |
| 2 | `20260420_002_install_missing.md` | Install ontbrekende tools | Stap 1 klaar |
| 3 | `20260420_003_blender_adapter.md` | Blender + PyQt5 + Aseprite in bridge | Stap 2 klaar |
| 4 | `20260420_004_godot_adapter.md` | Godot in bridge | Stap 3 klaar |
| 5 | `20260420_005_remaining_tools.md` | GRASS, GIMP, Krita, Inkscape | Stap 4 klaar |

Elke handoff is een Cursor-uitvoerbare opdracht volgens bridge protocol.

## Installatie in bridge directory

```powershell
# Uitpakken
Expand-Archive -Path "$HOME\Downloads\bridge_expansion.zip" -DestinationPath "L:\!Nova V2\bridge\nova_bridge\expansion\" -Force

# Handoffs naar to_cursor kopiëren
Copy-Item "L:\!Nova V2\bridge\nova_bridge\expansion\bridge_expansion\handoffs\*" "L:\!Nova V2\bridge\nova_bridge\handoff\to_cursor\"
```

Cursor detecteert nieuwe opdrachten automatisch (als watcher draait) en werkt ze sequentieel af.

## Tijd schatting

Per stap: 1-3 uur Cursor werk. Totaal ~10-15 uur voor volledige bridge expansion.

Dat kan parallel aan batch 2 agent deployment lopen - Cursor wisselt tussen sessies.

## Volgorde rationale

1. **Inventory eerst**: weten wat aanwezig is voor we adapters bouwen
2. **Missing installs**: alles klaarzetten in één keer, minimaliseert reboot/install stappen
3. **Batch 3 tools**: Blender + Aseprite + PyQt5 nodig voor sprite pipeline (volgende batch)
4. **Godot**: validatie voor imports, kan later
5. **Rest**: nice-to-have, geen blocker voor core pipeline

## Niet in scope

- Cloud API's (Meshy, ElevenLabs) - geen bridge nodig, direct vanuit container
- Ollama - draait al, direct access via 11434
- Docker runtime - al geconfigureerd
- N8n - draait in container op Hetzner

## Start

Zorg dat bridge watcher draait:
```powershell
cd "L:\!Nova V2\bridge\nova_bridge"
.\scripts\handoff_status.ps1
```

Als running: kopieer handoffs naar to_cursor/, Cursor pakt ze op.
Als niet running: `.\scripts\start_watcher.ps1` eerst.
