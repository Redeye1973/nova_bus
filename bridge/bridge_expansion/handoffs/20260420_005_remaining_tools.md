# 20260420_005 - Bridge Adapters: GRASS + GIMP + Krita + Inkscape

**Van**: claude.ai  
**Naar**: Cursor  
**Prioriteit**: normal (blocker voor Fase 4 Agent 32 en 35)  
**Expected duration**: 2-3 uur

## Context

Bridge heeft 6 adapters: FreeCAD, QGIS, Blender, Aseprite, PyQt, Godot.
Laatste uitbreiding: GRASS GIS + 2D raster/vector tools.

## Doel

4 extra adapters toevoegen voor Fase 4 agents.

## Opdracht

### GRASS GIS adapter (/grass/*)

Voor Agent 32 GRASS Analysis.

Endpoints:
- `GET /grass/status`
- `POST /grass/import_raster` - import GeoTIFF naar GRASS location
- `POST /grass/terrain_analysis` - slope, aspect, flow accumulation
- `POST /grass/export_raster` - export analysis results
- `POST /grass/module_run` - run arbitraire GRASS module

GRASS vereist "location" en "mapset" setup. Adapter creëert default location per project, werkt daarin.

### GIMP adapter (/gimp/*)

Voor Agent 35 Raster 2D (primary voor photo-style work).

Endpoints:
- `GET /gimp/status`
- `POST /gimp/script_fu` - run Script-Fu of Python-Fu
- `POST /gimp/batch_convert` - batch format conversion
- `POST /gimp/filter_apply` - apply filter (blur, sharpen, color adjust)
- `POST /gimp/composite` - multi-layer composite

GIMP console flags: `gimp -i -b "(batch-script ...)" -b "(gimp-quit 0)"`.

### Krita adapter (/krita/*)

Voor Agent 35 (secondary, complement voor digital painting).

Endpoints:
- `GET /krita/status`
- `POST /krita/plugin_execute` - run Krita plugin
- `POST /krita/batch_export` - PSD/KRA → PNG batch
- `POST /krita/brush_batch` - stroke scripts (procedural painting)

Krita: `krita --batch --script <script.py>` voor automation.

### Inkscape adapter (/inkscape/*)

Voor Agent 35 (vector work).

Endpoints:
- `GET /inkscape/status`
- `POST /inkscape/svg_to_png` - SVG render naar PNG op resolutie
- `POST /inkscape/convert` - SVG ↔ PDF, EPS, DXF
- `POST /inkscape/batch_process` - batch operaties via CLI actions
- `POST /inkscape/template_fill` - SVG template + data → gerenderde PNG

Inkscape CLI: `inkscape --actions="select-all;object-align:center;export-type:png;export-do"` voor batch.

### Adapter templates

Alle 4 adapters volgen pattern van eerder gebouwde adapters:
- Pydantic models voor input
- Async subprocess calls
- Timeout per endpoint
- Logging
- Status endpoint eerst implementeren

Zie `adapters/<tool>_adapter_template.py` in expansion pakket.

### Main app integration

```python
from app.adapters import (
    freecad_adapter,
    qgis_adapter,  
    blender_adapter,
    aseprite_adapter,
    pyqt_adapter,
    godot_adapter,
    grass_adapter,      # NIEUW
    gimp_adapter,       # NIEUW
    krita_adapter,      # NIEUW
    inkscape_adapter,   # NIEUW
)

for adapter in [freecad_adapter, qgis_adapter, blender_adapter, aseprite_adapter,
                pyqt_adapter, godot_adapter, grass_adapter, gimp_adapter,
                krita_adapter, inkscape_adapter]:
    app.include_router(adapter.router)
```

### /tools endpoint final

```python
@app.get("/tools")
def list_tools():
    return {
        "freecad": freecad_adapter.status(),
        "qgis": qgis_adapter.status(),
        "blender": blender_adapter.status(),
        "aseprite": aseprite_adapter.status(),
        "pyqt": pyqt_adapter.status(),
        "godot": godot_adapter.status(),
        "grass": grass_adapter.status(),
        "gimp": gimp_adapter.status(),
        "krita": krita_adapter.status(),
        "inkscape": inkscape_adapter.status(),
    }
```

### Tests

Elke adapter krijgt test file. Minimum:
- Status test
- 1 happy path per endpoint
- Error handling (missing file, invalid params)

Test fixtures voor sample assets in `tests/fixtures/`:
- `sample.png` voor GIMP/Krita/Inkscape
- `sample.svg` voor Inkscape
- `sample.tif` voor GRASS
- `sample.psd` voor Krita

## Constraints

- **Fallback mode** voor tools die niet geïnstalleerd zijn (status returns available=false, operations return 503)
- **Geen system-wide config changes** door adapters
- **Tmpdir per request** - geen state tussen requests
- **Output cleanup** - adapter maakt outputs in user-specified path of temp, cleanup na response

## Success criteria

- 10 adapters in totaal operationeel
- `/tools` endpoint compleet
- Alle tests slagen (of fallback correct)
- Git commit "bridge: grass + gimp + krita + inkscape adapters"
- Bridge startup tijd < 3s ondanks alle adapters
- Documented in `docs/BRIDGE_ENDPOINTS.md`

## Rapporteer terug

Schrijf `handoff/from_cursor/20260420_005_response.md`:

1. Alle 10 adapters status
2. /tools endpoint output (JSON)
3. Per tool: test resultaten + version
4. Fallback tools (niet geïnstalleerd)
5. Performance impact bridge startup
6. Complete endpoint lijst voor documentatie
7. Conclusie: bridge expansion COMPLETE

Update shared state:
- `current_baseline.md` - bridge final state
- `decisions.md` - adapter patterns gebruikt
- Schrijf `docs/BRIDGE_ENDPOINTS.md` met complete API reference

## Notities

- GRASS heeft steile learning curve - als je vastloopt, fallback adapter en documenteer als TODO
- GIMP Script-Fu is scheme dialect - voor Python dev lastig maar beter gedocumenteerd dan Python-Fu
- Krita plugin system werkt alleen met Python3 - check Krita versie
- Inkscape 1.3+ heeft CLI completely veranderd vs 1.0 - check installed versie

## Volgende stap

Na handoff 005: bridge is complete voor NOVA V2 Pipeline Build. Agent 32 en 35 kunnen volle implementatie krijgen.

Vervolg werk: batch agent deployment voor Fase 2, 3, 4 (deze vereisen geen bridge uitbreiding meer).

Black Ledger Full Build kan gebruik maken van complete bridge.
