# Prompt 34: End-to-End GIS Pipeline Test

## Wat deze prompt doet

Test planetside alien world generation pipeline: PDOK → QGIS → Blender Baker → 3D Model Jury.

## Voorwaarden

- [ ] Prompt 33 compleet
- [ ] Agents 13, 15, 14, 05, 31, 32, 04 active

## De prompt

```
Voer end-to-end GIS pipeline integration test uit.

DOEL: Test dat PDOK data → bruikbare alien terrain voor game werkt.

TEST CASE: Hoogeveen centrum, 1km² area

STAP 1: PDOK DOWNLOAD
POST http://178.104.207.194:5680/webhook/pdok-download
Body: {
  "bounds": {"min_x": 228000, "min_y": 530000, "max_x": 229000, "max_y": 531000},
  "data_type": "ahn4_dtm",
  "resolution": 0.5
}

Verwacht: tile paths voor DEM data.

STAP 2: QGIS PROCESSOR
POST http://178.104.207.194:5680/webhook/qgis-process
Body: {
  "input_dem": "<van stap 1>",
  "operations": ["contour", "slope", "hillshade"],
  "output_format": "geotiff"
}

Verwacht: processed raster paths.

STAP 3: QGIS ANALYSIS (ADVANCED)
POST http://178.104.207.194:5680/webhook/qgis-analysis
Body: {
  "workflow": "terrain_classification",
  "input": "<van stap 2>"
}

Verwacht: classification raster (flats, slopes, steep).

STAP 4: GRASS GIS VIEWSHED
POST http://178.104.207.194:5680/webhook/grass-analysis
Body: {
  "operation": "viewshed",
  "dem": "<van stap 1>",
  "observer": {"x": 228500, "y": 530500, "height": 10},
  "max_distance": 500
}

Verwacht: visibility raster.

STAP 5: BLENDER BAKER (TERRAIN)
POST http://178.104.207.194:5680/webhook/blender-bake
Body: {
  "dem_file": "<van stap 1>",
  "classification": "<van stap 3>",
  "output_format": "gltf",
  "optimization": "game_ready",
  "target_tri_count": 50000
}

Verwacht: terrain .glb bestand.

STAP 6: 3D MODEL JURY
POST http://178.104.207.194:5680/webhook/3d-review
Body: {
  "model_path": "<van stap 5>",
  "context": "game_terrain",
  "checks": ["manifold", "poly_count", "uv_valid"]
}

Verwacht: verdict accept/revise.

STAP 7: GIS JURY
POST http://178.104.207.194:5680/webhook/gis-review
Body: {
  "artifacts": ["<stap 1 dem>", "<stap 3 classification>"],
  "check_topology": true
}

Verwacht: verdict.

STAP 8: RAPPORT
Schrijf L:\\!Nova V2\\docs\\integration_test_34_report.md vergelijkbaar met test 33:
- Per stap status
- Output bestanden
- Performance (duur per stap)
- Verdict overall

STAP 9: COMMIT
git commit -m "test: integration test 34 GIS pipeline - <status>"

RAPPORT:
- Test 34 resultaat
- Totale duur (grotere tests kunnen 30-60 min duren)
- Volgende: prompt 35
```

## Verwachte output

- Terrain .glb bestand bruikbaar voor Godot 3D mode
- Test rapport
- Bruikbaar voor toekomstige alien planet generation

## Volgende prompt

`05_integration/prompt_35_end_to_end_story_pipeline.md`
