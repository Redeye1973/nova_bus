# SESSIE 07 — Agent Bouw Batch 3: Asset Productie + Specialized (22-35)

**Doel:** 14 agents voor asset pipeline + specialized domeinen.
**Tijd:** 120-180 min (split evt over 2 Composer runs)
**Afhankelijkheden:** 06 compleet

Te bouwen (skip 20, 21 — gebouwd):
- 22 Blender Game Renderer (bridge-dependent)
- 23 Aseprite Processor (bridge-dependent)
- 24 Aseprite Animation Jury
- 25 PyQt5 Assembly (bridge-dependent)
- 26 Godot Import (bridge-dependent)
- 27 Storyboard Visual Agent
- 28 Story Text Integration
- 29 ElevenLabs Audio Agent
- 30 Audio Asset Jury
- 31 QGIS Analysis (bridge-dependent)
- 32 GRASS GIS Analysis (bridge-dependent)
- 33 Blender Architecture Walkthrough (bridge-dependent)
- 34 Unreal Engine Import
- 35 Raster 2D Processor (bridge-dependent)

---

### ===SESSION 07 START===

```
SESSIE 07 van 7 — Agent bouw batch 3 (asset productie + specialized).

14 agents. Bridge-afhankelijk: 22, 23, 25, 26, 31, 32, 33, 35.
Volledig zonder bridge: 24, 27, 28, 29, 30, 34.

## Strategie

Start met de 6 NIET-bridge-afhankelijke agents (kunnen volledig werken):
- 24 Aseprite Animation Jury (PIL + Ollama, geen bridge nodig)
- 27 Storyboard Visual Agent (FLUX API, geen bridge)
- 28 Story Text Integration (Qdrant + Ollama)
- 29 ElevenLabs Audio Agent (ElevenLabs REST API)
- 30 Audio Asset Jury (librosa)
- 34 Unreal Engine Import (FBX/USD processing)

Daarna de bridge-afhankelijke als STUBS:
- 22, 23, 25, 26, 31, 32, 33, 35

Stub = container healthy, endpoint reageert, maar geeft "pending_full_bridge"
status. Volledige implementatie wacht op bridge adapters.

## Uniform template

Zelfde als sessie 05/06.

## Agent-specifieke logic (kort)

### 24 Aseprite Animation Jury
PIL image diff per frame, Moondream op combined strip
Evalueert frame coherence, sprite sheet timing
Geen bridge nodig (PIL + Ollama via localhost)

### 27 Storyboard Visual Agent
FLUX API of SDXL lokaal (na RTX 5060 Ti)
Input: scene description, style bible
Output: storyboard panels (1920x1080)
Cost Guard integratie (rate limit)

### 28 Story Text Integration
Qdrant voor canon search
Character profiles YAML in /data
Ingest .docx via python-docx
Endpoints: /canon/search, /character/:name, /ingest

### 29 ElevenLabs Audio Agent
REST client naar api.elevenlabs.io
Character voice registry (Postgres)
Cost tracking per characters generated
Caching in MinIO (hash van text → audio file)

### 30 Audio Asset Jury
Librosa voor technische checks
Tempo consistency, key detection
Integratie met 03 (Audio Jury) voor game-specifiek

### 34 Unreal Engine Import
FBX + USD validation
Texture path rewriting
Material conversion mapping
Python (unreal.py stubs, geen echte UE nodig voor import-prep)

### 22/23/25/26/31/32/33/35 als stub
main.py template:
from fastapi import FastAPI, HTTPException
app = FastAPI(title="<Agent> (pending full bridge)")

@app.get("/health")
def health():
    return {"status": "pending_full_bridge", "mode": "stub"}

@app.post("/<operation>")
def op():
    raise HTTPException(503, "Bridge not fully wired. See session 08+.")

## Uitvoering

Phase A: 6 volledige agents (70-100 min)
Phase B: 8 stubs (20-30 min — klein werk, alleen FastAPI skelet)

Na elke 3 agents: commit + push.

## Rapport

File: docs\session_07_report.md
# Sessie 07 Rapport
- Agents attempted: 22-35 (minus 20, 21)
- Full implementations: 24, 27, 28, 29, 30, 34 (6 agents)
- Stubs (pending bridge): 22, 23, 25, 26, 31, 32, 33, 35 (8 agents)
- Active: <count>/14
- Tests: <count passed>
- Next: sessie 08 (pipelines integratie) of sessie 10 (Fase H DAZ)

## Totaalbalans na sessie 07

Aantal V2 agents actief:
- Skip-lijst (voor deze build): 5 (01, 02, 10, 20, 21)
- Sessie 05: X/7 juries
- Sessie 06: X/9 operational
- Sessie 07: X/14 asset prod

Totaal target: 35 agents, waarvan 30 in deze sessies te bouwen.
Realistisch target: 20-25 active, rest pending_bridge of failed.

git commit -m "session 07: asset production batch complete"
git push origin main

Tag deze mijlpaal:
git tag -a v2.0-core-complete -m "NOVA v2 core build compleet na sessies 01-07"
git push origin v2.0-core-complete

Print "SESSION 07 COMPLETE — V2 CORE BUILD KLAAR"

REGELS:
- Start met volledige agents (hoger waarde), dan stubs
- Stubs minimaal maar runnend
- Cost Guard blokkeert elke ElevenLabs test als budget overschreden
- Na deze sessie: Fase H (DAZ agents) en Pipelines integratie (F fase) als sessies 08/09/10

Ga.
```

### ===SESSION 07 EINDE===

---

## OUTPUT

- 14 agents: 6 volledig + 8 stubs
- Git tag `v2.0-core-complete`
- `docs/session_07_report.md`
- Totaal: 20-25 actieve agents van 35

## VERIFIEREN

```powershell
ssh root@178.104.207.194 "docker compose -f /docker/nova-v2/docker-compose.yml ps --format 'table {{.Name}}\t{{.Status}}' | Select-String healthy"
```
