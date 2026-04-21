# 20260420_003 - Bridge Adapters: Blender + Aseprite + PyQt5

**Van**: claude.ai  
**Naar**: Cursor  
**Prioriteit**: high (blocker voor batch 3 agent deployment)  
**Expected duration**: 2-3 uur

## Context

Inventory + installs compleet (handoffs 001, 002). Tools staan in PATH.

Nu bridge adapters bouwen zodat Hetzner agents deze tools kunnen aanroepen.

## Doel

3 nieuwe routes in `nova_host_bridge`:
- `/blender/*` voor 3D rendering + asset generation
- `/aseprite/*` voor pixel-art processing
- `/pyqt/*` voor Python Qt assembly operations

## Opdracht

### Stap 1: Adapter structuur

In bridge project (vermoedelijk `L:\!Nova V2\bridge\nova_host_bridge\` of vergelijkbaar):

```
nova_host_bridge/
├── app/
│   ├── main.py              # FastAPI entry
│   ├── config.py            # nova_config.yaml loader
│   └── adapters/
│       ├── freecad_adapter.py    # bestaand
│       ├── qgis_adapter.py       # bestaand  
│       ├── blender_adapter.py    # NIEUW
│       ├── aseprite_adapter.py   # NIEUW
│       └── pyqt_adapter.py       # NIEUW
```

### Stap 2: Blender adapter

Gebruik template uit `adapters/blender_adapter_template.py` (in expansion pakket).

Endpoints:
- `GET /blender/status` - availability + version
- `POST /blender/render` - render scene met parameters
- `POST /blender/export` - export GLB/FBX/OBJ  
- `POST /blender/script` - run Python script in Blender context

Blender draait headless via `blender --background --python script.py`.

Input validation via Pydantic models. Subprocess timeout 300s default (lange renders).

### Stap 3: Aseprite adapter

Gebruik template `adapters/aseprite_adapter_template.py`.

Endpoints:
- `GET /aseprite/status`
- `POST /aseprite/batch_export` - export sprite sheets uit .ase files
- `POST /aseprite/convert` - PNG → .ase of omgekeerd
- `POST /aseprite/palette_apply` - palette swap op sprites
- `POST /aseprite/animation_export` - animation frames export

Aseprite CLI via `aseprite --batch --script-param key=value`.

### Stap 4: PyQt5 adapter

Gebruik template `adapters/pyqt_adapter_template.py`.

PyQt5 is geen CLI tool maar Python library. Adapter roept Python subprocess met specifiek script.

Endpoints:
- `GET /pyqt/status`
- `POST /pyqt/sprite_assembly` - combineer meerdere sprites tot sheet (QPixmap + QPainter)
- `POST /pyqt/image_compose` - layer composition
- `POST /pyqt/metadata_sheet` - genereer sprite metadata JSON

Scripts inline in adapter of apart in `nova_host_bridge/scripts/pyqt_*.py`.

### Stap 5: Main app updaten

`app/main.py` moet nieuwe routers includen:

```python
from app.adapters import (
    freecad_adapter, 
    qgis_adapter,
    blender_adapter,    # NIEUW
    aseprite_adapter,   # NIEUW  
    pyqt_adapter,       # NIEUW
)

app.include_router(freecad_adapter.router)
app.include_router(qgis_adapter.router)
app.include_router(blender_adapter.router)   # NIEUW
app.include_router(aseprite_adapter.router)  # NIEUW
app.include_router(pyqt_adapter.router)      # NIEUW
```

### Stap 6: /tools endpoint uitbreiden

`/tools` moet nu alle 5 tools rapporteren. Code in `main.py`:

```python
@app.get("/tools")
def list_tools():
    from app.adapters import freecad_adapter, qgis_adapter, blender_adapter, aseprite_adapter, pyqt_adapter
    return {
        "freecad": freecad_adapter.status(),
        "qgis": qgis_adapter.status(),
        "blender": blender_adapter.status(),
        "aseprite": aseprite_adapter.status(),
        "pyqt": pyqt_adapter.status(),
    }
```

### Stap 7: Tests

Elke adapter heeft test file in `tests/adapters/test_<tool>_adapter.py`.

Minimum tests:
- status endpoint returnt correct
- Elke operation endpoint met happy path
- Error handling bij missende tool
- Timeout handling bij long operations

Gebruik templates in `tests/` folder van expansion pakket.

### Stap 8: Bridge restart + verificatie

```powershell
# Stop huidige bridge
# Start opnieuw
python -m uvicorn app.main:app --host 0.0.0.0 --port 8500

# Verify vanaf PowerShell (PC lokaal)
curl http://localhost:8500/tools

# Verify vanaf Hetzner
ssh root@178.104.207.194 "curl -s http://alex-main-1:8500/tools | jq"
```

Alle 5 tools moeten `available: true` tonen.

### Stap 9: End-to-end test

Vanaf Hetzner, test één echte operation per tool:

```bash
# Blender render test
curl -X POST http://alex-main-1:8500/blender/status

# Aseprite status
curl -X POST http://alex-main-1:8500/aseprite/status

# PyQt status
curl -X POST http://alex-main-1:8500/pyqt/status
```

Verwacht: 200 OK, JSON response met version info.

## Constraints

- **Behoud bestaande FreeCAD + QGIS routes** - niks breken
- **Async waar mogelijk** - lange operaties niet blocking
- **Timeouts per endpoint** gedefinieerd (niet infinite)
- **Geen state in adapter** - elk request is stateless
- **Error responses** volgens FastAPI HTTPException pattern
- **Logging** naar `nova_host_bridge.log`

## Success criteria

- 3 nieuwe adapters operationeel
- `/tools` endpoint toont 5 tools, allen available=true
- Tests slagen (pytest adapters/)
- End-to-end test vanaf Hetzner slaagt
- Git commit "bridge: blender + aseprite + pyqt adapters"
- Bridge responsive na herstart (geen 5s+ startup)

## Rapporteer terug

Schrijf `handoff/from_cursor/20260420_003_response.md`:

1. Per adapter: status en test resultaten
2. Code structuur (files created/modified)
3. Bridge startup tijd voor/na
4. /tools response (JSON)
5. End-to-end tests resultaten
6. Aanbeveling voor handoff 004 (Godot)

Update `current_baseline.md` met:
- 3 nieuwe adapters in bridge
- Batch 3 agents (22, 23, 25) kunnen nu volle implementatie gebruiken

## Notities voor Cursor

- Kijk naar bestaande `freecad_adapter.py` als template patroon
- Hergebruik config pattern (nova_config.yaml paths)
- Test eerst lokaal vanaf PC, dan via Tailscale vanaf Hetzner
- Als een adapter niet werkt: andere werken moeten blijven (graceful degradation)
- PyQt adapter is subtly - geen subprocess naar "pyqt" maar naar Python met specifieke scripts
