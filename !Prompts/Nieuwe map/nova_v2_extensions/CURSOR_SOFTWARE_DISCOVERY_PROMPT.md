# NOVA v2 Software Discovery Prompt voor Cursor

Deze prompt laat Cursor zelf zoeken naar alle NOVA v2 relevante software op C:\ en L:\ drives en genereert een config bestand met alle gevonden paden.

## Hoe gebruiken

1. Open Cursor in je NOVA v2 project folder
2. Open nieuwe Composer (Ctrl+I)
3. Kopieer de prompt hieronder
4. Cursor gaat zelf zoeken en config maken
5. Review output in `nova_config.yaml` en `discover_software.py`

## De prompt

```
Ik heb een NOVA v2 pipeline die verschillende software tools gebruikt (Blender, FreeCAD, Aseprite, QGIS, GRASS GIS, GIMP, Krita, Inkscape, Unreal Engine, Godot, Python, N8n, Ollama). Ik werk op Windows met software mogelijk geïnstalleerd op C:\ of L:\ drives.

Bouw een auto-discovery systeem dat:

1. Een Python script `scripts/discover_software.py` dat:
   - Scant Windows Registry voor installed software
   - Checkt standaard install locaties op C:\ en L:\
   - Zoekt via PATH environment variable
   - Detecteert executables voor alle NOVA tools
   - Valideert dat gevonden executables werken (basic --version call)
   - Output: nova_config.yaml met alle gevonden paden

2. Tools die gedetecteerd moeten worden:
   - Blender (.exe locatie + versie)
   - FreeCAD (FreeCAD.exe + FreeCADCmd.exe)
   - Aseprite (aseprite.exe)
   - QGIS (qgis-bin.exe + qgis_process-qgis.bat + Python)
   - GRASS GIS (grass84.bat of vergelijkbaar)
   - GIMP (gimp-2.10.exe of 3.0)
   - Krita (krita.exe)
   - Inkscape (inkscape.exe + inkscape.com voor CLI)
   - Unreal Engine (UnrealEditor.exe, UE_5.7 verwacht op L:\)
   - Godot (Godot_v4.x.exe, 4.6.2 of nieuwer)
   - Python (meerdere versies mogelijk)
   - Node.js + npm (voor N8n)
   - Docker Desktop
   - Ollama (ollama.exe + modellen folder)
   - Claude Code CLI (claude.exe op C:\Users\*\.local\bin\)
   - Cursor (cursor.exe)
   - Git

3. Standaard locaties om te checken (NIET uitputtend, Cursor voeg toe):
   - C:\Program Files\
   - C:\Program Files (x86)\
   - C:\Users\*\AppData\Local\Programs\
   - C:\Users\*\AppData\Roaming\
   - L:\ (alle subfolders tot 3 niveaus diep)
   - C:\Users\*\.local\bin\
   - C:\Tools\
   - C:\NOVA\
   - C:\GODOT_PROJECTS\

4. Per tool detection logic:
   - Zoek naar exact executable naam
   - Bij meerdere versies: prefereer nieuwste
   - Run --version (of equivalent) om te valideren
   - Vang timeouts en errors op (niet crashen bij één gefaalde detection)
   - Log wat gevonden is en wat niet

5. Output format (YAML):

```yaml
nova_config:
  discovered_at: "2026-04-19T10:30:00"
  system:
    os: Windows 11
    cpu: <detected>
    ram_gb: <detected>
    gpu: <detected>
  
  tools:
    blender:
      path: "L:\\Blender\\blender.exe"
      version: "4.3.2"
      installed: true
      validated: true
      python_path: "L:\\Blender\\4.3\\python\\bin\\python.exe"
    
    freecad:
      path: "C:\\Program Files\\FreeCAD 1.0\\bin\\FreeCAD.exe"
      cli_path: "C:\\Program Files\\FreeCAD 1.0\\bin\\FreeCADCmd.exe"
      version: "1.0.0"
      installed: true
      validated: true
    
    aseprite:
      path: "C:\\Program Files\\Aseprite\\Aseprite.exe"
      version: "1.3.x"
      installed: true
      validated: true
    
    qgis:
      path: "C:\\Program Files\\QGIS 3.34\\bin\\qgis-bin.exe"
      process_path: "C:\\Program Files\\QGIS 3.34\\bin\\qgis_process-qgis.bat"
      python_path: "C:\\Program Files\\QGIS 3.34\\apps\\Python3"
      version: "3.34"
      installed: true
      validated: true
    
    grass_gis:
      path: "C:\\Program Files\\GRASS GIS 8.3\\grass83.bat"
      version: "8.3"
      installed: false  # example: niet gevonden
      validated: false
      note: "Not detected, install from osgeo.org"
    
    # ... etc voor alle tools
    
    python:
      installations:
        - path: "C:\\Python311\\python.exe"
          version: "3.11.9"
          is_default: true
        - path: "C:\\Users\\awsme\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
          version: "3.12.1"
          is_default: false
    
    ollama:
      path: "C:\\Users\\awsme\\AppData\\Local\\Programs\\Ollama\\ollama.exe"
      models_folder: "C:\\Users\\awsme\\.ollama\\models"
      version: "0.x.x"
      available_models:
        - codestral:22b
        - llama3.2:3b
      installed: true
      validated: true
    
    claude_code:
      path: "C:\\Users\\awsme\\.local\\bin\\claude.exe"
      version: "x.x.x"
      installed: true
      validated: true
    
    unreal_engine:
      path: "L:\\UE_5.7\\Engine\\Binaries\\Win64\\UnrealEditor.exe"
      version: "5.7.x"
      installed: true
      validated: true
  
  nova_paths:
    projects_root: "L:\\Nova\\"
    ue_project: "L:\\Nova\\UnrealProjects\\HeliosHoogeveen\\HeliosHoogeveen.uproject"
    space_shooter: "L:\\Nova\\SpaceShooter"
    godot_projects: "C:\\GODOT_PROJECTS\\"
    agents_folder: "L:\\Nova\\agents\\"
    python_venv: "L:\\Nova\\agent_env\\Scripts\\python.exe"
    renders: "L:\\Nova\\Renders\\"
    key_backup: "C:\\NOVA\\Key Backup"
  
  not_found:
    - "Some tool that wasn't found"
  
  recommendations:
    - "Install GRASS GIS from osgeo.org"
    - "Update Blender to latest (found 4.3.2, latest is X.X.X)"
```

6. Python script structuur:

```python
#!/usr/bin/env python3
"""
NOVA v2 Software Discovery
Scans system voor alle NOVA-relevant tools, outputs config YAML.
"""
import os
import sys
import subprocess
import winreg
from pathlib import Path
import yaml
import platform
from datetime import datetime

class SoftwareDiscoverer:
    def __init__(self):
        self.found = {}
        self.not_found = []
        self.recommendations = []
        
    def scan_registry(self):
        """Scan Windows Registry voor installed software."""
        # HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
        # HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall
        pass
    
    def scan_common_locations(self):
        """Check standaard install folders."""
        locations = [
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
            Path("L:/"),
            # etc
        ]
        pass
    
    def detect_blender(self):
        """Vind Blender installatie."""
        # Check registry
        # Check common paths
        # Check PATH env var
        # Validate met --version
        pass
    
    def detect_freecad(self):
        pass
    
    def detect_aseprite(self):
        pass
    
    # ... meer detectors
    
    def validate_executable(self, path, version_flag='--version', timeout=10):
        """Run executable met --version om te valideren."""
        try:
            result = subprocess.run(
                [str(path), version_flag],
                capture_output=True, text=True, timeout=timeout
            )
            return True, result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return False, str(e)
    
    def detect_all(self):
        """Run alle detectors."""
        self.detect_blender()
        self.detect_freecad()
        # ... etc
    
    def generate_config(self, output_path="nova_config.yaml"):
        """Write discovered config to YAML."""
        config = {
            "nova_config": {
                "discovered_at": datetime.now().isoformat(),
                "system": self._get_system_info(),
                "tools": self.found,
                "nova_paths": self._detect_nova_paths(),
                "not_found": self.not_found,
                "recommendations": self.recommendations
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"Config written to {output_path}")
        self._print_summary()
    
    def _get_system_info(self):
        """Detect OS, CPU, RAM, GPU info."""
        import psutil
        return {
            "os": platform.platform(),
            "cpu": platform.processor(),
            "ram_gb": round(psutil.virtual_memory().total / (1024**3)),
            "gpu": self._detect_gpu()
        }
    
    def _detect_gpu(self):
        """Probeer GPU te detecteren via nvidia-smi of WMI."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except:
            return "Unknown"
    
    def _detect_nova_paths(self):
        """Vind NOVA specifieke project paths."""
        paths = {}
        
        nova_locations = [
            ("projects_root", "L:/Nova"),
            ("space_shooter", "L:/Nova/SpaceShooter"),
            ("ue_project", "L:/Nova/UnrealProjects/HeliosHoogeveen/HeliosHoogeveen.uproject"),
            ("godot_projects", "C:/GODOT_PROJECTS"),
            ("key_backup", "C:/NOVA/Key Backup"),
        ]
        
        for name, path in nova_locations:
            p = Path(path)
            if p.exists():
                paths[name] = str(p)
        
        return paths
    
    def _print_summary(self):
        """Print readable summary naar console."""
        print("\n=== NOVA v2 Software Discovery Summary ===\n")
        print(f"Found: {len(self.found)} tools")
        print(f"Not found: {len(self.not_found)} tools")
        
        print("\nFound tools:")
        for tool, info in self.found.items():
            status = "✓" if info.get('validated') else "?"
            print(f"  {status} {tool}: {info.get('path')}")
        
        if self.not_found:
            print("\nMissing tools:")
            for tool in self.not_found:
                print(f"  ✗ {tool}")
        
        if self.recommendations:
            print("\nRecommendations:")
            for rec in self.recommendations:
                print(f"  → {rec}")

if __name__ == "__main__":
    discoverer = SoftwareDiscoverer()
    discoverer.scan_registry()
    discoverer.scan_common_locations()
    discoverer.detect_all()
    discoverer.generate_config()
```

7. Voor tools die specifieke zoek-logica nodig hebben:

**Blender detection:**
```python
def detect_blender(self):
    # Registry check
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                             r"SOFTWARE\BlenderFoundation\Blender")
        install_dir = winreg.QueryValueEx(key, "Install_Dir")[0]
        blender_exe = Path(install_dir) / "blender.exe"
        if blender_exe.exists():
            self._add_tool('blender', blender_exe, '--version')
            return
    except FileNotFoundError:
        pass
    
    # Common paths
    common_paths = [
        Path("C:/Program Files/Blender Foundation/Blender 4.3/blender.exe"),
        Path("C:/Program Files/Blender Foundation/Blender 4.2/blender.exe"),
        Path("L:/Blender/blender.exe"),
        Path("C:/Blender/blender.exe"),
    ]
    
    # Glob for any Blender version
    for base in [Path("C:/Program Files/Blender Foundation"), Path("L:/")]:
        if base.exists():
            for blender_dir in base.glob("Blender*"):
                exe = blender_dir / "blender.exe"
                if exe.exists():
                    common_paths.append(exe)
    
    for path in common_paths:
        if path.exists():
            valid, output = self.validate_executable(path, '--version')
            if valid:
                version = self._parse_blender_version(output)
                self.found['blender'] = {
                    'path': str(path),
                    'version': version,
                    'installed': True,
                    'validated': True,
                    'python_path': str(path.parent / f"{version[:3]}/python/bin/python.exe")
                }
                return
    
    self.not_found.append('blender')
    self.recommendations.append("Install Blender from blender.org")
```

**Unreal Engine detection:**
```python
def detect_unreal_engine(self):
    # Typische locaties incl. L: per jouw memory
    candidates = [
        Path("L:/UE_5.7/Engine/Binaries/Win64/UnrealEditor.exe"),
        Path("L:/UE_5.6/Engine/Binaries/Win64/UnrealEditor.exe"),
        Path("C:/Program Files/Epic Games"),
        Path("L:/Program Files/Epic Games"),
    ]
    
    # Epic Games Launcher scans
    epic_dirs = []
    for candidate in [Path("C:/Program Files/Epic Games"), Path("L:/Program Files/Epic Games")]:
        if candidate.exists():
            for ue_dir in candidate.glob("UE_*"):
                epic_dirs.append(ue_dir / "Engine/Binaries/Win64/UnrealEditor.exe")
    
    # Combineer en check
    all_paths = candidates + epic_dirs
    for path in all_paths:
        if path.exists():
            # UE --version werkt niet, check via bestand bestaan + executeerbaarheid
            self.found['unreal_engine'] = {
                'path': str(path),
                'version': self._parse_ue_version_from_path(path),
                'installed': True,
                'validated': True
            }
            return
    
    self.not_found.append('unreal_engine')
```

**Ollama met model detection:**
```python
def detect_ollama(self):
    # Standaard locatie
    ollama_exe = Path(os.environ.get('USERPROFILE', '')) / "AppData/Local/Programs/Ollama/ollama.exe"
    
    if ollama_exe.exists():
        valid, output = self.validate_executable(ollama_exe, '--version')
        if valid:
            # List models
            models_result = subprocess.run(
                [str(ollama_exe), 'list'],
                capture_output=True, text=True, timeout=10
            )
            models = self._parse_ollama_models(models_result.stdout)
            
            self.found['ollama'] = {
                'path': str(ollama_exe),
                'models_folder': str(Path(os.environ['USERPROFILE']) / ".ollama/models"),
                'version': output.strip(),
                'available_models': models,
                'installed': True,
                'validated': True
            }
            return
    
    self.not_found.append('ollama')
```

8. Extra helper script `scripts/apply_config.py`:
   - Leest nova_config.yaml
   - Genereert environment variables file (.env)
   - Creates symlinks waar nodig
   - Generates tool-specific config files
   - Updates N8n credentials (waar mogelijk)

9. Integration met andere NOVA v2 agents:
   - Elke agent leest nova_config.yaml bij startup
   - Environment variables auto-geset
   - Geen hardcoded paths meer in agent code

10. Run instructions:
    ```bash
    # Install dependencies
    pip install pyyaml psutil pywin32
    
    # Run discovery
    python scripts/discover_software.py
    
    # Review output
    cat nova_config.yaml
    
    # Apply to environment
    python scripts/apply_config.py
    ```

Zorg voor:
- Graceful handling als tool niet gevonden (niet crashen)
- Duidelijke console output tijdens scanning
- Support voor meerdere versies (latest preferred)
- Cross-reference met PATH env var
- Logs in JSON format voor latere analyse
- Resumable bij grote scans (cache results)

Test dit lokaal en verfijn per tool waar detection faalt.
```

## Wat Cursor gaat bouwen

Na deze prompt krijg je:

1. `scripts/discover_software.py` - Hoofdscript
2. `scripts/apply_config.py` - Config toepassingsscript  
3. `scripts/detectors/` - Per-tool detection modules
4. `nova_config.yaml` - Gegenereerde config (na run)
5. `.env` - Environment variables file

## Verwachte output bij eerste run

```
=== NOVA v2 Software Discovery ===
Scanning registry...
Scanning C:\Program Files...
Scanning C:\Program Files (x86)...
Scanning L:\...
Scanning user directories...
Validating found executables...

✓ Blender 4.3.2 found at L:\Blender\blender.exe
✓ FreeCAD 1.0.0 found at C:\Program Files\FreeCAD 1.0
✓ Aseprite found at C:\Program Files\Aseprite
✓ QGIS 3.34 found at C:\Program Files\QGIS 3.34
✗ GRASS GIS not found
✓ GIMP 2.10.38 found
✗ Krita not found
✓ Inkscape 1.3 found
✓ Unreal Engine 5.7 found at L:\UE_5.7\
✓ Godot 4.6.2 found at C:\GODOT_PROJECTS\
✓ Python 3.11.9 found at C:\Python311
✓ Node.js 20.11.0 found
✓ Docker Desktop running
✓ Ollama found with 2 models (codestral, llama3.2)
✓ Claude Code found at C:\Users\awsme\.local\bin\claude.exe
✓ Cursor found
✓ Git 2.43 found

Config written to nova_config.yaml

Summary:
- Found: 15 tools
- Missing: 2 tools (GRASS GIS, Krita)

Recommendations:
- Install GRASS GIS from osgeo.org
- Install Krita from krita.org
```

## Update workflow

Als je nieuwe software installeert of upgrade:

```bash
# Re-run discovery
python scripts/discover_software.py --refresh

# Apply updated config
python scripts/apply_config.py
```

NOVA agents picken nieuwe paths automatisch op bij volgende startup.

## Integration met NOVA v2 agents

Alle NOVA v2 agents (01-35) lezen `nova_config.yaml` bij startup:

```python
# In elke agent:
import yaml
from pathlib import Path

config_path = Path(__file__).parent.parent / "nova_config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

BLENDER_PATH = config['nova_config']['tools']['blender']['path']
ASEPRITE_PATH = config['nova_config']['tools']['aseprite']['path']
# etc.
```

Dit voorkomt hardcoded paths en maakt agents portable tussen machines.

## Veiligheid

Script vraagt niet om admin rights, alleen read access. Raakt niks aan registry of files, alleen leest.

Bij eerste run: verify output voor je apply_config runt.
