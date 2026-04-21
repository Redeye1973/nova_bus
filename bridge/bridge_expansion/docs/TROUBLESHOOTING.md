# Bridge Expansion Troubleshooting

## Adapter import errors na toevoegen

Symptoom: bridge start niet meer na nieuwe adapter

```
ImportError: cannot import name 'blender_adapter'
```

Checks:
1. File bestaat: `adapters/blender_adapter.py`
2. `__init__.py` in adapters/ folder aanwezig
3. Import in main.py correct: `from app.adapters import blender_adapter`
4. Geen syntax errors: `python -c "from app.adapters import blender_adapter"`

## Tool niet gevonden na install

Symptoom: `/tools` zegt available=false terwijl install is gedaan

Oorzaak 1: PATH niet refreshed
```powershell
# In huidige sessie
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Bridge restart nodig voor persistent fix
```

Oorzaak 2: Bridge draait in andere context (Windows service)
- Service heeft eigen environment
- NSSM: `nssm set NOVA_Bridge AppEnvironmentExtra PATH=C:\Program Files\Blender...;...`
- Service restart na elke tool install

Oorzaak 3: Wrong binary name
- Blender op Windows is meestal `blender.exe` in PATH, maar soms alleen als `blender-launcher.exe`
- Check: `Get-Command blender | Select-Object Source`

## Adapter subprocess hangt

Symptoom: request timeout na 60s+

Debug stappen:
```powershell
# Run tool command handmatig met exact zelfde args
# Bijv voor Blender:
blender --background --python script.py

# Kijk wat er gebeurt:
# - Wacht op gebruikersinput? (bv. crash dialog)
# - Kan niet render? (missing GPU driver)
# - Asset niet vindbaar? (paden)
```

Fix:
- Korter timeout: `"timeout_seconds": 30`
- Specifieker script dat geen GUI triggers
- Gebruik `--no-prompt` waar beschikbaar

## PyQt DLL errors op Windows

Symptoom: `ImportError: DLL load failed while importing QtCore`

Oorzaak: PyQt5 wheel conflict met Python version

Fix:
```powershell
pip uninstall PyQt5 PyQt5-sip
pip install PyQt5==5.15.10
```

Als blijft: gebruik PyQt6 of PySide6 variant.

## Godot Android export faalt

Symptoom: export_build returnt exit 1 voor Android preset

Oorzaak: Android SDK + keystore niet geconfigureerd

Workaround voor nu:
- Skip Android exports, documenteer
- Android export via Godot GUI eenmalig, daarna CLI werkt
- Volgt uit batch 4 / release prep

## Bridge startup langzaam

Symptoom: bridge doet 10+ sec over opstarten

Oorzaak: elke adapter doet status check bij import

Fix: lazy status (alleen bij /status call) in plaats van op import:

```python
# Bad: status check at import time
TOOL_PATH = _find_tool()  # runs at import

# Good: lazy check
_tool_path = None
def get_tool_path():
    global _tool_path
    if _tool_path is None:
        _tool_path = _find_tool()
    return _tool_path
```

## GRASS GIS complexe location setup

Symptoom: GRASS commands falen met "no location set"

Context: GRASS heeft unique state model (locations + mapsets)

Solution: adapter maakt default location per project in tmpdir:

```python
def _ensure_grass_location(project_id):
    loc_dir = f"/tmp/grass_locations/{project_id}"
    if not Path(loc_dir).exists():
        # Create via grass --tmp-location
        subprocess.run([GRASS_PATH, "-c", "EPSG:28992", "-e", loc_dir])
    return loc_dir
```

## Aseprite CLI silent (no output)

Symptoom: `aseprite --batch ...` returnt 0 exit maar geen file

Oorzaak: Aseprite silent fail op ongeldige sprite/palette

Fix: altijd `--verbose` toevoegen voor diagnose:

```python
args = ["--verbose", "--batch", input_file, ...]
```

Parse stdout/stderr voor errors.

## Krita plugin niet gevonden

Symptoom: krita --script fails

Oorzaak: Krita scripting is Python 3 based, package dependencies

Fix: package in Krita resource folder, of use Krita's built-in Python:

```powershell
# Vinden waar Krita z'n Python heeft
krita --help | findstr python
```

## Inkscape 1.3+ vs oude syntax

Symptoom: Inkscape CLI commands werken niet

Oorzaak: Inkscape 1.3 heeft complete nieuwe CLI (actions-based)

Check version eerst:
```bash
inkscape --version
```

1.3+:
```bash
inkscape --export-type=png --export-filename=out.png in.svg
# of
inkscape --actions="select-all;export-type:png;export-do" in.svg
```

1.0-1.2:
```bash
inkscape --export-png=out.png in.svg
```

Adapter moet versie detecteren en juiste syntax kiezen.

## Debug mode bridge

Zet bridge in debug mode voor meer logging:

```python
# app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Of env var:
```powershell
$env:NOVA_BRIDGE_LOG_LEVEL = "DEBUG"
```

## Contact with running bridge from WSL

Als je bridge wilt testen vanuit WSL (Ubuntu in Windows):

Tailscale IP van PC werkt:
```bash
curl http://100.64.0.2:8500/tools
```

Of gebruik `host.docker.internal` wanneer in container.

## Rollback een slechte adapter

Als nieuwe adapter het hele bridge kapot maakt:

```powershell
cd L:\!Nova V2\bridge\nova_host_bridge
git log --oneline -10
git revert <commit-hash-met-slechte-adapter>
# Restart bridge
```

Of tijdelijk commenteer in main.py:
```python
# app.include_router(broken_adapter.router)
```
