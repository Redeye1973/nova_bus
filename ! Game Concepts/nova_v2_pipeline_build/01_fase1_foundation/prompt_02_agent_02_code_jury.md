# Prompt 02: Agent 02 - Code Jury

## Wat deze prompt bouwt

Code Jury voor GDScript (Godot) en Python code review. Kritiek want valideert alle toekomstige code van agents.

## Voorwaarden

- [ ] Prompt 01 (Agent 20 Design Fase) compleet
- [ ] agent_20_status.json toont "active"

## De prompt

```
Bouw Agent 02 - Code Jury voor NOVA v2.

CONTEXT:
- Spec: L:\!Nova V2\agents\nova_v2_agents\jury_judge\02_code_jury.md
- Target: L:\!Nova V2\v2_services\agent_02_code_jury\
- Webhook: http://178.104.207.194:5680/webhook/code-review
- Port: 8102
- Referentie: L:\!Nova V2\v2_services\agent_20_design_fase\ voor structuur

JURY MEMBERS (4 leden):
1. Syntax Validator (Python ast + godot-headless parse check)
2. Complexity Analyzer (cyclomatic complexity, function length)
3. Style Conformance (PEP8 voor Python, GDScript style guide)
4. Security Scanner (bandit voor Python, handmatige checks GDScript)

ENDPOINTS:
- POST /review/python - review Python code
- POST /review/gdscript - review GDScript code
- POST /review/batch - batch review multiple files
- GET /health

VOLG PROMPT TEMPLATE uit 00_master/PROMPT_TEMPLATE.md voor alle 11 stappen.

SPECIFIEKE IMPLEMENTATIE DETAILS:

main.py:
- FastAPI app op port 8102
- 3 POST endpoints voor review
- Accept code als string of base64

Per jury member een module:
- syntax_validator.py: use ast.parse() voor Python; for GDScript: write to temp file + godot --headless --check-only
- complexity_analyzer.py: use radon library voor Python complexity
- style_conformance.py: use pycodestyle voor Python
- security_scanner.py: use bandit voor Python, regex checks voor GDScript

judge.py:
- Aggregate 4 jury scores
- Verdict: accept/revise/reject
- Per verdict: specifieke feedback

requirements.txt:
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
radon==6.0.1
pycodestyle==2.11.1
bandit==1.7.6

Dockerfile: standaard, expose 8102

tests/: 
- test_python_review (valid + invalid Python code)
- test_gdscript_review (valid + invalid GDScript)
- test_security_scan (detect eval(), exec())
- test_batch_review

N8N WORKFLOW:
- Webhook trigger op /code-review
- Switch node op language (python/gdscript)
- HTTP request naar agent
- Respond naar webhook

DEPLOY + TEST conform template STAP 5-11.

STATUS FILE:
agent_02_status.json met:
- workflow_id
- webhook_url
- tests_passed
- status: active/fallback/failed

Bij klaar: rapporteer summary en volgende prompt 03 (Game Balance Jury).
```

## Verwachte output

Service met 4 jury members, 3 review endpoints, deployed en actief.

## Validatie

```powershell
# Test Python review
$pythonCode = @"
def hello():
    print('world')
"@
$body = @{language="python"; code=$pythonCode} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/code-review" -Method POST -Body $body -ContentType "application/json"

# Test GDScript review (basic)
$gdscript = @"
extends Node
func _ready():
    print("test")
"@
$body = @{language="gdscript"; code=$gdscript} | ConvertTo-Json
Invoke-RestMethod -Uri "http://178.104.207.194:5680/webhook/code-review" -Method POST -Body $body -ContentType "application/json"
```

Verwacht: verdict object met jury scores.

## Volgende prompt

`01_fase1_foundation/prompt_03_agent_10_game_balance_jury.md`
