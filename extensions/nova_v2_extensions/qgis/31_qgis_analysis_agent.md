# 31. QGIS Analysis Agent

## Doel
Interactieve QGIS workflows voor geo-analyse beyond basic data processing. Cartografie, spatial analysis, custom map deliverables.

## Scope
- Thematic map generation
- Spatial analysis (buffers, intersections, statistics)
- Custom cartografie output (legend, scale, north arrow)
- Print layouts (.qpt templates)
- Plugin orchestration (GRASS integratie, QuickOSM, etc)

## Jury (3 leden, medium)

**1. Cartografische Correctheid Validator**
- Tool: Python + QGIS Python API
- Checkt: legenda compleet, schaal correct, north arrow aanwezig
- Verify: CRS informatie zichtbaar, bronvermelding
- Output: cartografie compliance

**2. Spatial Analysis Logic Checker**
- Tool: Python + geopandas + shapely
- Verify: analysis results make sense
- Check: buffer distances reasonable
- Detect: topology issues in results

**3. Output Format Validator**
- Tool: Python + file parsers
- Check: PDF exports quality (resolution, fonts embedded)
- Verify: shapefile/GeoPackage validity
- Compliance met gov/client standaarden

## Judge

Accept → Client-ready deliverable
Revise → Specific cartografie/analysis fixes
Reject → Fundamental approach issue

## Cursor Prompt

```
Bouw NOVA v2 QGIS Analysis Agent:

1. Python service `qgis_analysis/workflow_executor.py`:
   - FastAPI POST /workflow/execute
   - Input: {workflow_name, input_data, parameters}
   - Use qgis_process CLI of PyQGIS
   - Track progress, handle errors
   - Output: analysis results paths

2. Python service `qgis_analysis/thematic_map.py`:
   - FastAPI POST /map/thematic
   - Input: dataset + theme (kadaster, demografie, verkeersdichtheid)
   - Apply pre-configured stijlen (.qml files)
   - Color ramp selection per theme
   - Export PNG + georeferenced TIF

3. Python service `qgis_analysis/spatial_analysis.py`:
   - FastAPI POST /analysis/spatial
   - Operations: buffer, intersect, union, dissolve, distance
   - Combine multiple layers
   - Statistics calculation
   - Output: result layer + summary

4. Python service `qgis_analysis/print_layout_generator.py`:
   - FastAPI POST /layout/generate
   - Use QGIS print layout API (or templates)
   - Add: map, legend, scale, north arrow, title, logo
   - Export: PDF met correcte resolutie (300 DPI)
   - Template-based per client

5. Python service `qgis_analysis/plugin_orchestrator.py`:
   - Integration met QGIS plugins:
     - QuickOSM voor OSM data
     - Serval voor raster editing
     - Semi-Automatic Classification voor satellite
   - Install/update plugins via code
   - Run plugin functions programmatically

6. Python service `qgis_analysis/cartographic_validator.py`:
   - Jury member 1
   - Parse print layout XML
   - Check: legend aanwezig, complete
   - Scale bar correct, north arrow present
   - Attribution visible

7. Python service `qgis_analysis/analysis_validator.py`:
   - Jury member 2
   - Load analysis results
   - Sanity checks (buffer sizes, result counts)
   - Compare tegen input expectations

8. Python service `qgis_analysis/output_validator.py`:
   - Jury member 3
   - PDF validation (PyPDF)
   - Shapefile integrity (fiona)
   - Compliance checking

9. Python service `qgis_analysis/analysis_judge.py`:
   - Aggregate verdicts

10. Template library `qgis_analysis/templates/`:
    - .qpt print templates
    - .qml style definitions
    - Common workflow definitions

Gebruik Python 3.11, PyQGIS (via QGIS install), geopandas,
FastAPI, subprocess voor QGIS CLI invocations.
```

## Common QGIS workflows voor NOVA producten

**Voor FINN (architect/gemeente digital twin):**
- Zoning analysis (what zones exist, overlap met project)
- View analysis (wat zie je vanaf welke plek)
- Sunlight analysis (schaduwen per tijdstip)
- Height regulations compliance

**Voor 45Route:**
- Route optimization tussen stops
- Service area analysis
- Travel time isochrones

**Voor gemeente klanten:**
- Population density maps
- Building age distribution
- Infrastructure overlay

**Voor archeologie/historie:**
- Old map georeferencing
- Comparison met huidige situatie
- Change over time visualization

## Plugin library essentieel

QGIS plugins die vaak nuttig zijn:
- **QuickOSM** - OSM data downloaden
- **GRASS provider** - Advanced geoprocessing
- **Semi-Automatic Classification** - Satellite image analysis
- **Profile Tool** - Elevation profiles (AHN data)
- **Time Manager** - Temporal visualizations
- **PDOK Services** - Direct PDOK integration
- **QGIS2ThreeJS** - 3D web output

Agent kan deze via Python aanroepen na installation.

## Test Scenario's

1. Buffer analysis rond gebouwen → correct geometry
2. Thematic map Hoogeveen bouwjaren → proper classification + colors
3. Print layout A3 → professional output
4. Missing legend in print → revise

## Success Metrics

- Cartografie compliance: > 95%
- Analysis accuracy: > 90% (vs manual validation)
- Output format compliance: 100%
- Plugin integration success: > 85%

## Output

Per workflow:
- Result datasets (GeoJSON, shapefile, raster)
- Maps (PNG, PDF)
- Summary statistics
- Workflow reproducibility (params + QGIS version)

## Integratie

- Werkt met QGIS Processor (15) voor data prep
- Uses GRASS GIS Analysis (32) voor advanced ops
- Validated door GIS Jury (05)
- Feeds Blender Architecture (33) voor 3D visualisation
- Distribution Agent (19) delivers finale maps
