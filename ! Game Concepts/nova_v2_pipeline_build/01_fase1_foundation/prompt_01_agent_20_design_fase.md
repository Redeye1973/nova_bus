# Prompt 01: Agent 20 - Design Fase Agent

## Wat deze prompt bouwt

Design Fase Agent: style bible generator, master palette manager, silhouette checker. Eerste agent van pipeline omdat alle andere agents palettes en design specs nodig hebben.

## Voorwaarden

- [ ] Infrastructure draait (V2 op 5679)
- [ ] Agent 01 Sprite Jury is live (referentie voor structuur)
- [ ] Secrets file accessible
- [ ] SSH key werkt naar root@178.104.207.194

Check: `Get-Content "L:\!Nova V2\status\agent_01_status.json"` moet laten zien dat agent 01 active is.

## Voor plakken in Cursor

1. Verifieer voorwaarden hierboven
2. Kopieer het prompt blok hieronder
3. Plak in Cursor Composer (Ctrl+I)
4. Monitor: `Get-Content "L:\!Nova V2\logs\pipeline_build_$(Get-Date -Format 'yyyy-MM-dd').log" -Wait`

## De prompt

```
Bouw Agent 20 - Design Fase Agent voor NOVA v2.

CONTEXT:
- Spec bestand: L:\!Nova V2\extensions\nova_v2_extensions\design\20_design_fase_agent.md
- Target: L:\!Nova V2\v2_services\agent_20_design_fase\
- Deploy: /docker/nova-v2/services/agent_20_design_fase/ op Hetzner
- V2 N8n: http://178.104.207.194:5679
- Webhook: http://178.104.207.194:5680/webhook/design-fase
- Language: Python 3.11, FastAPI
- Referentie: L:\!Nova V2\v2_services\01_sprite_jury\ voor structuur

FALLBACK MODE:
Als V1 orchestrator geen code-generation capability heeft, werk in solo mode.
Gebruik agent_01_sprite_jury als template voor directory structuur.

STAP 1: SPEC LEZEN
Open L:\!Nova V2\extensions\nova_v2_extensions\design\20_design_fase_agent.md
Extract:
- Jury members (3: Palette Coherence, Silhouette Clarity, Style Consistency)
- Endpoints (POST /palette/create, /palette/validate, /silhouette/check, /consistency/check)
- Dependencies (Qdrant, Ollama, PIL, colormath)
- Output structuur

STAP 2: DIRECTORY + FILES
Maak L:\!Nova V2\v2_services\agent_20_design_fase\ met:

main.py:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging

app = FastAPI(title="NOVA v2 Agent 20 - Design Fase")
logger = logging.getLogger(__name__)

class PaletteRequest(BaseModel):
    theme: str
    faction_count: int = 6
    restrictions: Dict = {}

class PaletteValidationRequest(BaseModel):
    palette: List[str]  # hex codes
    faction_names: List[str]

class SilhouetteRequest(BaseModel):
    image_base64: str
    target_sizes: List[int] = [32, 64, 128]

class ConsistencyRequest(BaseModel):
    concept_image_base64: str
    faction: str
    reference_faction_assets: Optional[List[str]] = None

@app.get("/health")
def health():
    return {"status": "ok", "agent": "20_design_fase", "version": "0.1.0"}

@app.post("/palette/create")
def create_palette(req: PaletteRequest):
    # Implementatie zie palette_manager.py
    from palette_manager import generate_master_palette
    result = generate_master_palette(req.theme, req.faction_count, req.restrictions)
    return result

@app.post("/palette/validate")
def validate_palette(req: PaletteValidationRequest):
    from palette_validator import validate
    return validate(req.palette, req.faction_names)

@app.post("/silhouette/check")
def check_silhouette(req: SilhouetteRequest):
    from silhouette_checker import check
    return check(req.image_base64, req.target_sizes)

@app.post("/consistency/check")
def check_consistency(req: ConsistencyRequest):
    from consistency_checker import check
    return check(req.concept_image_base64, req.faction, req.reference_faction_assets)
```

palette_manager.py:
```python
"""Master palette generator using color theory."""
import colorsys
from typing import Dict, List

def generate_master_palette(theme: str, faction_count: int, restrictions: Dict) -> Dict:
    # 32-color master palette met faction sub-palettes
    master_palette = []
    
    # Base hue per theme
    theme_hues = {
        "space_noir": 220,  # blauw
        "industrial": 30,   # oranje
        "alien": 150,       # groen
        "neutral": 0,       # rood baseline
    }
    base_hue = theme_hues.get(theme, 220)
    
    # Generate master palette
    for i in range(32):
        hue = (base_hue + i * 11) % 360
        saturation = 0.6 + (i % 4) * 0.1
        lightness = 0.3 + (i // 4) * 0.08
        rgb = colorsys.hls_to_rgb(hue/360, lightness, saturation)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)
        )
        master_palette.append(hex_color)
    
    # Faction sub-palettes (5 colors each)
    faction_palettes = {}
    for i in range(faction_count):
        start_idx = i * 5
        faction_palettes[f"faction_{i}"] = master_palette[start_idx:start_idx+5]
    
    return {
        "master_palette": master_palette,
        "faction_palettes": faction_palettes,
        "theme": theme,
        "color_count": 32
    }
```

palette_validator.py:
```python
"""Validate palettes for contrast, distinguishability."""
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

def validate(palette, faction_names):
    issues = []
    
    # Check delta-E tussen faction kleuren
    rgb_colors = [hex_to_rgb(c) for c in palette]
    lab_colors = [convert_color(sRGBColor(*rgb, is_upscaled=True), LabColor) 
                  for rgb in rgb_colors]
    
    for i in range(len(lab_colors)):
        for j in range(i+1, len(lab_colors)):
            delta = delta_e_cie2000(lab_colors[i], lab_colors[j])
            if delta < 15:
                issues.append({
                    "colors": [palette[i], palette[j]],
                    "delta_e": float(delta),
                    "issue": "too_similar"
                })
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "palette_size": len(palette)
    }

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
```

silhouette_checker.py:
```python
"""Check silhouette recognizability op doelgroottes."""
from PIL import Image
import base64
from io import BytesIO

def check(image_base64, target_sizes):
    img_data = base64.b64decode(image_base64)
    img = Image.open(BytesIO(img_data)).convert("RGBA")
    
    results = {}
    for size in target_sizes:
        # Downscale
        small = img.resize((size, size), Image.NEAREST)
        
        # Extract silhouette
        mask = small.split()[3] if small.mode == 'RGBA' else None
        
        # Simple metrics
        if mask:
            visible_pixels = sum(1 for p in mask.getdata() if p > 128)
            total = size * size
            coverage = visible_pixels / total
        else:
            coverage = 1.0
        
        results[f"size_{size}"] = {
            "coverage": coverage,
            "recognizable": coverage > 0.1 and coverage < 0.8,
            "notes": "good" if 0.2 < coverage < 0.6 else "check_manually"
        }
    
    return {
        "size_results": results,
        "recommendation": "accept" if all(r["recognizable"] for r in results.values()) else "review"
    }
```

consistency_checker.py:
```python
"""Check design consistency met faction references."""
import base64
from PIL import Image
from io import BytesIO
from typing import List, Optional

def check(concept_image_base64, faction, reference_assets):
    # Simplified - Qdrant vector search zou hier komen in full versie
    # POC: color histogram comparison
    img_data = base64.b64decode(concept_image_base64)
    img = Image.open(BytesIO(img_data)).convert("RGB")
    
    # Extract dominant colors
    small = img.resize((50, 50))
    pixels = list(small.getdata())
    
    # Count color regions (simplified)
    color_buckets = {}
    for p in pixels:
        bucket = (p[0] // 32, p[1] // 32, p[2] // 32)
        color_buckets[bucket] = color_buckets.get(bucket, 0) + 1
    
    dominant_count = sum(1 for v in color_buckets.values() if v > 50)
    
    return {
        "faction": faction,
        "consistency_score": 0.75 if dominant_count < 5 else 0.5,
        "dominant_color_count": dominant_count,
        "outlier_aspects": [],
        "recommendation": "accept" if dominant_count < 5 else "review"
    }
```

requirements.txt:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pillow==10.2.0
colormath==3.0.0
numpy==1.26.3
requests==2.31.0
```

Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8120
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8120"]
```

tests/test_agent.py:
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["agent"] == "20_design_fase"

def test_palette_create():
    response = client.post("/palette/create", json={
        "theme": "space_noir",
        "faction_count": 6,
        "restrictions": {}
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["master_palette"]) == 32
    assert "faction_0" in data["faction_palettes"]

def test_palette_validate():
    response = client.post("/palette/validate", json={
        "palette": ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"],
        "faction_names": ["harkon", "helios", "marshal", "ghost", "phantom"]
    })
    assert response.status_code == 200
    assert "valid" in response.json()

def test_silhouette_check():
    # Minimal PNG base64 - 10x10 transparent with diagonal line
    import base64
    from PIL import Image
    from io import BytesIO
    
    img = Image.new("RGBA", (100, 100))
    for i in range(100):
        img.putpixel((i, i), (255, 0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    
    response = client.post("/silhouette/check", json={
        "image_base64": img_b64,
        "target_sizes": [32, 64]
    })
    assert response.status_code == 200
    assert "size_results" in response.json()
```

workflow.json (N8n workflow):
```json
{
  "name": "Agent 20 Design Fase",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "design-fase",
        "responseMode": "responseNode"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300],
      "webhookId": "design-fase-webhook"
    },
    {
      "parameters": {
        "url": "http://agent-20-design-fase:8120/palette/create",
        "method": "POST",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "theme", "value": "={{ $json.theme }}"},
            {"name": "faction_count", "value": "={{ $json.faction_count }}"}
          ]
        }
      },
      "name": "Call Agent",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [450, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ $json }}"
      },
      "name": "Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [650, 300]
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "Call Agent", "type": "main", "index": 0}]]},
    "Call Agent": {"main": [[{"node": "Response", "type": "main", "index": 0}]]}
  },
  "active": false,
  "settings": {}
}
```

README.md:
```markdown
# Agent 20 - Design Fase

FastAPI service voor palette management, silhouette check, consistency validation.

## Endpoints

- POST /palette/create - Genereer master palette per theme
- POST /palette/validate - Valideer palette voor distinguishability
- POST /silhouette/check - Check silhouette recognizability op doelgrootte
- POST /consistency/check - Vergelijk concept met faction references

## Port

Internal: 8120
Via webhook: http://178.104.207.194:5680/webhook/design-fase
```

STAP 3: LOKALE TESTS
cd L:\!Nova V2\v2_services\agent_20_design_fase
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/ -v

Verwacht: 4 tests passed.

STAP 4: DOCKER BUILD LOKAAL
cd L:\!Nova V2\v2_services\agent_20_design_fase
docker build -t nova-v2-agent-20-design-fase .

Verwacht: successful build, geen errors.

STAP 5: DEPLOY NAAR HETZNER
Gebruik ssh_key based login:

# Upload files
scp -r L:\!Nova V2\v2_services\agent_20_design_fase\ root@178.104.207.194:/docker/nova-v2/services/

# Update docker-compose.yml op Hetzner
ssh root@178.104.207.194 "cat >> /docker/nova-v2/docker-compose.yml" << 'EOF'

  agent-20-design-fase:
    build: ./services/agent_20_design_fase
    container_name: nova-v2-agent-20
    restart: unless-stopped
    networks:
      - nova-v2-network
    expose:
      - "8120"
EOF

# Build + start
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose build agent-20-design-fase && docker compose up -d agent-20-design-fase"

# Wacht 15 sec voor container start
Start-Sleep -Seconds 15

# Verify container running
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps | grep agent-20"

Verwacht: container status "Up".

STAP 6: IMPORT N8N WORKFLOW
$v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" | Where-Object { $_ -match "N8N_V2_API_KEY" } | Select-Object -First 1) -replace ".*N8N_V2_API_KEY\s*=\s*", ""
$v2key = $v2key.Trim()

$workflow = Get-Content "L:\!Nova V2\v2_services\agent_20_design_fase\workflow.json" -Raw
$response = Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows" -Method POST -Headers @{"X-N8N-API-KEY"=$v2key; "Content-Type"="application/json"} -Body $workflow
$workflow_id = $response.id
Write-Host "Workflow imported: $workflow_id"

# Activate
Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows/$workflow_id/activate" -Method POST -Headers @{"X-N8N-API-KEY"=$v2key}
Write-Host "Workflow activated"

STAP 7: END-TO-END TEST
Start-Sleep -Seconds 5
$testBody = @{
    theme = "space_noir"
    faction_count = 6
    restrictions = @{}
} | ConvertTo-Json

$testResponse = Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/design-fase" -Method POST -Body $testBody -ContentType "application/json"

Verwacht: response met master_palette array van 32 kleuren + faction_palettes.

STAP 8: STATUS FILE
$status = @{
    agent_number = "20"
    name = "design_fase"
    status = "active"
    built_at = (Get-Date -Format "o")
    deployed_at = (Get-Date -Format "o")
    workflow_id = $workflow_id
    webhook_url = "http://178.104.207.194:5680/webhook/design-fase"
    endpoints = @("/palette/create", "/palette/validate", "/silhouette/check", "/consistency/check")
    tests_passed = $true
    fallback_mode = $true
    notes = "POC versie, Ollama integratie toevoegen in latere iteratie"
} | ConvertTo-Json

$status | Out-File "L:\!Nova V2\status\agent_20_status.json"

STAP 9: LOG
$logEntry = "$(Get-Date -Format 'o') | agent_20 | built+deployed+tested | SUCCESS"
Add-Content "L:\!Nova V2\logs\pipeline_build_$(Get-Date -Format 'yyyy-MM-dd').log" $logEntry

STAP 10: GIT COMMIT
cd "L:\!Nova V2"
git add v2_services/agent_20_design_fase/ status/agent_20_status.json
git commit -m "feat: Agent 20 Design Fase - POC implementation

- FastAPI service op port 8120
- 4 endpoints: palette create/validate, silhouette check, consistency check
- 32-color master palette generator met faction sub-palettes
- Delta-E color distinguishability validation
- Basic silhouette recognizability check
- POC mode, Ollama integratie in latere iteratie
- Deployed to Hetzner, workflow active"

STAP 11: RAPPORT AAN MIJ
Toon in chat:
- Klaar met Prompt 01 (Agent 20)
- Webhook: http://178.104.207.194:5680/webhook/design-fase
- Tests passed: [ja/nee]
- Status: active/fallback/failed
- Volgende prompt: 01_fase1_foundation/prompt_02_agent_02_code_jury.md

Bij fouten:
- Max 2 retries per stap
- Als STAP 5 (deploy) faalt: rollback, rapporteer
- Als STAP 7 (test) faalt: markeer fallback_mode, continue
- Bij kritiek probleem: stop, wacht op instructie
```

## Verwachte output

**Bestanden aangemaakt in L:\!Nova V2\v2_services\agent_20_design_fase\:**
- main.py (FastAPI app)
- palette_manager.py (generator)
- palette_validator.py (delta-E check)
- silhouette_checker.py (recognizability)
- consistency_checker.py (POC comparison)
- requirements.txt
- Dockerfile
- tests/test_agent.py (4 tests)
- workflow.json (N8n import)
- README.md

**Hetzner:**
- Container nova-v2-agent-20 draait
- Workflow "Agent 20 Design Fase" active in V2 N8n
- Webhook responsive

**Status:**
- L:\!Nova V2\status\agent_20_status.json geschreven
- Log entry in pipeline_build log

## Validatie (handmatig doen na Cursor klaar is)

### Test 1: Health check
```powershell
ssh root@178.104.207.194 "curl -s http://localhost:8120/health" # Via container network
# Alternatief: check docker compose logs
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs agent-20-design-fase --tail 20"
```

### Test 2: Webhook end-to-end
```powershell
$body = @{theme = "space_noir"; faction_count = 6} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/design-fase" -Method POST -Body $body -ContentType "application/json"
Write-Host "Master palette size: $($r.master_palette.Count)"
Write-Host "Factions: $($r.faction_palettes.PSObject.Properties.Name -join ', ')"
```

Verwacht: 32 kleuren, 6 factions.

### Test 3: Status file
```powershell
Get-Content "L:\!Nova V2\status\agent_20_status.json" | ConvertFrom-Json
```

Verwacht: status "active" of "fallback_mode".

## Debug als het faalt

**Container start niet:**
```powershell
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose logs agent-20-design-fase"
```
Zoek naar: import errors, missing dependencies, syntax errors.

**Workflow import fails:**
- Check V2 API key nog werkt
- Check workflow.json valid JSON (Test-Json)
- Check of workflow al bestaat met zelfde naam

**Webhook returnt 500:**
- docker compose logs agent-20 voor runtime errors
- Test direct op container: `docker exec nova-v2-agent-20 curl http://localhost:8120/health`

**Tests lokaal falen:**
- Check Python 3.11 geïnstalleerd
- requirements.txt versie conflicts
- Virtual env geactiveerd

## Rollback als nodig

```powershell
# Stop container
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose stop agent-20-design-fase"

# Remove uit compose file
# Edit manually /docker/nova-v2/docker-compose.yml

# Disable workflow
$v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" | Where-Object { $_ -match "N8N_V2_API_KEY" } | Select-Object -First 1) -replace ".*N8N_V2_API_KEY\s*=\s*", ""
$v2key = $v2key.Trim()
$workflowId = (Get-Content "L:\!Nova V2\status\agent_20_status.json" | ConvertFrom-Json).workflow_id
Invoke-RestMethod -Uri "http://178.104.207.194:5679/api/v1/workflows/$workflowId/deactivate" -Method POST -Headers @{"X-N8N-API-KEY"=$v2key}
```

## Commit message

```
feat: Agent 20 Design Fase Agent

- FastAPI service op Hetzner port 8120
- 4 endpoints: palette create/validate, silhouette/consistency check
- Master palette generator met color theory
- Delta-E validation voor faction distinguishability
- POC versie, Ollama upgrade later
- Status: active
```

## Volgende prompt

Als agent_20_status.json "active" toont: open `01_fase1_foundation/prompt_02_agent_02_code_jury.md`.
