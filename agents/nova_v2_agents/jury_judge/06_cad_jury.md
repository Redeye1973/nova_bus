# 06. CAD Jury Agent

## Doel
Valideert CAD output uit FreeCAD/OpenSCAD voor manufacturing, 3D print, of game asset integratie.

## Scope
- FreeCAD parametric models (voor FINN, architect projecten)
- OpenSCAD script-based models
- STL exports voor 3D printing
- STEP files voor engineering toepassingen

## Jury Leden

**1. Manifold Geometry Validator**
- Tool: Python + FreeCAD Python API of trimesh
- Checkt: watertight mesh, printable
- Kritiek voor manufacturing

**2. Wall Thickness Analyzer**
- Tool: trimesh + analyse
- Checkt: minimum wall thickness voor manufacturing method
- Warning bij te dunne wanden (< 1mm voor print, < 3mm voor concrete)

**3. Structural Integrity Reviewer**
- Tool: Ollama + mesh analysis
- Checkt: plausibele structurele integriteit voor beoogd gebruik
- Niet FEA-niveau maar sanity check

**4. Parametric Robustness**
- Tool: FreeCAD Python scripting
- Test model met verschillende parameter waardes
- Checkt: breekt model bij edge cases?

**5. Dimensional Accuracy**
- Tool: Python + spec comparison
- Checkt: dimensies match specificatie
- Tolerance compliance voor precision parts

**6. Build Orientation Optimizer**
- Tool: trimesh + Ollama
- Voor 3D print: analyse optimale print orientation
- Voor game asset: standard orientation (Y-up etc)

## Judge

**CAD Judge**
- Per gebruik andere thresholds
- Print-ready vs Game-ready vs Draft

## Cursor Prompt

```
Bouw een NOVA v2 CAD Jury voor FreeCAD/OpenSCAD output:

1. Python service `cad_jury/manifold_check.py`:
   - Input: STL/STEP/FCStd file
   - Use trimesh voor watertight check
   - Output: {manifold, holes_count, non_manifold_edges: []}

2. Python service `cad_jury/wall_thickness.py`:
   - Analyseer mesh voor minimum wall
   - Use trimesh proximity checks
   - Output: {min_thickness, areas_below_threshold: []}

3. Python service `cad_jury/structural_review.py`:
   - Render model views
   - Send naar Ollama met structural questions
   - Output: {plausibility_score, concerns: []}

4. Python service `cad_jury/parametric_test.py`:
   - Alleen voor FreeCAD .FCStd files
   - Load parameters, vary binnen plausible range
   - Check dat model rebuildt succesvol
   - Output: {robust: bool, failing_params: []}

5. Python service `cad_jury/dimension_checker.py`:
   - Compare measurements tegen spec
   - Output tolerance compliance

6. Python service `cad_jury/orientation_optimizer.py`:
   - Voor print: minimize support material
   - Voor game: standard axes
   - Output: recommended orientation

7. Python service `cad_jury/cad_judge.py`:
   - Use-case specific rules
   - print-ready/game-ready/draft/reject

8. N8n workflow
9. Docker setup met FreeCAD installed

Gebruik Python 3.11, trimesh, FreeCAD Python bindings, FastAPI.
```

## Test Scenario's

1. Clean FreeCAD parametric model voor 3D print → print-ready
2. Thin walls onder 1mm → revise (thicken)
3. Non-manifold STL export → reject
4. Parametric model breekt bij edge parameter → revise

## Success Metrics

- Manifold detection: 99%+
- Thickness check accuracy: > 95%
- Parametric robustness detection: > 85%
