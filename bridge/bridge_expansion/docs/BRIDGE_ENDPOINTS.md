# Bridge Endpoints Reference

Complete API reference voor nova_host_bridge na volledige expansion.

**Bridge URL**: `http://alex-main-1:8500` (via Tailscale) of `http://100.64.0.2:8500`

## Global endpoints

### `GET /`
Bridge info + uptime.

### `GET /health`
Health check. Returns 200 als bridge responsive.

### `GET /tools`
List alle beschikbare tools met status.

Response:
```json
{
  "freecad": {"tool": "freecad", "available": true, "version": "1.0.2"},
  "qgis": {"tool": "qgis", "available": true, "version": "3.40.13 LTR"},
  "blender": {"tool": "blender", "available": true, "version": "Blender 4.3.2"},
  "aseprite": {"tool": "aseprite", "available": true, "version": "1.3.7-x64"},
  "pyqt": {"tool": "pyqt", "available": true, "version": "5.15.10"},
  "godot": {"tool": "godot", "available": true, "version": "4.6.2.stable.official"},
  "grass": {"tool": "grass", "available": false},
  "gimp": {"tool": "gimp", "available": true, "version": "GNU Image Manipulation Program 2.10.38"},
  "krita": {"tool": "krita", "available": true, "version": "5.2.6"},
  "inkscape": {"tool": "inkscape", "available": true, "version": "Inkscape 1.3.2"}
}
```

## FreeCAD `/freecad/*`

Voor Agent 21 Parametric, 06 CAD Jury.

- `GET /freecad/status`
- `POST /freecad/parametric` - genereer parametric component
- `POST /freecad/export_step` - export naar STEP
- `POST /freecad/validate` - valideer geometry

## QGIS `/qgis/*`

Voor Agent 15 Processor, 31 Analysis, 05 GIS Jury.

- `GET /qgis/status`
- `POST /qgis/process` - run processing algorithm
- `POST /qgis/export` - raster/vector export
- `POST /qgis/analyze` - spatial analysis

## Blender `/blender/*`

Voor Agent 22 Game Renderer, 14 Baker, 33 Architecture.

- `GET /blender/status`
- `POST /blender/render` - render scene
- `POST /blender/export` - export 3D format (GLB/FBX/OBJ/USD)
- `POST /blender/script` - run Python script

Example render request:
```json
{
  "scene_path": "C:/assets/ship.blend",
  "output_path": "C:/output/ship_render.png",
  "format": "PNG",
  "resolution_x": 1920,
  "resolution_y": 1080,
  "samples": 128,
  "engine": "CYCLES"
}
```

## Aseprite `/aseprite/*`

Voor Agent 23 Processor, 24 Animation Jury.

- `GET /aseprite/status`
- `POST /aseprite/batch_export` - export sprite sheets
- `POST /aseprite/convert` - PNG ↔ ASE
- `POST /aseprite/palette_apply` - palette swap
- `POST /aseprite/animation_export` - animation frames

## PyQt5 `/pyqt/*`

Voor Agent 25 Assembly.

- `GET /pyqt/status`
- `POST /pyqt/sprite_assembly` - combine sprites
- `POST /pyqt/image_compose` - grid/horizontal/vertical layout
- `POST /pyqt/metadata_sheet` - sprite sheet metadata JSON

## Godot `/godot/*`

Voor Agent 26 Import.

- `GET /godot/status`
- `POST /godot/import_test` - validate asset import
- `POST /godot/project_validate` - validate whole project
- `POST /godot/headless_test` - run test scene
- `POST /godot/export_build` - export to binary
- `POST /godot/script_execute` - run GDScript

## GRASS GIS `/grass/*`

Voor Agent 32 Analysis.

- `GET /grass/status`
- `POST /grass/import_raster`
- `POST /grass/terrain_analysis`
- `POST /grass/export_raster`
- `POST /grass/module_run`

## GIMP `/gimp/*`

Voor Agent 35 Raster 2D.

- `GET /gimp/status`
- `POST /gimp/script_fu` - Script-Fu execution
- `POST /gimp/batch_convert`
- `POST /gimp/filter_apply`
- `POST /gimp/composite`

## Krita `/krita/*`

Voor Agent 35 (secondary).

- `GET /krita/status`
- `POST /krita/plugin_execute`
- `POST /krita/batch_export`
- `POST /krita/brush_batch`

## Inkscape `/inkscape/*`

Voor Agent 35 (vector).

- `GET /inkscape/status`
- `POST /inkscape/svg_to_png`
- `POST /inkscape/convert`
- `POST /inkscape/batch_process`
- `POST /inkscape/template_fill`

## Error handling

Alle endpoints gebruiken consistent error codes:

- **200**: Success
- **400**: Bad request (invalid params)
- **404**: Resource niet gevonden (file, project)
- **422**: Pydantic validation failure
- **500**: Internal error (tool crash, unexpected state)
- **503**: Tool niet beschikbaar
- **504**: Timeout

Error body:
```json
{
  "detail": "Human-readable error message"
}
```

## Rate limiting

Niet geïmplementeerd - trust boundary via Tailscale, alleen jouw agents roepen aan.

## Logging

Bridge logt naar `nova_host_bridge.log` op PC. Elke request + subprocess call wordt gelogd.

Log levels:
- INFO: normale operations
- WARNING: degradatie (tool slow, niet optimaal)
- ERROR: operation failed
- CRITICAL: bridge zelf heeft problemen

## Security notes

- Bridge luistert op `0.0.0.0:8500` - accepteert elk connection, maar alleen Tailscale mesh bereikt het
- Geen authentication headers - Tailscale = trusted network
- Subprocess calls met user-provided input: alle paden worden gevalideerd (absolute paths check, geen `..`)
- Timeout bescherming tegen runaway processes

## Deployment

Bridge start op PC met:
```powershell
cd L:\!Nova V2\bridge\nova_host_bridge
python -m uvicorn app.main:app --host 0.0.0.0 --port 8500
```

Of als Windows Service met NSSM (recommended voor 24/7).
