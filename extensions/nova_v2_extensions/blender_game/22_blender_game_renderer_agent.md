# 22. Blender Game Renderer Agent

## Doel
Multi-angle rendering van 3D models naar game-ready sprites. Voor Raptor-style shmup visuals.

## Scope
- STEP import + material application
- Lighting rig (consistent sun + fill + rim)
- Orthographic camera setup
- 16 rotation frame rendering
- Damage state variations
- Compositor pixel-perfect downscale
- Batch rendering orchestration

## Jury (3 leden, medium)

**1. Render Consistency Validator**
- Tool: Python + PIL image compare
- Check lighting identical tussen frames (same shadow angles)
- Verify camera positie unchanged
- Detect rendering anomalies (artifacts)

**2. Frame Alignment Checker**
- Tool: OpenCV feature matching
- Verify ship center consistent tussen rotation frames
- Check no drift tussen angles
- Validate expected rotation math

**3. Material Quality Reviewer**
- Tool: Ollama Qwen VL + PIL color analysis
- Check PBR values realistic
- Verify faction colors applied correctly
- Detect rendering issues (compression artifacts)

## Judge

Accept → Feed to Aseprite Processor
Revise → Re-render specifiek frames
Reject → Setup problem, fix scene

## Cursor Prompt

```
Bouw NOVA v2 Blender Game Renderer Agent:

1. Python script `blender_game/render_orchestrator.py`:
   - FastAPI POST /render
   - Input: {step_file, damage_states: [], rotation_frames: 16}
   - Spawn Blender subprocess per render job
   - Track progress, collect output
   - Timeout handling

2. Python script `blender_game/blender_script.py`:
   - Runs IN Blender: `blender --background --python blender_script.py`
   - Accepts args via sys.argv after --
   - Import STEP (needs STEPper addon or use CAD workbench)
   - Apply materials from library
   - Setup lighting + camera
   - Render loop over angles + damage states
   - Write to output folder

3. Python module `blender_game/material_library.py`:
   - Load materials.blend asset library
   - Apply materials by name
   - Damage state variants (pristine/damaged/critical)
   - PBR parameters per faction

4. Python module `blender_game/lighting_rig.py`:
   - Standardized 3-point lighting
   - Sun (45° down, 30° azimuth, warm white)
   - Fill (opposite, cool blue, 20% intensity)
   - Rim (behind, white, 40% intensity)
   - Function: apply_standard_lighting(scene)

5. Python module `blender_game/camera_rig.py`:
   - Orthographic camera per size category
   - 15° tilt (not 90° top-down)
   - Consistent framing

6. Python module `blender_game/compositor.py`:
   - Pixel-perfect downscale setup
   - Render op 4x target, downscale via Closest filter
   - Or: high samples + render target exact

7. Python module `blender_game/render_consistency_check.py`:
   - Jury member 1
   - Compare frames for consistency
   - Detect artifacts

8. Python module `blender_game/alignment_checker.py`:
   - Jury member 2
   - OpenCV feature tracking
   - Validate rotation alignment

9. Python module `blender_game/material_reviewer.py`:
   - Jury member 3
   - Ollama vision check on rendered frames
   - PBR sanity

10. Python module `blender_game/render_judge.py`:
    - Aggregate verdict

11. Asset file: materials.blend
    - Pre-configured materials library
    - Faction variants
    - Damage state blends

12. Shell script voor batch rendering met xvfb

Gebruik Blender 4.3+, Python 3.11, bpy API, OpenCV, PIL, Ollama.
```

## Performance Tuning

**Render settings Eevee voor speed:**
- Samples: 32 development, 64 final
- Denoising: on
- Volumetrics: off (unless needed)
- Reflections: SSR only (no baked probes tenzij nodig)

**Parallelization:**
- Multiple Blender instances (1 per CPU core)
- Each handles subset of angles
- Merge results at end

## Test Scenario's

1. Standard fighter STEP → 48 renders (16 × 3 damage) → consistent output
2. Extreme angle → lighting nog correct
3. High-poly boss STEP → completes within 2 hours

## Success Metrics

- Render consistency: > 95% (lighting/camera identiek tussen frames)
- Frame alignment accuracy: drift < 1 pixel
- Material quality: PBR values within ranges
- Batch success rate: > 90%

## Output

Per asset:
- Folder met individual PNG renders
- Organized per damage_state/angle
- Render metadata (settings, timing, output paths)
- Thumbnail preview sheet

## Integratie

- Input van FreeCAD Parametric (21) STEP files
- Output naar Aseprite Processor (23)
- 3D Model Jury (04) valideert render quality
- Apart van Blender Baker (14) die voor city baking is
