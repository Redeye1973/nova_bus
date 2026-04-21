# 14. Blender Baker Agent

## Doel
Converteert verwerkte GIS data naar game-ready 3D geometry via Blender headless.

## Functionaliteit

**1. Geometry Generation**
- BAG footprints + AHN hoogte → 3D gebouwen
- BGT wegen → road meshes
- Terrein heightmap → terrain mesh

**2. Asset-Kit Application**
- Per gebouw assign gevel + dak asset op basis van attributes
- Straatmeubilair placement
- Bomen uit BGT boom-locaties

**3. LOD Generation**
- High (close-up), Mid (middle distance), Low (far)
- Via Blender Decimate modifier

**4. UV Unwrapping**
- Smart UV project voor gebouwen
- Texture atlas generation

**5. Material Assignment**
- PBR materials per asset category
- Texture tiling configuration

**6. Export**
- GLB formaat (multi-engine compatible)
- FBX optional (voor Unreal preferences)
- Per-LOD exports

## Cursor Prompt

```
Bouw een NOVA v2 Blender Baker:

1. Python script `blender_baker/main.py` (draait IN Blender via bpy):
   - Entry point, loaded met blender --background --python main.py
   - Accept args: --input /path/to/processed.geojson --output /path/to/bake
   - Orchestrates all baking steps

2. Python module `blender_baker/building_generator.py`:
   - Input: BAG polygons + heights
   - Extrude footprints naar 3D via bpy.ops
   - Apply random asset-kit variant based on bouwjaar + size
   - Join per-chunk voor performance

3. Python module `blender_baker/road_generator.py`:
   - BGT road polygons → flat meshes with materials
   - Sidewalks, fietspaden separate materials
   - Road markings as decals

4. Python module `blender_baker/terrain_generator.py`:
   - Load AHN4 heightmap (GeoTIFF)
   - Convert naar plane met displacement
   - Subdivide to match LOD target

5. Python module `blender_baker/asset_library.py`:
   - Load asset-kit .blend file
   - Function: get_facade(bouwjaar, width, height) → mesh reference
   - Function: get_roof(shape, area) → mesh reference  
   - Function: get_street_furniture(type) → mesh reference
   - Cache loaded assets

6. Python module `blender_baker/lod_generator.py`:
   - Input: high detail mesh
   - Apply Decimate modifier with different ratios
   - Export as separate LOD levels

7. Python module `blender_baker/uv_unwrapper.py`:
   - Smart UV project per asset
   - Create texture atlas
   - Optimize UV space usage

8. Python module `blender_baker/exporter.py`:
   - Export to GLB via Blender glTF exporter
   - Preserve metadata in custom properties
   - Multi-file export (per LOD)

9. Wrapper script `blender_baker/run_bake.sh`:
   - bash script die blender --background aanroept
   - Handles timeouts
   - Logs naar structured format

10. FastAPI service `blender_baker/api.py`:
    - POST /bake
    - Spawns subprocess met blender
    - Returns job_id, tracks completion
    - Async via Celery of simpel polling

11. Asset library .blend file met 250+ assets:
    - Gevels per tijdperk (50 varianten)
    - Daken per type (50 varianten)  
    - Street furniture (30 types)
    - Trees/plants (20 varianten)
    - Vehicles (10 statisch geparkeerde)
    - Traffic signs (40 NDW types)

Gebruik: Python 3.11, Blender 4.3+, bpy API, FastAPI voor wrapper.
Headless execution via xvfb indien geen display.
```

## Performance Optimalisaties

- Mesh instancing voor repeated assets (MultiMesh in Godot, Instanced Static Mesh in Unreal)
- Per-chunk processing (100m x 100m) om memory beheren
- Bake lighting niet in deze fase (engine handelt real-time)

## Test Scenario's

1. Hoogeveen centrum bake: ~5000 gebouwen → should complete binnen 30 min
2. Klein dorpje: < 500 gebouwen → 5 min
3. Amsterdam (Jordaan): 15000 gebouwen → 2 uur
4. Error recovery: corrupted input → graceful fail

## Success Metrics

- Bake completion rate: > 95%
- Poly budget adherence: 100% (automatic LOD fallback als over budget)
- Asset-kit variety (niet overal zelfde gevel): measured via histogram
- Output quality (GIS jury approval): > 90%
