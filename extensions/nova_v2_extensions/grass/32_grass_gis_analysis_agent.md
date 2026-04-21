# 32. GRASS GIS Analysis Agent

## Doel
Advanced geo-processing via GRASS GIS. Complement aan QGIS voor computationally intensive analyses en raster work.

## Scope
- Raster analysis (AHN4 DEM work)
- Hydrological modeling (water flow, drainage)
- Viewshed analysis (wat zie je vanaf positie X)
- Terrain analysis (slope, aspect, curvature)
- Cost surfaces en least-cost paths
- Satellite/drone image processing

## Jury (3 leden, medium)

**1. Computational Validity Checker**
- Tool: Python + GRASS
- Verify: resolution matching tussen rasters
- Check: CRS consistent
- Detect: NoData propagation issues
- Output: data compatibility report

**2. Analysis Output Reasonableness**
- Tool: Python + statistics
- Apply sanity checks:
  - Slopes 0-90°
  - Flow accumulation non-negative
  - Viewshed coverage reasonable
- Detect outliers of obvious errors

**3. Performance Profiler**
- Tool: Python timing + GRASS stats
- Track: analysis duration
- Compare tegen benchmarks
- Flag excessive memory use
- Suggest optimizations

## Judge

Accept → Analysis complete
Revise → Fix parameters of data issues
Reject → Re-think approach

## Waarom GRASS naast QGIS

QGIS + Python doet veel maar voor specifieke use cases:
- GRASS is sneller voor raster math
- GRASS heeft bewezen algorithms voor terrain work
- r.watershed is superior voor hydrology
- r.viewshed is efficiënter
- Kan headless draaien zonder QGIS overhead

Voor FINN en architecture projects: GRASS maakt verschil.

## Cursor Prompt

```
Bouw NOVA v2 GRASS GIS Analysis Agent:

1. Python service `grass_gis/grass_runner.py`:
   - FastAPI POST /analysis/run
   - Input: {analysis_type, input_rasters, parameters}
   - Setup GRASS GIS session (grass --exec)
   - Use grass-session Python library
   - Output: result rasters + metadata

2. Python service `grass_gis/terrain_analysis.py`:
   - Wrapper voor terrain modules:
     - r.slope.aspect
     - r.curvature  
     - r.geomorphon
     - r.reliefshade
   - Input: DEM (AHN4)
   - Output: slope/aspect/curvature rasters

3. Python service `grass_gis/hydrology.py`:
   - Wrapper voor hydrological modules:
     - r.watershed (flow accumulation, drainage)
     - r.flow (flow direction)
     - r.basin.fill
     - r.stream.extract
   - Useful voor gemeente wateroverlast analysis

4. Python service `grass_gis/viewshed.py`:
   - r.viewshed wrapper
   - Input: DEM + observer points
   - Output: visibility raster
   - Use cases: real estate (uitzicht), planning (zichtbaarheid)

5. Python service `grass_gis/cost_surface.py`:
   - r.cost + r.path wrappers
   - Least-cost path analysis
   - Input: cost raster + start/end points
   - Output: optimal path

6. Python service `grass_gis/raster_math.py`:
   - r.mapcalc wrapper
   - Generic raster algebra
   - Useful voor custom analyses

7. Python service `grass_gis/image_processing.py`:
   - i.* modules voor satellite/aerial
   - PCA, classification, segmentation
   - For aerial photography analysis

8. Python service `grass_gis/computational_validator.py`:
   - Jury member 1
   - Check raster compatibility
   - Verify GRASS location setup
   - Detect data issues

9. Python service `grass_gis/reasonableness_checker.py`:
   - Jury member 2
   - Statistical sanity checks
   - Outlier detection

10. Python service `grass_gis/performance_profiler.py`:
    - Jury member 3
    - Time tracking
    - Memory usage
    - Suggest optimizations

11. Python service `grass_gis/grass_judge.py`:
    - Aggregate verdict

Gebruik Python 3.11, grass-session, GRASS GIS 8.3+,
FastAPI, GDAL voor raster IO.
```

## Common analyses voor NOVA

**Voor FINN digital twin:**
```python
# Viewshed vanaf belangrijke punten
viewshed_town_hall = run_viewshed(
    dem=ahn4_raster,
    observer=(x, y, height=15),  # town hall roof
    max_distance=2000  # 2km radius
)

# Slope voor wheelchair accessibility
slope_raster = run_slope_analysis(dem=ahn4_raster)
accessible_routes = slope_raster < 5  # <5° is wheelchair OK
```

**Voor architectural archviz:**
```python
# Sun + shadow analyse
shadow_map = run_shadow_analysis(
    dem=terrain_plus_buildings,
    sun_position=(azimuth=180, altitude=45)
)

# Best viewpoint voor presentatie
best_views = find_optimal_observer_points(
    target_buildings=new_development,
    candidate_points=public_spaces
)
```

**Voor gemeente planning:**
```python
# Water overlast risico
flow_accumulation = run_watershed(dem=ahn4_raster)
risk_zones = flow_accumulation > threshold

# Bereikbaarheid vanuit zorginstellingen
cost_surface = combine_roads_and_terrain(roads, dem)
accessibility = least_cost_from_points(cost_surface, hospitals)
```

## GRASS Location Management

GRASS vereist "location" (projection + extent) en "mapset" (work area).

Agent handles dit automatisch:
```python
# Auto-setup location voor NL
grass_location = setup_grass_location(
    epsg=28992,  # RD-New
    bounds=netherlands_extent,
    resolution=0.5  # AHN4 resolution
)

# Mapset per project
mapset = create_mapset(location=grass_location, project="hoogeveen_finn")
```

## Integration met AHN4

AHN4 (Actueel Hoogtebestand Nederland) is kern data:
- 0.5m resolution DSM (Digital Surface Model)
- 0.5m resolution DTM (Digital Terrain Model)
- Landelijk beschikbaar
- 5-jaarlijkse updates

GRASS is ideaal voor AHN4 processing want:
- Tile-based, efficiënt
- Statistics over grote gebieden
- Processing chains zonder elke keer loaden

## Test Scenario's

1. Slope analysis Hoogeveen → reasonable slope map
2. Viewshed vanaf watertoren → coverage pattern logical
3. Water accumulation → pools in natuurlijk lage punten
4. CRS mismatch → detect + auto-reproject

## Success Metrics

- Analysis completion rate: > 95%
- Computational efficiency: competitive met QGIS native
- Result accuracy: validated tegen benchmarks
- Memory efficiency: handle 10GB+ DEMs

## Output

Per analysis:
- Result rasters (GeoTIFF format)
- Summary statistics
- Performance metrics
- Visualization previews

## Integratie

- Complement aan QGIS Analysis (31)
- Input van QGIS Processor (15)
- Output valideerbaar door GIS Jury (05)
- Feed Blender Architecture (33) voor 3D met analysis overlays
- Useful voor Buro Hollema-achtige klanten (toekomstig)
