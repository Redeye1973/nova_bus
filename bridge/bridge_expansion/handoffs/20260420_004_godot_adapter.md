# 20260420_004 - Bridge Adapter: Godot

**Van**: claude.ai  
**Naar**: Cursor  
**Prioriteit**: normal (blocker voor batch 4 Agent 26)  
**Expected duration**: 1-2 uur

## Context

Bridge heeft nu 5 adapters (FreeCAD, QGIS, Blender, Aseprite, PyQt).
Volgende: Godot adapter voor asset import validatie + project tests.

## Doel

Godot adapter in bridge zodat Agent 26 Godot Import assets kan valideren, projecten kan testen, en export kan triggeren.

## Opdracht

### Godot adapter endpoints

```
GET  /godot/status          - version + available
POST /godot/import_test     - test of asset (sprite/mesh/audio) valide is voor Godot import
POST /godot/project_validate - valideer Godot project (project.godot + scenes + scripts)
POST /godot/headless_test   - run Godot headless met test scene
POST /godot/export_build    - trigger export (Windows/Linux/Android)
POST /godot/script_execute  - run GDScript in headless context
```

### Godot CLI flags

Belangrijkste flags die adapter gebruikt:

- `godot --headless --quit` - start/test zonder window
- `godot --headless --path <project_path>` - specificeer project
- `godot --headless --import` - force reimport assets
- `godot --headless --export-release "<preset>" "<output>"` - export
- `godot --headless --script <script.gd>` - run specifiek script
- `godot --check-only --path <path>` - syntax check scripts

### Adapter code structuur

Zie template `adapters/godot_adapter_template.py` uit expansion pakket.

Kerncomponenten:

```python
# Pydantic models
class ImportTestRequest(BaseModel):
    asset_path: str
    asset_type: Literal["sprite", "mesh", "audio", "scene"]
    project_path: str

class ProjectValidateRequest(BaseModel):
    project_path: str
    check_scripts: bool = True
    check_scenes: bool = True
    check_resources: bool = True

class HeadlessTestRequest(BaseModel):
    project_path: str
    test_scene: str
    timeout_seconds: int = 60
```

### Asset import testing

Voor `import_test`: kopieer asset naar test directory, open Godot headless, check of import zonder errors loopt. Parse output voor error detection.

### Project validation

Loop door project directory:
- `project.godot` exists + parseable
- Alle `.tscn` files valide (geen missing references)
- Alle `.gd` files syntactisch correct (via `godot --check-only`)
- Alle `.tres` resources loadbaar

Return report met per-file status.

### Headless test

Run Godot met test scene, capture logs, check voor:
- Errors in stderr
- Print statements in stdout (test assertions)
- Exit code 0
- Completion binnen timeout

### Export build

Export vereist `export_presets.cfg` in project. Adapter valideert dit eerst.

```python
@router.post("/export_build")
def export_build(request: ExportRequest):
    preset = request.preset  # "Windows Desktop", "Android", "Linux/X11"
    output = request.output_path
    project = request.project_path
    
    # Validate preset exists
    # Run: godot --headless --path {project} --export-release "{preset}" "{output}"
    # Monitor subprocess, log progress
    # Return: success, output_file, build_size, duration
```

### Integration met bestaande bridge

Update `app/main.py`:
```python
from app.adapters import godot_adapter
app.include_router(godot_adapter.router)
```

Update `/tools` endpoint:
```python
"godot": godot_adapter.status(),
```

### Tests

`tests/adapters/test_godot_adapter.py`:
- Status endpoint
- Import test met valid sprite (Pillow generate test PNG)
- Project validate op minimale Godot project (create in test fixtures)
- Headless test op scene die `print("ok")` doet
- Export test (indien export preset beschikbaar)

## Constraints

- **Geen Godot projecten modificeren** tijdens tests - kopieer eerst naar temp
- **Timeout protection** - headless tests mogen niet langer dan user-specified
- **Subprocess isolation** - elke test in eigen Godot instance
- **Dependency check**: niet alle Godot operaties vereisen GPU, maar sommige shaders wel. Log als GPU ontbreekt.

## Success criteria

- `/godot/status` returns version 4.6.2+ + available=true
- `/godot/import_test` detect valide en invalide assets correct
- `/godot/project_validate` rapporteert per-file status
- `/godot/headless_test` runt test scene
- Tests slagen
- Git commit "bridge: godot adapter"

## Rapporteer terug

Schrijf `handoff/from_cursor/20260420_004_response.md`:

1. Adapter endpoints implemented
2. Test resultaten
3. Godot version gedetecteerd
4. Performance (startup tijd headless Godot)
5. Eventuele issues met specifieke flags
6. Update `current_baseline.md`

## Notities

- Godot headless startup is ~2s - cache mag maar acceptabel
- Voor sprite imports: Godot maakt `.import` file, check bestaan
- Voor script check: `godot --check-only` is preferred boven runtime test
- Android export vereist Android SDK + keystore - voor nu skippen, documenteer in response

## Dependencies

Deze handoff heeft als prereq:
- Handoff 003 compleet (bridge adapters pattern gesetteld)
- Godot 4.6.2+ installed + in PATH (uit handoff 002)

## Volgende stap

Na deze handoff: Batch 4 Agent 26 Godot Import kan volle implementatie gebruiken.
Dan handoff 005 voor resterende tools (GRASS, GIMP, Krita, Inkscape).
