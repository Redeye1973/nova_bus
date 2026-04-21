# 21. FreeCAD Parametric Agent

## Doel
Genereert parametric 3D models voor asset varianten. Eén base model → 20+ varianten door parameter variatie.

## Scope
- Parametric base models (ships, buildings, vehicles, props)
- Component library (wings, engines, weapons, cockpits)
- Variant assembly via parameter matrices
- STEP export voor Blender pipeline

## Jury (3 leden, medium)

**1. Parametric Robustness Tester**
- Tool: FreeCAD Python API + test range
- Varieer parameters over volledige range
- Detect: model breekt bij edge values, geometry failures
- Output: robust/brittle per parameter

**2. Dimensional Coherence Validator**
- Tool: Python + FreeCAD
- Checkt: afmetingen passen binnen category (fighter size, boss size)
- Verify mounting points correct
- Check scale consistentie

**3. STEP Export Quality Checker**
- Tool: Python + trimesh
- Load exported STEP
- Verify manifold, proper tessellation
- Check geen data-loss vs FreeCAD source

## Judge

Accept → Export batch naar Blender queue
Revise → Fix parametric expressions
Reject → Redesign base model

## Cursor Prompt

```
Bouw NOVA v2 FreeCAD Parametric Agent:

1. Python service `freecad/base_builder.py`:
   - FastAPI POST /model/build-base
   - Input: {category, dimensions, mount_points_config}
   - Use FreeCAD.cmd headless Python
   - Create Spreadsheet met parameters
   - Hook geometry to parameters via expressions
   - Output: .FCStd file path

2. Python service `freecad/variant_generator.py`:
   - FastAPI POST /variants/generate
   - Input: {base_model, parameter_matrix, count}
   - For each parameter combination:
     - Load base
     - Set parameters
     - Recompute
     - Save as variant
     - Export STEP
   - Output: list of variant paths

3. Python service `freecad/component_library.py`:
   - Manage reusable components (wings, engines, etc)
   - Load from .FCStd files
   - Assemble via boolean operations
   - Standardized mount points (coordinates system)

4. Python service `freecad/robustness_tester.py`:
   - Jury member 1
   - For each parameter: vary over range
   - Catch FreeCAD exceptions
   - Output: {robust: bool, brittle_params: []}

5. Python service `freecad/dimension_validator.py`:
   - Jury member 2
   - Parse FCStd metadata
   - Check bounding box vs category expectations
   - Verify mount points correct coordinates

6. Python service `freecad/step_validator.py`:
   - Jury member 3
   - Load STEP via trimesh
   - Check manifold, face count reasonable
   - Compare bounds met FreeCAD source

7. Python service `freecad/parametric_judge.py`:
   - Aggregate jury verdicts
   - Accept/revise/reject

8. CLI tool: 
   - `freecad-cli build-base --category fighter`
   - `freecad-cli generate --base <f> --matrix variants.yaml`
   - `freecad-cli export --variant <n>`

9. N8n workflow

Gebruik: FreeCAD 1.0+ Python, trimesh, PyYAML, FastAPI.
Run via `freecad.cmd --python script.py` of Python met FreeCAD sys.path.
```

## Output

Per run:
- N variants .FCStd files
- STEP exports voor Blender
- Metadata JSON met parameter values
- Quality report per variant

## Test Scenario's

1. Fighter base → 20 varianten → alle STEP exports valid
2. Edge parameter value → robust (niet crashen)
3. Boss size model → dimensional validator accepts
4. Broken base model → clear feedback naar designer

## Success Metrics

- Variant generation success rate: > 95%
- STEP export validity: 100%
- Parameter robustness coverage: alle params getest
- Cross-compatibility Blender: 100%

## Integratie

- Output feed Blender Game Renderer (22)
- STEP files gevalideerd door CAD Jury (06)
- Parameter matrices gestuurd door Design Fase Agent (20)
