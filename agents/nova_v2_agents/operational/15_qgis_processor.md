# 15. QGIS Processor Agent

## Doel
Data preprocessing tussen PDOK download en Blender baking. QGIS via Python (PyQGIS of qgis_process CLI).

## Functionaliteit

**1. Reprojection**
- RD-New → game engine coordinates (offset naar lokale origin)

**2. Geometry Cleanup**
- Fix invalid geometries
- Remove duplicate features
- Snap vertices

**3. Attribute Enrichment**
- Cross-reference BAG met BGT voor functie
- Merge AHN4 hoogtes naar BAG footprints
- Add calculated fields (area, perimeter)

**4. Simplification**
- Per LOD appropriate simplification
- Preserve topology

**5. Filtering**
- Remove features buiten target postcode
- Filter by relevance (bouwjaar > 1800, etc)

**6. Export**
- GeoJSON met alle enriched attributes
- GeoPackage voor archival

## Cursor Prompt

```
Bouw een NOVA v2 QGIS Processor:

1. Python service `qgis_processor/processor.py`:
   - FastAPI POST /process
   - Input: {input_dir, output_dir, postcode, target_lod}
   - Chain van processing steps

2. Python module `qgis_processor/reprojector.py`:
   - Use pyproj voor CRS transforms
   - RD-New → WGS84 → local origin (postcode center)
   - Output: meters relative to origin

3. Python module `qgis_processor/geometry_cleaner.py`:
   - shapely voor validity
   - Buffer(0) trick voor self-intersections
   - Snap vertices binnen tolerance
   - Remove degenerate geometries

4. Python module `qgis_processor/attribute_enricher.py`:
   - Spatial join BAG ↔ BGT (gebouw functie)
   - AHN4 raster sampling at BAG footprint (hoogte)
   - Calculate: oppervlakte, omtrek, centroid
   - Classify: bouwjaar era (voor 1920, 1920-1940, etc)

5. Python module `qgis_processor/simplifier.py`:
   - Douglas-Peucker per LOD
   - Preserve topology (use topologic simplification)
   - Different thresholds per LOD

6. Python module `qgis_processor/filter.py`:
   - Postcode boundary filter
   - Relevance filter (exclude temporary structures)
   - Attribute-based filters

7. Python module `qgis_processor/exporter.py`:
   - Write GeoJSON met metadata
   - Write GeoPackage als archive
   - Include processing log

8. Alternative: qgis_process CLI wrapper:
   - Soms makkelijker dan PyQGIS
   - `qgis_process run native:snap -- INPUT=...`
   - Subprocess calls met error handling

Gebruik Python 3.11, geopandas, shapely, pyproj, rasterio.
Voor zware operaties: PyQGIS via qgis_process CLI.
FastAPI voor service.
```

## Processing Pipeline

```
Input: raw PDOK downloads
    ↓
Reproject to local coords
    ↓
Clean geometries
    ↓
Cross-reference datasets
    ↓
Enrich with calculated attributes
    ↓
Filter by postcode boundary
    ↓
Generate LOD versions
    ↓
Export ready for Blender
```

## Test Scenario's

1. Standard Hoogeveen processing → clean output naar Blender
2. AHN4 gaten (wolken) → graceful fill of flag areas
3. BAG/BGT inconsistency → logged maar proceed
4. Invalid geometries → fixed automatically

## Success Metrics

- Processing tijd < 30 min voor standaard postcode
- Attribute enrichment coverage > 95%
- Geometry validity 100% post-processing
