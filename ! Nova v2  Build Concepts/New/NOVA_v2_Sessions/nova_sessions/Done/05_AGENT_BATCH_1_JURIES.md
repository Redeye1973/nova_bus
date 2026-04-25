# SESSIE 05 — Agent Bouw Batch 1: Juries (03-09)

**Doel:** 7 jury-agents bouwen, deployen, testen.
**Tijd:** 90-150 min
**Afhankelijkheden:** 01-04 compleet

Te bouwen (skip 01, 02, 10 — die zijn klaar):
- 03 Audio Jury
- 04 3D Model Jury
- 05 GIS Jury
- 06 CAD Jury
- 07 Narrative Jury
- 08 Character Art Jury
- 09 2D Illustration Jury

---

### ===SESSION 05 START===

```
SESSIE 05 van 7 — Agent bouw batch 1 (7 juries: 03, 04, 05, 06, 07, 08, 09).

Skip: 01, 02, 10 (al gebouwd).

## Strategie

Voor elk van 7 agents: uniform template. Werk parallel waar mogelijk.

Template per agent:
1. Lees spec uit project files (<NN>_<name>.md)
2. Genereer FastAPI service code
3. Schrijf tests (pytest, minstens 3 scenarios)
4. Dockerfile + requirements.txt
5. N8n workflow JSON
6. Judge-wiring in workflow (roept /evaluate aan op nova-judge)
7. Deploy naar Hetzner
8. E2E test
9. Status update

## Uniform service template

Per agent, schrijf main.py met:

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="<Agent Name>", version="1.0.0")

class JuryRequest(BaseModel):
    job_id: str
    artifact: Dict[str, Any]
    context: Dict[str, Any]

class JuryVerdict(BaseModel):
    job_id: str
    verdict: str
    scores: Dict[str, Dict[str, Any]]
    judge_decision: Dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "agent": "<name>"}

@app.post("/review", response_model=JuryVerdict)
async def review(req: JuryRequest):
    # Jury specialists run (domain-specific)
    scores = await run_jury_members(req)
    # Judge synthesis
    final = synthesize_verdict(scores)
    return JuryVerdict(
        job_id=req.job_id,
        verdict=final["verdict"],
        scores=scores,
        judge_decision=final
    )

## Jury-logic per agent

### 03 Audio Jury
Leden:
- Technical validator (librosa: sample rate, clipping, silence)
- Loudness detector (pyloudnorm: LUFS measurement)
- Spectrum analyzer (numpy FFT: frequency distribution)
- Context reviewer (Ollama Qwen 2.5 VL op spectrogram PNG)
Judge: weegt scores, accept als alle >= 6

### 04 3D Model Jury
Leden:
- Polycount validator (trimesh: faces/vertices budget)
- Topology checker (trimesh: manifold, watertight)
- UV validity (trimesh: uv bounds 0-1, overlap)
- Bounding box size sanity
- Visual: Ollama op screenshots uit 4 angles

### 05 GIS Jury
Leden:
- Projection validator (EPSG check)
- Geometry validity (shapely: valid, non-empty)
- Topology (no self-intersection, valid polygons)
- Attribute completeness
- Coverage completeness tegen baseline

### 06 CAD Jury
Leden:
- Parametric constraint health (FreeCAD API check)
- Dimensions sanity (bounding box reasonable)
- Feature tree depth (warn if > 50)
- Export compatibility (STEP + STL export test)

### 07 Narrative Jury
Leden:
- Canon adherence (Qdrant vector search tegen Surilians bible)
- Character voice (Ollama met character profile)
- World logic coherence (Ollama met worldbuilding rules)
- Narrative arc validator
- Cross-product consistency (Qdrant)

### 08 Character Art Jury
Leden:
- Pixel integrity (PIL: palette, transparency, artifacts)
- Silhouette readability (Ollama Qwen VL op silhouet)
- Expression clarity (Ollama Vision)
- Consistency versus bestaande character renders (Qdrant)
- Outfit context fit

### 09 2D Illustration Jury
Leden:
- Resolution + format (PIL basic)
- Color palette adherence (Krita-style check)
- Composition analysis (Ollama Vision)
- Style consistency (Qdrant tegen approved illustrations)
- Readability in intended context (Ollama)

## Parallelisatie

Bouw deze 7 agents niet sequentieel — batch ze.

Per agent in L:\!Nova V2\v2_services\<name>\:
- main.py
- requirements.txt
- Dockerfile
- tests\test_<name>.py
- workflow.json
- README.md

## Deployment loop

Voor elke agent:
scp -r "L:\!Nova V2\v2_services\<name>" root@178.104.207.194:/docker/nova-v2/services/

SSH update docker-compose.yml, voeg service toe met:
- name: <agent_name>
- build context: services/<name>
- expose 8000 intern
- health check
- depends_on: postgres-v2, redis-v2, nova-judge

Dan:
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose build <name> && docker compose up -d <name>"

## Judge-wiring per workflow

Elke N8n workflow moet eindigen op:

[Agent logic] → [HTTP Request naar http://nova-judge:8000/evaluate]
             → [IF verdict==reject] → [retry_count++] → [IF retry<2] → back to agent
                                    → [ELSE status=failed, save]
             → [IF accept] → [save to Postgres nova_assets]

## N8n workflow import

Per agent workflow.json:
$v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" |
  Select-String "^N8N_V2_API_KEY=").ToString().Split("=",2)[1]

Invoke-RestMethod -Method POST `
  -Uri "http://178.104.207.194:5679/api/v1/workflows" `
  -Headers @{"X-N8N-API-KEY"=$v2key; "Content-Type"="application/json"} `
  -Body (Get-Content "v2_services\<name>\workflow.json" -Raw)

Activeer workflow via API.

## Status tracking

Per agent: L:\!Nova V2\status\agent_<NN>_status.json
{
  "agent_number": "03",
  "name": "audio_jury",
  "status": "active|built|failed",
  "built_at": "<iso>",
  "deployed_at": "<iso>",
  "tests_passed": true,
  "v1_used": false,
  "fallback_used": true,
  "notes": "..."
}

## Milestone commits

Na elke 2 agents: git commit + push.

## Rapport

File: docs\session_05_report.md
# Sessie 05 Rapport
- 7 agents attempted: 03, 04, 05, 06, 07, 08, 09
- Active: <count>/7
- Failed: <lijst met reasons>
- Tests passed: <count>/7
- Total time: <minutes>
- Total commits: <count>
- Status: SUCCESS (>=5/7) / PARTIAL (3-4/7) / FAILED (<3/7)
- Next session: 06 (operational agents)

git commit -m "session 05: batch 1 juries complete (X/7 active)"
git push origin main

Print "SESSION 05 COMPLETE — X/7 agents active — next: sessie 06"

REGELS:
- V1 gebruik waar mogelijk (sneller), anders Cursor self-gen
- Max 2 retries per agent, dan mark failed + next
- Judge-wiring niet overslaan (anders zijn agents on-gevalideerd)
- Commits tussendoor zodat state nooit verloren gaat
- Als nova-judge niet bereikbaar (sessie 04 mis): STOP, escaleer

Ga.
```

### ===SESSION 05 EINDE===

---

## OUTPUT

- 7 agents (of zoveel als lukt) in `v2_services/` + deployed op Hetzner
- Status JSONs in `status/`
- Commits per batch
- `docs/session_05_report.md`

## VERIFIEREN

```powershell
ssh root@178.104.207.194 "docker compose -f /docker/nova-v2/docker-compose.yml ps"
```

Moet minimaal 5 van 7 healthy tonen voor doorgaan naar sessie 06.
