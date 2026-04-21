# 33. Blender Architecture Walkthrough Agent

## Doel
Architecture visualisation workflows voor walkthroughs, VR-prep en client deliverables. Apart van game rendering - focus op fotorealisme en real-world scale.

## Scope
- BIM/CAD import (Datasmith, IFC, FBX)
- Realistic material application
- Architectural lighting (HDRI, sun studies)
- Camera paths voor flyovers
- VR-ready scene preparation
- Integration met PDOK context
- Export naar Unreal (voor VR)

## Jury (5 leden, zwaar - architectuur kwaliteit kritiek)

**1. Scale Accuracy Validator**
- Tool: Python + Blender API
- Check: afmetingen matchen blueprint
- Verify: wall heights, door sizes, room proportions
- Input: BIM metadata of architect spec

**2. Material Realism Reviewer**
- Tool: Ollama Qwen VL + Blender materials analysis
- Check: PBR values realistic voor material types (baksteen, glas, metaal, hout)
- Verify: texture tiling niet zichtbaar op flat surfaces
- Detect: AI-artifact textures

**3. Lighting Naturalism Checker**
- Tool: Python + histogram analysis + Ollama
- Verify: sun position realistic voor tijd/datum
- Check: interior light fixtures plausible
- Shadows physically correct

**4. Scene Composition Specialist**
- Tool: Ollama vision
- Check: visual storytelling (what draws eye)
- Environment context (not isolated building)
- Appropriate scale figures (mensen voor schaalgevoel)

**5. Performance for Runtime Validator**
- Tool: Python + scene stats
- Poly count within budget voor VR (90 FPS target)
- Texture memory reasonable
- Detect: optimization needed

## Judge

- Publish-ready: client deliverable quality
- Revise: specific fixes per jury feedback
- Reject: fundamental scene issue

## Cursor Prompt

```
Bouw NOVA v2 Blender Architecture Walkthrough Agent:

1. Python service `blender_arch/importer.py`:
   - FastAPI POST /import
   - Input: {file_path, file_type: 'ifc|fbx|datasmith|sketchup'}
   - Blender headless import
   - Proper scale correction
   - Material assignment from imported metadata
   - Output: processed .blend file

2. Python module `blender_arch/material_mapper.py`:
   - Map imported materials → NOVA architectural material library
   - PBR-correct substitutions
   - Factory function per material type:
     - map_brick(source_material) → realistic brick PBR
     - map_glass(source) → proper glass with IOR
     - map_metal(source) → anisotropic metal
     - map_wood(source) → wood grain

3. Python module `blender_arch/lighting_setup.py`:
   - HDRI environment setup
   - Sun position per tijd/datum (use solar calculator)
   - Interior lighting plausibility
   - Studio lighting voor detail shots

4. Python module `blender_arch/pdok_context_loader.py`:
   - Import omgeving uit PDOK gebakken city packages
   - Place new building in correct location
   - Context blending (lighting consistent)
   - Reference voor Fase 4 pipeline (shmup doesn't need this)

5. Python module `blender_arch/camera_paths.py`:
   - Generate cinematic camera paths:
     - Flyover (exterior reveal)
     - Walkthrough (interior tour)
     - Hero shots (key views)
   - Bezier curves, smooth interpolation
   - VR-aware (comfortable speeds, no motion sickness)

6. Python module `blender_arch/vr_preparation.py`:
   - Optimize scene voor VR runtime:
     - LOD generation
     - Bake lighting (faster runtime)
     - Reduce polygon count where not visible
     - Atlas textures
   - Export naar Unreal (via FBX/USD)

7. Python module `blender_arch/scale_validator.py`:
   - Jury member 1
   - Parse imported metadata
   - Measure objects in Blender scene
   - Compare tegen spec
   - Output: accurate/drift report

8. Python module `blender_arch/material_reviewer.py`:
   - Jury member 2
   - Render test views
   - Ollama analysis: "Does this material look realistic?"
   - PBR values validation

9. Python module `blender_arch/lighting_checker.py`:
   - Jury member 3
   - Histogram analysis voor overall balance
   - Shadow direction verification
   - Ollama naturalism check

10. Python module `blender_arch/composition_specialist.py`:
    - Jury member 4
    - Render hero views
    - Ollama composition analysis
    - Scale figure detection

11. Python module `blender_arch/performance_validator.py`:
    - Jury member 5
    - Scene statistics analysis
    - Budget compliance per target engine (Unreal VR)
    - Optimization recommendations

12. Python module `blender_arch/arch_judge.py`:
    - Aggregate 5 jury verdicts
    - Client-deliverable tier vs development tier

13. CLI voor complete workflows

Gebruik Blender 4.3+, Python 3.11, bpy, pyifc voor IFC,
Ollama Qwen VL 7B (of 32B voor detail), FastAPI.
```

## Unreal Engine integratie

Deze agent bereidt scenes voor Unreal Engine Import (34) voor:

**Export pipeline:**
```
Blender scene optimized
    ↓
FBX export (with materials baked as textures)
    ↓
Or: USD export (Unreal USD workflow)
    ↓
Or: Datasmith direct (preferred voor archviz)
    ↓
Unreal Engine Import Agent (34)
```

## Materials library architectuur

`materials_archviz.blend` bevat:
- Bricks (rode steen, gele steen, wit geschilderd)
- Wood (eiken, grenen, donker hardhout)
- Metals (staal, aluminium, roestig)
- Glass (helder, getint, gematteerd)
- Concrete (glad, gestempeld, verweerd)
- Roofing (tegel rood, tegel grijs, leien, bitumen)
- Ground surfaces (asfalt, klinkers, gras, grind)

All PBR with proper texture sizes (2K minimum voor close-ups).

## Lighting presets

```yaml
lighting_presets:
  bright_sunny_day:
    sun_altitude: 45
    sun_azimuth: 180  # Zuid
    sun_color: [1.0, 0.98, 0.90]
    hdri: studio_sunny.hdri
    exposure: 0.5
    
  golden_hour:
    sun_altitude: 15
    sun_azimuth: 270  # West
    sun_color: [1.0, 0.85, 0.70]
    hdri: sunset.hdri
    exposure: 0.3
    
  overcast:
    sun_altitude: 45
    sun_strength: 0.3
    sun_color: [0.95, 0.97, 1.0]
    hdri: overcast.hdri
    exposure: 0.7
    
  night_interior:
    sun_strength: 0
    interior_lights_on: true
    hdri: night_city.hdri
    exposure: 1.0
```

## VR Performance targets

Voor Meta Quest 3 standalone:
- 72 FPS minimum, 90 FPS target
- < 1M polygons in view
- < 2GB texture memory
- Lighting baked waar mogelijk

Voor PC VR (Quest Link, Index):
- 90 FPS minimum, 120 FPS target
- Up to 5M polygons
- Dynamic lighting OK

Agent rapporteert tegen deze targets.

## Test Scenario's

1. Import SketchUp model architect → scale correct + materials realistic
2. IFC bestand met BIM data → behoud attributes voor queries
3. VR preparation → 90 FPS haalbaar
4. PDOK context integration → building past in omgeving

## Success Metrics

- Scale accuracy: < 1% drift van spec
- Material realism: > 85% (subjectieve score)
- VR performance: > 90% targets halen
- Client satisfaction: > 80% approve zonder revisions

## Output

Per project:
- .blend file (editable source)
- Exported assets (FBX, USD, Datasmith)
- Reference renders (key shots)
- Performance report
- VR-ready flag

## Integratie

- Input van QGIS Analysis (31) en GRASS GIS (32) voor context
- Integrates PDOK city packages (via Blender Baker 14 output)
- Output naar Unreal Engine Import (34)
- 3D Model Jury (04) voor technical validation
- Distribution Agent (19) voor client delivery

## Workflow voor werk-pitch

Jouw showcase bij werk zou kunnen gebruiken:
1. Import bestaand SketchUp project uit werkmap
2. Blender Architecture workflow
3. PDOK context toevoegen (echte Hoogeveen)
4. VR prep
5. Unreal Import voor VR demo
6. Scherm-mirroring naar projectie voor publiek

Dat is concreet voorbeeld hoe deze agent directe waarde levert.
