# 05. GIS Jury Agent

## Doel
Valideert geografische data voor NORA, FINN en andere geo-producten. Kwaliteitscontrole op PDOK/NDW/KNMI data pipeline output.

## Scope
- PDOK BGT, BAG, AHN4 downloads
- NDW verkeersborden, stoplichten
- Gebakken city packages
- OSM aanvullende data
- GeoJSON exports uit QGIS pipeline

## Jury Leden

**1. Projection Consistency Validator**
- Tool: Python + pyproj + GDAL
- Checkt: RD-New (EPSG:28992) correct, conversie naar game coords klopt
- Detecteert: mixed coordinate systems, offset errors

**2. Data Completeness Detector**
- Tool: Python + geopandas
- Checkt: geen gaten in raster data, vector feature counts plausible
- Voor stad: expected building count vs actual

**3. Topology Validator**
- Tool: PostGIS of shapely
- Checkt: geen overlappende polygonen (tenzij intentioneel), line continuity, valid geometries
- Detecteert: self-intersections, floating points

**4. Attribute Integrity Checker**
- Tool: Python + JSON schema
- Checkt: alle features hebben verwachte velden, types correct, waardes in range
- Bouwjaren realistisch, hoogtes plausible

**5. Scale Appropriateness**
- Tool: Python analysis
- Checkt: resolutie past bij gebruik (game: lage detail ok, FINN: high detail vereist)
- Simplification level appropriate

**6. Source Provenance Tracker**
- Tool: Python + metadata
- Checkt: bron-dataset versies gedocumenteerd, download timestamps, bronverwijzing compleet
- Belangrijk voor klanten die geldigheid moeten bewijzen

**7. Cross-Reference Validator**
- Tool: Python compare
- Checkt: BGT gebouwen matchen BAG counts, NDW borden op geldige wegen
- Detecteert: inconsistencies tussen datasets

## Judge

**GIS Judge**
- Publication-ready: alle green, metadata compleet, bruikbaar voor FINN verkoop
- Game-ready: lower bar, geschikt voor NORA zonder publieke verantwoording
- Development: experimentele data voor intern gebruik
- Reject: fundamentele problemen

## N8n Workflow

```
Trigger: na QGIS pipeline run (city bake)
    ↓
Load gebakken dataset
    ↓
Parallel jury:
    ├─ Projection check
    ├─ Completeness
    ├─ Topology
    ├─ Attributes
    ├─ Scale
    ├─ Provenance
    └─ Cross-reference
    ↓
Merge
    ↓
GIS Judge
    ↓
Verdict + publicatie kanaal
```

## Cursor Prompt

```
Bouw een NOVA v2 GIS Jury voor validatie van gebakken city packages:

1. Python service `gis_jury/projection_validator.py`:
   - Input: GeoJSON of GPKG file
   - Detect CRS via fiona/geopandas
   - Verify consistent projection across features
   - Check valid conversion RD-New ↔ WGS84
   - Output: {crs_consistent, correct_epsg, issues}

2. Python service `gis_jury/completeness_checker.py`:
   - Input: city package path + expected_postcode
   - Check: BAG feature count vs expected for postcode
   - Check: BGT coverage percentage
   - Check: AHN raster geen NoData holes
   - Output: {complete: bool, coverage_pct, missing_areas: []}

3. Python service `gis_jury/topology_validator.py`:
   - Use shapely voor geometry validation
   - Check: valid geometries, no self-intersections
   - Check: adjacent polygons correctly share boundaries
   - Output: {valid_count, invalid: [{feature_id, issue}]}

4. Python service `gis_jury/attribute_checker.py`:
   - Load JSON schema per dataset type
   - Validate features tegen schema
   - Check value ranges (bouwjaar 1000-2026, hoogte 0-400m, etc)
   - Output: {valid, validation_errors: []}

5. Python service `gis_jury/scale_validator.py`:
   - Input: dataset + intended_use (game|viewer|planning)
   - Check geometry simplification level
   - Check raster resolution
   - Compare tegen target specifications
   - Output: {appropriate: bool, current_level, recommended}

6. Python service `gis_jury/provenance_tracker.py`:
   - Check metadata completeness
   - PDOK version, download date, processing steps
   - Verify attribution info aanwezig
   - Output: {provenance_complete, missing_info: []}

7. Python service `gis_jury/cross_reference.py`:
   - Load multiple datasets (BGT + BAG + NDW)
   - Cross-check: buildings in BGT match BAG
   - NDW bord locations op wegen in NWB?
   - Output: {consistent, discrepancies: [...]}

8. Python service `gis_jury/gis_judge.py`:
   - Input: all jury outputs + intended_use
   - Use-case specific thresholds
   - Output verdict + routing recommendation

9. N8n workflow `gis_jury_workflow.json`:
   - Trigger na bake completion
   - Parallel jury validation
   - Judge
   - Route naar:
     - city_packages/production/ (FINN sale quality)
     - city_packages/game_ready/ (NORA use)
     - city_packages/development/ (experimental)
     - city_packages/rejected/ (fix needed)

10. Integration met monitor-agent: notify bij quality regression

Gebruik Python 3.11, geopandas, shapely, fiona, pyproj, 
rasterio voor AHN. FastAPI voor services.
```

## Integratie met Bake Pipeline

```
QGIS pipeline processing
    ↓
Blender headless 3D generation
    ↓
GIS Jury validation ← (hier)
    ↓
Distribution (different buckets per verdict)
    ↓
Notify monitor-agent
```

## Test Scenario's

1. Clean Hoogeveen bake → all green → publication-ready
2. Bake met ontbrekende AHN data (wolken in luchtfoto) → completeness flagged → development
3. Mixed projections in export → projection fail → revise
4. BAG features missing attributes → attribute warning → game-ready (acceptabel)
5. Topology errors (zelfkruisende polygonen) → reject + fix needed

## Success Metrics

- Detectie invalid geometries: 99%+
- Cross-reference accuracy: > 90% detecteert echte issues
- False positive rate: < 10%
- Quality regression alerts within 24 uur na introductie
