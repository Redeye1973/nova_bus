# 34. Unreal Engine Import Agent

## Doel
Unreal Engine 5 asset import en scene setup. Gespecialiseerd voor archviz en VR applications, parallel aan Godot Import (26) voor games.

## Scope
- Datasmith import (preferred voor archviz)
- USD import (modern pipeline)
- FBX fallback
- Blueprint setup voor VR interactions
- Lumen/Nanite configuration
- Cinematic sequences
- Pakages voor export (VR executable, packaged app)

## Jury (5 leden, zwaar - Unreal complexiteit)

**1. Import Fidelity Validator**
- Tool: Python + UE Python API
- Check: materials correct geïmporteerd
- Verify: geometry intact
- Detect: data loss in conversion

**2. Lumen Performance Checker**
- Tool: UE Python + stats
- Check: Lumen settings appropriate
- Verify: geen lichtfouten (artifacts, flickering)
- FPS targets haalbaar

**3. Nanite Compatibility Validator**
- Tool: Python + UE stats
- Check: meshes eligible voor Nanite
- Detect: issues die Nanite blokkeren (transparency, very small meshes)
- Output: Nanite/traditional mesh recommendation per asset

**4. VR Readiness Checker**
- Tool: UE Python + performance profiling
- Stereo rendering compatibility
- Foveated rendering settings
- Comfort settings (no motion sickness triggers)
- Plugin dependencies voor VR

**5. Scene Integration Validator**
- Tool: UE Python + scene analysis
- Check: collision setup correct voor walkthrough
- Verify: lighting bakes complete
- Player start placement correct

## Judge

- Production-ready: client VR experience ready
- Revise: specific UE settings/assets fixen
- Reject: import fundamentally broken

## Cursor Prompt

```
Bouw NOVA v2 Unreal Engine Import Agent:

1. Python service `unreal/datasmith_importer.py`:
   - FastAPI POST /import/datasmith
   - Input: {datasmith_file, ue_project_path}
   - Use UE Python API (requires Editor running of automation)
   - Or: UE commandlet voor headless
   - Import met juiste materials, hierarchy
   - Output: imported assets paths

2. Python service `unreal/usd_importer.py`:
   - FastAPI POST /import/usd
   - USD (Universal Scene Description) import
   - Modern Unreal workflow
   - Preserves references

3. Python service `unreal/fbx_importer.py`:
   - Fallback voor legacy workflows
   - Careful material mapping
   - Skeleton/animation handling indien nodig

4. Python service `unreal/scene_setup.py`:
   - Player start placement
   - Navigation mesh generation
   - Lighting setup (sky sphere, sun, sky light)
   - Post-process volume configuration

5. Python service `unreal/lumen_configurator.py`:
   - Apply Lumen settings per scene type
   - Quality tiers: epic/high/medium/low
   - Indirect lighting intensity
   - Surface cache settings

6. Python service `unreal/nanite_configurator.py`:
   - Per-asset Nanite decision
   - Check polycount, complexity
   - Enable where beneficial
   - Traditional mesh waar niet

7. Python service `unreal/vr_setup.py`:
   - VR Template integration
   - Teleport locomotion setup
   - Grab interaction setup (voor objects pick up)
   - Comfort settings

8. Python service `unreal/blueprint_generator.py`:
   - Generate common Blueprints:
     - VR_Walkthrough_Pawn
     - Interactive_Door
     - Info_Display
     - Tour_Guide
   - Python writes .uasset files (complex)
   - Or: templated .ucasset mechanism

9. Python service `unreal/cinematic_setup.py`:
   - Level Sequence generation
   - Camera path from Blender → UE sequencer
   - Cinematic rendering setup

10. Python service `unreal/packager.py`:
    - Package VR application
    - Windows executable of Quest 3 build
    - Proper ini config

11. Python service `unreal/import_fidelity_validator.py`:
    - Jury member 1
    - Compare imported met source Blender
    - Material property checks
    - Geometry integrity

12. Python service `unreal/lumen_performance_checker.py`:
    - Jury member 2
    - Test runs capture FPS
    - Check for light artifacts
    - Output: performance report

13. Python service `unreal/nanite_validator.py`:
    - Jury member 3
    - Check Nanite stats per mesh
    - Recommend enable/disable

14. Python service `unreal/vr_readiness.py`:
    - Jury member 4
    - Stereo rendering test
    - Plugin verification
    - Comfort check

15. Python service `unreal/scene_integration_validator.py`:
    - Jury member 5
    - Collision checks
    - Lighting bake completeness
    - Player start reachability

16. Python service `unreal/import_judge.py`:
    - Aggregate 5 jury

Gebruik Python 3.11, Unreal Python API (plus UnrealEnginePython),
FastAPI, subprocess voor UE editor automation.
```

## Unreal Python API notes

Unreal Editor heeft Python API maar:
- Editor moet running zijn voor sommige ops
- Commandlets voor headless operaties
- UnrealEnginePython plugin voor meer features
- Scripting Tools plugin vereist

Agent kan:
- Editor automation: launch editor, run Python, close
- Commandlet: headless imports
- Build system: voor packaging

## Asset import strategieen

**Datasmith (preferred archviz):**
- Preserves hierarchy best
- Materials translate better
- Supports incremental updates
- Requires Datasmith Exporter plugin in source (Blender/SketchUp)

**USD (modern):**
- Industry standard
- Good voor inter-application
- Unreal native support growing

**FBX (fallback):**
- Widely compatible
- Some data loss typical
- Materials often need manual fixup

**glTF (web-ready):**
- Modern, good compression
- Growing Unreal support
- Voor web + VR combined workflows

## VR deliverable formats

**Quest 3 standalone:**
- Build .apk of .aab
- Deploy via ADB or Meta Developer Hub
- 72 FPS target
- Simplified shaders (geen Lumen realtime)

**PC VR:**
- Windows executable
- SteamVR or Oculus PC runtime
- Full Lumen support
- 90 FPS target

**Archviz desktop (niet VR):**
- Standard Windows app
- Mouse/keyboard navigation
- Full quality render

## Test Scenario's

1. SketchUp project via Datasmith → correct materials + hierarchy
2. VR prep → Quest 3 deploy successful
3. Lumen scene → no artifacts, 72 FPS Quest
4. Interior walkthrough → player can navigate alle rooms

## Success Metrics

- Import fidelity: > 90% materials correct first-pass
- VR performance targets: > 85% halen
- Package success rate: > 95%
- Client satisfaction: > 80%

## Output

Per project:
- Unreal project met geïmporteerde assets
- Packaged VR app (indien gevraagd)
- Reference renders
- Performance reports
- Client handover package

## Integratie

- Input van Blender Architecture (33)
- Integreert PDOK context uit Blender Baker (14)
- Code Jury (02) valideert Blueprint code
- 3D Model Jury (04) voor mesh validation
- Distribution Agent (19) voor client deliverables

## Werk-pitch specifiek

Voor jouw werkgever showcase:
- Import huidige SketchUp project
- PDOK Hoogeveen context toevoegen
- VR-ready setup voor Meta Quest 3
- Scherm-mirroring config
- Packaged demo voor meenemen

Alles via deze agent orchestreerbaar, mits je Unreal Engine 5.7 draait (wat memory aangeeft).
