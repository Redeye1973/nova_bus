# 04. 3D Model Jury Agent

## Doel
Beoordeelt 3D models uit Meshy, Blender, FreeCAD op game-ready en professional quality.

## Scope
- Meshy AI-gegenereerde models
- Blender output (handmatig of procedureel)
- FreeCAD parametric models
- Asset-kit componenten voor NORA/FINN city packages

## Jury Leden

**1. Topology Validator**
- Tool: Blender headless + Python (bmesh)
- Checkt: clean quads, manifold geometry, geen N-gons op verkeerde plekken
- Output: mesh statistics + issue locations

**2. Polygon Budget Checker**
- Tool: Python + file parsing
- Checkt: polycount binnen target (game: ~5000 tri, FINN: ~20000 tri)
- Multi-LOD aanwezig?

**3. UV Mapping Validator**
- Tool: Blender headless
- Checkt: UV efficient unwrapped, geen overlaps (tenzij intentioneel), texture space gebruik
- Output: UV coverage percentage + overlap report

**4. Scale Consistency**
- Tool: Python + metadata
- Checkt: juiste wereld-eenheden, logische afmetingen voor asset type
- Belangrijk voor city-kit coherentie

**5. Pivot Point Checker**
- Tool: Blender headless
- Checkt: logisch pivot voor rotation (voet voor characters, bottom-center voor buildings)

**6. Silhouette Reviewer**
- Tool: Blender render vanuit 4 hoeken + Ollama vision
- Checkt: herkenbaar silhouet van verschillende kanten

**7. Normal Map Validator** (indien aanwezig)
- Tool: PIL + analysis
- Checkt: correct baked, juiste tangent space, no seams visible

**8. PBR Materials Check**
- Tool: Python + Blender
- Checkt: albedo, roughness, metallic waardes plausible
- Detecteert slechte AI-gegenereerde textures

## Judge

**3D Judge**
- Tool: Ollama met rendered views
- Logic:
  - Non-manifold → reject (breekt physics)
  - Over budget → revise (decimate mesh)
  - UV issues → revise (re-unwrap)
  - Scale wrong → revise (auto-fix mogelijk)
  - Silhouette weak → experimental bucket
  - Alles ok → accept game-ready

## N8n Workflow

```
Trigger: nieuw 3D model in queue
    ↓
Blender headless prepare (import, basic checks)
    ↓
Parallel jury:
    ├─ Topology via bmesh
    ├─ Polygon count
    ├─ UV mapping
    ├─ Scale check
    ├─ Pivot check  
    ├─ Silhouette render + analyse
    ├─ Normal map (conditional)
    └─ PBR materials
    ↓
Merge
    ↓
3D Judge
    ↓
Verdict
    ↓
Bij revise: auto-fix script proberen
    ↓
Re-run jury (max 2x)
    ↓
Final verdict
```

## Cursor Prompt

```
Bouw een NOVA v2 3D Model Jury voor Meshy/Blender output validatie:

1. Python service `jury_3d/topology_validator.py`:
   - FastAPI POST /topology
   - Input: GLB/FBX/OBJ file path
   - Output: {manifold: bool, quad_ratio, ngon_count, issues: []}
   - Gebruik Blender as Python library (bpy) headless
   - Commands: import mesh, bmesh.ops.recalc_face_normals, check manifold

2. Python service `jury_3d/polygon_budget.py`:
   - Input: file + target_budget
   - Output: {tris, verts, within_budget, lod_count}
   - Parse GLB/FBX metadata
   - Check LOD chain aanwezig

3. Python service `jury_3d/uv_validator.py`:
   - Blender headless UV analysis
   - Output: {coverage_pct, overlaps: [], efficiency_score}
   - Detect overlapping UV islands
   - Calculate texture space usage

4. Python service `jury_3d/scale_checker.py`:
   - Input: file + expected_category (building|character|prop|vehicle)
   - Check bounding box vs category expectations
   - Output: {scale_correct: bool, actual_size, expected_range}

5. Python service `jury_3d/silhouette_reviewer.py`:
   - Render 4 orthographic views via Blender headless
   - Send renders naar Ollama Qwen VL
   - Vraag: is dit silhouet herkenbaar als [category]?
   - Output: {recognizable: bool, score, weak_angles: []}

6. Python service `jury_3d/pbr_check.py`:
   - Analyseer material values
   - Check albedo niet > 0.9 of < 0.02 (onrealistisch)
   - Check roughness/metallic distributions
   - Detect AI-artifact textures (onnatuurlijke patterns)

7. Python service `jury_3d/model_judge.py`:
   - Aggregate scores
   - Category-specific rules (building vs character vs weapon)
   - Output verdict

8. Auto-fix service `jury_3d/auto_fix.py`:
   - Bij revise verdict, probeer automatic fixes:
     - Decimate voor over-budget
     - Recompute normals voor flipped faces
     - Auto-pivot voor wrong pivot
   - Return modified file, re-submit aan jury

9. N8n workflow met retry logic:
   - First jury run
   - Auto-fix attempt als verdict = revise
   - Second jury run
   - Final verdict

10. Docker compose met Blender image (blender/blender:latest)

Gebruik Python 3.11, bpy (via Blender install of blender-bpy-wheels),
FastAPI, structured logging.
```

## Integratie met Meshy

Meshy output → automatische download via API → jury → approved/experimental/reject routing.

Bij reject: nieuwe Meshy generation met feedback prompt.

## Test Scenario's

1. Clean Meshy fighter model (game-ready) → accept
2. High-poly model > budget → revise + auto-decimate
3. Non-manifold model (common Meshy issue) → reject of repair
4. Scale wrong (1m building) → revise (auto-scale)
5. AI-artifact textures → reject

## Success Metrics

- Non-manifold detection: 99%+
- Polygon budget enforcement: 100%
- Auto-fix success rate: > 60%
- False accept rate: < 5%
