# 02. FreeCAD Parametric Models

## Doel
Parametric base models waaruit veel ship varianten kunnen worden gegenereerd. Eén parametric fighter = 20 verschillende enemy ships door parameters aan te passen.

## Waarom FreeCAD voor shmup

**Parametric = schaalbaarheid:**
- Wing sweep angle als parameter → nieuwe variant
- Engine count (1/2/4) als boolean → nieuwe variant
- Wing span als dimensie → verschillende size klassen

**Precisie:**
- Exact measurements voor consistent size
- Geen modeling drift tussen ships
- Booleans voor weapon mounts snel toevoegen

**Export naar Blender:**
- STEP files preserven exact geometry
- Materials apart in Blender (zoals het hoort)

**Versioning:**
- FreeCAD files zijn text-based XML
- Git friendly
- Diffs te reviewen

## Folder structuur

```
shmup_assets/
├── freecad/
│   ├── base_models/
│   │   ├── fighter_base.FCStd
│   │   ├── bomber_base.FCStd
│   │   ├── heavy_base.FCStd
│   │   ├── boss_frame.FCStd
│   │   └── projectiles.FCStd
│   ├── components/
│   │   ├── wings/
│   │   │   ├── wing_straight.FCStd
│   │   │   ├── wing_swept.FCStd
│   │   │   └── wing_delta.FCStd
│   │   ├── engines/
│   │   │   ├── engine_small.FCStd
│   │   │   ├── engine_large.FCStd
│   │   │   └── engine_thruster.FCStd
│   │   ├── weapons/
│   │   │   ├── gun_mount.FCStd
│   │   │   ├── missile_rack.FCStd
│   │   │   └── turret_base.FCStd
│   │   └── cockpits/
│   │       ├── cockpit_standard.FCStd
│   │       └── cockpit_bubble.FCStd
│   └── variants/
│       ├── corporate_fighter_mk1.FCStd
│       ├── corporate_fighter_mk2.FCStd
│       └── ...
```

## Parametric fighter base

Een fighter base model heeft parameters:

| Parameter | Range | Effect |
|-----------|-------|--------|
| body_length | 40-120 | Ship size |
| body_width | 20-80 | Ship breedte |
| wing_sweep | 0-60 deg | Agressieve vs vredige look |
| wing_span | 30-100 | Wingspan |
| engine_count | 1-4 | Single tot quad engines |
| cockpit_style | 0-3 | Verschillende cockpit types |
| weapon_mounts | 0-6 | Aantal wapen pods |
| tail_type | 0-3 | None, single, double, delta |

Met deze 8 parameters alleen al 10000+ variaties mogelijk. Praktisch kies je er 20-50 die werken.

## Workflow: nieuwe ship variant

**Optie A: GUI workflow (voor iteratie)**
1. Open fighter_base.FCStd in FreeCAD
2. Spreadsheet panel → pas parameters aan
3. Recompute (F5)
4. Check silhouette
5. Save as variant (corporate_fighter_heavy.FCStd)
6. Export STEP naar Blender import folder

**Optie B: Script workflow (voor batch)**
1. Python script met parameter matrix
2. Loopt through combinaties
3. Per iteratie: open base, set params, save variant, export STEP
4. Genereert 20 varianten in 5 minuten

Optie B is wat NOVA v2 pipeline gebruikt voor bulk generatie.

## Cursor prompt: Parametric fighter generator

```
Bouw een FreeCAD parametric ship generator voor Black Ledger:

1. FreeCAD macro file `freecad/macros/fighter_generator.FCMacro`:
   - Opens fighter_base.FCStd
   - Defines parameter matrix (lists van values per param)
   - Loops through combinations
   - Per combination: 
     - Set spreadsheet values
     - Recompute document
     - Save as new .FCStd file
     - Export STEP file naar ./exports/step/
   - Logs progress

2. Base model builder `freecad/build_base.py`:
   - Use FreeCAD Python console API
   - Creates parametric fighter from scratch
   - Adds Spreadsheet with parameters
   - Uses Part.makeBox, Part.makeRuledSurface voor basic shapes
   - Hooks parameters to geometry via expressions
   - Output: fighter_base.FCStd

3. Component library builder `freecad/build_components.py`:
   - Generates reusable components:
     - Wing shapes (5 types)
     - Engine shapes (4 types)  
     - Weapon mounts (3 types)
     - Cockpits (3 types)
   - Each as separate FCStd file
   - Standardized mounting points (coordinates)

4. Variant assembler `freecad/assemble_variant.py`:
   - Input: parameter dict
   - Loads base model
   - Adds components per params (wing type, engine count)
   - Applies boolean operations (subtract engine holes, etc)
   - Output: assembled variant

5. STEP exporter `freecad/export_step.py`:
   - Batch export all variants to STEP
   - Consistent scale (1 unit = 1 meter, but ships are small)
   - Preserve parameter metadata in filename

6. Variant matrix config `freecad/variants.yaml`:
   - List of all desired variants
   - Parameters per variant
   - Metadata (faction, role, tier)

7. CLI wrapper `freecad/cli.py`:
   - `python cli.py generate --faction corporate --count 10`
   - `python cli.py list-variants`
   - `python cli.py export --variant <name>`

Gebruik: FreeCAD 1.0+ Python API, PyYAML, click voor CLI.
Run via FreeCAD's Python: `freecad.cmd --python script.py`
Of via standalone FreeCAD Python: `python -c "import FreeCAD; ..."`
```

## Component library standaarden

Alle component mounting points moeten consistent zijn. Gebruik deze conventies:

**Wing mounting:**
- Origin: wing root attachment point
- Z-axis: along wing span
- Orientation: as if mounted on right side
- Left wing = mirrored

**Engine mounting:**
- Origin: front face center
- Z-axis: pointing forward (towards engine exhaust)
- Consistent size class naming: small/medium/large/xlarge

**Weapon mounting:**
- Origin: barrel mount point
- Z-axis: pointing forward (firing direction)
- Includes recoil socket for animation

Met deze standaarden kun je components uitwisselen tussen base models zonder handmatig aanpassen.

## Validation scripts

```python
# freecad/validate_model.py
# Checks dat model voldoet aan constraints:
# - Bounding box binnen size category
# - Silhouette herkenbaar (render test)
# - Mounting points aanwezig
# - Naming conventions gevolgd
```

## Output van deze fase

Per ship variant:
- `.FCStd` file (parametric model, editable)
- `.step` file (static geometry voor Blender)
- Metadata JSON (params, category, faction)

Alle gestandaardiseerd voor volgende pipeline stap.

## Tips en trucs

**Tip 1: Start minimaal**
Begin met 3 base models (fighter/bomber/heavy). Maak 5 varianten elk. Test volledige pipeline. Dan expand.

**Tip 2: Save snapshot bij grote changes**
Parametric models kunnen breken bij extreme param values. Maak git commits op werkende punten.

**Tip 3: Boolean operations zijn duur**
Veel booleans maken model traag. Gebruik waar nodig maar niet overmatig.

**Tip 4: Gebruik Draft module voor 2D profielen**
Wing outlines teken je in 2D, extrude dan. Veel makkelijker dan 3D sketchen.

**Tip 5: Symmetrie waar mogelijk**
Modelleer halve ship, mirror naar andere kant. Zorgt voor perfect symmetric result.

## Integration met NOVA v2

FreeCAD stap heeft zijn eigen jury:
- CAD Jury (agent 06) valideert manifold, scale, mounting points
- Parametric robustness check (breekt bij edge cases?)
- Bij fail: terug naar aanpassen voor Blender stap

## Volgende stap

Met STEP files klaar: verder naar 03_blender_rendering.md voor het omzetten naar mooi gerenderde sprites.
