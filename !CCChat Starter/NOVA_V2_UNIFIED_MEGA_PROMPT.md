# NOVA v2 — UNIFIED MEGA BUILD PROMPT

**Versie:** 1.0 · 22 april 2026
**Doel:** één prompt, plak in Cursor Composer (Opus 4.7), werkt autonoom tot NOVA v2 compleet is
**Uitgangspunt:** V1 (68 agents, productie) bouwt V2. 5 V2-agents zijn al af en worden overgeslagen. Alle ideeën uit de brainstorm-documenten (judge, self-heal, bridge, shmup, jury-judge) zitten geïntegreerd.

---

## HOE GEBRUIKEN

1. Open Cursor in `L:\!Nova V2\`
2. Verifieer dat deze drie dingen waar zijn (anders eerst fixen):
   - Bridge draait op `http://localhost:8500/tools` (start met `python -m uvicorn app.main:app --host 0.0.0.0 --port 8500` in `L:\!Nova V2\bridge\nova_host_bridge\`)
   - **Workhorse n8n:** V1 bereikbaar: `curl http://178.104.207.194:5678` geeft response; optioneel UI-check via browser-inlog op die URL (alleen read-only gedrag handhaven)
   - V2 infra bereikbaar: `curl http://178.104.207.194:5679` geeft response (V2 main inlog: zelfde host, poort 5679)
3. Open Composer (Ctrl+I)
4. Plak alles tussen de `===PROMPT START===` en `===PROMPT EINDE===` markers
5. Enter, beantwoord 2 vragen (SSH access, secrets-pad), laat Cursor werken

Verwachte duur: 16–30 uur autonoom, in meerdere sessies. Cursor mag pauzeren voor escalaties en hervat met "resume".

---

## ===PROMPT START===

```
Je bent de autonome bouwer van NOVA v2 op een Claude Opus 4.7 backend in Cursor.
Je taak: bouw alle resterende NOVA v2 agents + hun ondersteunende lagen (judge,
self-heal, bridge, pipelines) af, zonder de al werkende productie aan te raken.
Gebruik NOVA v1 (68 agents, orchestrator) als uitvoerend werksysteem waar mogelijk.
Werk meerdere uren autonoom met minimale check-ins.

================================================================================
DEEL 1 — IDENTITEIT, CONTEXT, ABSOLUTE GRENZEN
================================================================================

### 1.1 Mijn rol

Ik ben Alex Meter uit Hoogeveen. Ik bouw NOVA: een content-productie QA engine
met jury-judge architectuur. NOVA v1 draait in productie. NOVA v2 is de nieuwe
generatie (vanaf april 2026) met jury-judge als standaard, lokaal-first AI,
multi-agent ensemble evaluatie.

### 1.2 Infrastructuur

```
Hetzner 178.104.207.194
├── :5678  V1 N8n               (68 workflows, PRODUCTIE, NIET AANRAKEN)
├── :5679  V2 N8n main          (draait, vult met agents)
├── :5680  V2 N8n webhook       (draait)
├── :19000 MinIO S3 API         (let op: afwijkende poort ivm conflict)
├── :19001 MinIO console
├── :6333  Qdrant HTTP
└── :6334  Qdrant gRPC

Lokale PC (Hoogeveen)
├── :8500  nova_host_bridge     (FastAPI, Tailscale mesh 100.64.0.2)
├── Ollama lokaal               (Codestral, llama3.2:3b; na RTX: Qwen 2.5 Coder 9B + Nemotron Nano 4B)
└── nova_poller.py              (pull model, belt Hetzner)

Tailscale mesh: PC 100.64.0.2 ↔ Hetzner 100.64.0.1 (119ms latency)
Docker compose V2 op Hetzner: /docker/nova-v2/
```

### 1.2a Workhorse: n8n (browser-inlog vs API)

De operationele **workhorse** voor server-side orchestratie is **n8n** op Hetzner — niet Cursor op zichzelf en niet alleen losse FastAPI-containers.

- **V1 productie** `http://178.104.207.194:5678` — n8n **UI-inlog** voor operators; voor deze unified build uitsluitend **read-only API** (`X-N8N-API-KEY`, workflows tellen / health), nooit muteren.
- **V2 main** `http://178.104.207.194:5679` — primaire n8n **inlog** voor V2: workflows importeren, handmatig testen, status bekijken.
- **V2 webhook** `:5680` — webhook-listener; beheer en edits horen op **:5679**.
- **Cursor / curl / scripts:** altijd **API keys** uit `L:\!Nova V2\secrets\nova_v2_passwords.txt` (`N8N_V1_API_KEY`, `N8N_V2_API_KEY`); nooit n8n UI-wachtwoorden in chat of logs.

### 1.3 Werkmap lokaal

```
L:\!Nova V2\
├── secrets\nova_v2_passwords.txt     # API keys + credentials (permissies 600)
├── bridge\nova_host_bridge\          # Bridge service
├── bridge\nova_bridge\handoff\
│   ├── to_cursor\                    # Opdrachten voor Cursor
│   ├── from_cursor\                  # Cursor responses
│   └── shared_state\                 # current_baseline.md, decisions.md, to_build.md
├── status\                           # Agent status JSON bestanden
├── pipelines\nova_v2_pipeline_build\ # 36 bestaande Cursor prompts
├── v2_services\                      # Hier komt gebouwde agent code
├── briefings\                        # V1 orchestrator input
├── logs\                             # Deploy + build logs
└── docs\                             # Finale rapporten

L:\Nova\SpaceShooter\                 # Black Ledger (Godot 4)
C:\GODOT_PROJECTS\TyrianKloon\        # TyrianKloon
L:\Nova\Key's\                        # API key backups
```

### 1.4 ABSOLUTE HARD GRENZEN — overtreden = fail hard, escaleer

1. V1 op :5678 is productie. Nooit wijzigen, nooit opnieuw deployen, nooit
   workflows muteren. Read-only toegang via API key voor delegatie, punt uit.
2. De volgende V2 agents zijn E2E verified en worden ONGEMOEID gelaten
   (controleer health, niet meer):
   - Agent 01 Sprite Jury POC   /webhook/sprite-review-poc
   - Agent 02 Code Jury         /webhook/code-review
   - Agent 10 Game Balance Jury /webhook/balance-review
   - Agent 20 Design Fase       /webhook/design-fase
   - Agent 21 FreeCAD Parametric v0.2.0  /webhook/freecad-parametric (via bridge)
3. Secrets NOOIT in code, chat, logs. Altijd uit
   `L:\!Nova V2\secrets\nova_v2_passwords.txt`. Als je ze moet gebruiken:
   env var of runtime inject, never printf.
4. Pull model: PC belt Hetzner, NOOIT andersom. Geen Cloudflare tunnel.
5. Krita CLI (`--script`) werkt niet op deze install. Altijd PyQt5 QImage/
   QPainter direct. Geen kritarunner.
6. Max 2 pogingen zelfde aanpak. Dan STOP, lees docs, zoek alternatief. Deze
   regel geldt ook op architectuurniveau: als dezelfde klasse probleem
   (netwerk/auth/bereikbaarheid) 2x opduikt, challenge het onderliggende
   ontwerp in plaats van nog een workaround te stapelen.
7. Ik (Alex) bepaal wanneer het gesprek klaar is. Nooit afsluiten met "tot
   straks", "🚂", "succes" enz.

### 1.5 Git toegang

De werkmap `L:\!Nova V2` is een git-repo met remote `origin` op
`https://github.com/Redeye1973/nova_bus.git` (**private**). Windows Credential
Manager bewaart de Personal Access Token, dus `git push` en `git pull` werken
**zonder interactieve prompts**. Huidige branch: **`main`** (trackt
`origin/main`). Gebruik git vrij voor:

- **Commits** na elke succesvolle fase (A/B/C/D/E/F/G), met duidelijke
  commitmessages (wat werkte, wat bewust niet is meegenomen).
- **Tags** op belangrijke milestones (bijv. `phase-c-judge-live`,
  `backup-YYYY-MM-DD`).
- **Branches** voor experimentele agents of risicovolle refactors; merge
  terug naar `main` pas na groene tests.
- **Herstel:** bij mislukte of gevaarlijke stap terug naar een bekende goede
  staat met `git reset --hard <tag-of-commit>` (bijv. na een milestone-tag
  of backup-tag vóór een grote deploy).

Push milestones naar `origin` zodat de private remote dezelfde staat heeft
als de lokale machine.

================================================================================
DEEL 2 — WAT ER AL GEBOUWD IS (SKIP / PRESERVE)
================================================================================

### 2.1 V1 (preserve, gebruiken als bouwmachine)

68 productie-workflows. Minimaal relevant voor ons:
- Orchestrator op /webhook/nova-orchestrator (bestaand)
- Sprites / audio / Unreal pipeline / error+rollback agents
- Bestaande code-generator en FastAPI-scaffolder agents

Deze gebruik je voor delegatie via het Delegation Format (Deel 6).

### 2.2 V2 gebouwd + verified (skippen in agent-bouw-loop)

| # | Naam | Endpoint | Actie |
|---|------|----------|-------|
| 01 | Sprite Jury POC | `/webhook/sprite-review-poc` | GET /health, laat ongemoeid |
| 02 | Code Jury | `/webhook/code-review` | GET /health, laat ongemoeid |
| 10 | Game Balance Jury | `/webhook/balance-review` | GET /health, laat ongemoeid |
| 20 | Design Fase | `/webhook/design-fase` | GET /health, laat ongemoeid |
| 21 | FreeCAD Parametric v0.2.0 | `/webhook/freecad-parametric` | GET /health, laat ongemoeid |

### 2.3 V2 stubs (29 containers healthy, logica leeg — DEZE VULLEN)

Alle andere agents uit de lijst in Deel 5. Stubs bestaan als containers maar
implementatie is leeg of placeholder. Jouw taak: code genereren, deployen,
testen, workflow importeren, status op active.

### 2.4 Bridge software op PC (geverifieerd 20 april)

GEÏNSTALLEERD:
- FreeCAD 1.0.2 — bridge actief, E2E verified
- QGIS 3.40.13 LTR — bridge actief
- Blender — adapter nog te bouwen (handoff 003)
- Aseprite — adapter nog te bouwen (handoff 003)
- Godot 4.6.2 — adapter nog te bouwen (handoff 004)
- Krita — adapter nog te bouwen (handoff 005)

NOG INSTALLEREN (voordat handoff 005):
- GIMP, Inkscape, GRASS GIS

Handoff pakketten 003-005 staan klaar in `bridge_expansion.zip` maar zijn niet
door Cursor uitgevoerd. Zie Fase B in Deel 4.

================================================================================
DEEL 3 — ARCHITECTUURPRINCIPES (onwijzigbaar tijdens deze build)
================================================================================

### 3.1 V1 = execution, V2 = intelligence

Flow voor elke taak in V2:

```
USER/TRIGGER → Planner (Agent 00, nog te bouwen)
            → Task System (Postgres task_id, status, retry_count)
            → Dispatcher
            → V1 (execution: codegen, file ops, deploy, test run)
            → V2 Jury (evaluatie per domein)
            → Critic (judge: accept|reject|review|experimental)
            → Planner loop (of klaar)
```

### 3.2 Jury-Judge patroon als standaard

Voor elk evaluatiedomein: meerdere specialisten-agents (jury) beoordelen
onafhankelijk, één judge synthesiseert. Domeinen:

- sprites (PIL + Ollama vision)
- code (AST + Codestral)
- audio (librosa + Ollama)
- 3D models (Blender inspectie + Meshy validate)
- GIS (QGIS metrics)
- CAD (FreeCAD constraints)
- narrative (Qdrant canon search + character voice)
- character art (Poser/DAZ validate + Ollama)
- 2D illustratie (GIMP/Krita/Inkscape metrics)
- game balance (numeriek + Ollama)
- aseprite animation (frame coherentie)
- audio asset integration (SFX + music)

Universele jury-archetypes die terugkomen:
1. Technische validator (deterministische checks, geen AI nodig)
2. Leesbaarheid/herkenbaarheid detector (Ollama vision)
3. Consistentie bewaker (Qdrant similarity search)
4. Context-bewuste reviewer (Ollama met domain prompt)
5. Kwaliteitsgradueel schatter (Ollama met rubric)

### 3.3 Lokaal-first AI

- Jury-leden draaien op Ollama (Qwen 2.5 VL 7B, Moondream 2, Codestral 22B,
  Llama 3.2 Vision 11B, Qwen 2.5 72B)
- RTX 5060 Ti 16GB is incoming → na installatie vervang llama3.2:3b door
  Nemotron Nano 4B, Codestral door Qwen 2.5 Coder 9B
- Claude Opus 4.7 via API = alleen escalatie (judge-deliberation tiebreaker
  of kalibratie). Budget-gated via Cost Guard agent.

### 3.4 NovaJudge laag (uit NOVA_JUDGE_MODULE)

Elke pipeline-run loopt door `judge/nova_judge.py`. Regels:

```python
# score start op 1.0, trekt af bij violations
# verdict = accept als score >= 0.75, anders reject
# errors:
#   - routing ontbreekt V1 → V2 flow → score -0.3
#   - localhost of 127.0.0.1 in logs → score -0.3 (HARD FAIL in productie)
#   - LOCAL_AGENT_OVERRIDES misuse (alleen godot_import mag override=true)
#     → score -0.2
#   - response format invalid (geen "status" key) → score -0.2
# reject genereert fix_prompt automatisch
```

### 3.5 Self-healing retry loop (uit NOVA_SELF_HEALING_PATCH)

In `core/worker.py`, reject-block:

```python
if result["judge"]["verdict"] == "reject":
    result["retry_count"] = result.get("retry_count", 0) + 1
    if result["retry_count"] > 2:
        result["status"] = "failed"; save_task(result); continue
    # apply fix (simpele mutatie-hook; later agent-specifiek maken)
    result["pipeline"][0]["input"]["variation"] = "adjusted"
    result = run_with_judge(nova, result)
```

Max 2 retries. Judge runt altijd na retry. Override-misuse blijft hard fail,
zelfs na retry. Geen architectuurwijzigingen in self-heal.

### 3.6 Judge hook opt-in (uit NOVA_RECOVERY_REPORT)

`core/judge_hook.py` wrapper. Wordt per worker opt-in aangeroepen:

```python
from core.judge_hook import run_with_judge
task = run_with_judge(NovaCore(), task)
if task["judge"]["verdict"] == "reject":
    print(task["judge"]["fix_prompt"])
```

Niet automatisch overal aanzetten — alleen waar we expliciet willen valideren.

### 3.7 Routing & network discipline

- V1 → V2 dispatcher → agent is het enige geldige pad
- LOCAL_AGENT_OVERRIDES mag alleen `godot_import` bevatten (lokaal via bridge)
- Geen localhost/127.0.0.1 in productie logs
- Alle inter-service calls via Tailscale IPs (100.64.0.0/10) of Hetzner
  interne Docker network

### 3.8 Storage & state

- PostgreSQL: task state, metrics, judge verdicts, retry counts
- Redis: queue + cache + rate limiters
- MinIO (:19000/:19001): shared artefact storage (sprites, renders, STEPs,
  audio, 3D models)
- Qdrant (:6333): vector similarity voor canon-search, style-consistency,
  duplicate detection

### 3.9 Asset Registry + Cost Guard

- Elk geproduceerd artefact krijgt entry in `nova_assets` Postgres-tabel
- Sprite-sheets MOETEN geregistreerd worden voordat import in Godot valide is
- Cost Guard (Agent 16) logt elke externe API-call (ElevenLabs, Meshy, Claude
  API) met kosten-schatting; dagbudget harde stop

================================================================================
DEEL 4 — FASE-INDELING (werk door in deze volgorde)
================================================================================

### FASE A — RECOVERY & BASELINE (max 30 min)

Doel: vaststellen wat na de stroomuitval nog draait, en wat niet.

A.1 Bridge health
```powershell
curl http://localhost:8500/tools
```
Als leeg: herstart bridge (`python -m uvicorn app.main:app --host 0.0.0.0 --port 8500`)
in `L:\!Nova V2\bridge\nova_host_bridge\`.

A.2 Hetzner containers
```bash
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps"
```
Verwacht 7+ containers healthy (postgres-v2, redis-v2, n8n-v2-main,
n8n-v2-worker-1, n8n-v2-webhook, minio-v2, qdrant-v2). Per unhealthy container:
logs lezen, 1× `docker compose restart <service>`. Nog steeds fail → escaleer.

A.3 V1 productie ping (read-only)
```bash
curl -sI http://178.104.207.194:5678
curl -H "X-N8N-API-KEY: <v1_key>" http://178.104.207.194:5678/api/v1/workflows | jq '.data | length'
```
Moet 68 of meer tonen.

A.4 V2 status baseline
```bash
curl -H "X-N8N-API-KEY: <v2_key>" http://178.104.207.194:5679/api/v1/workflows | jq '.data | length'
```
Check welke van de 5 skip-agents actief zijn, noteer in `./status/baseline.json`.

A.5 Git state + pending handoffs
```powershell
cd "L:\!Nova V2"; git log --oneline -10; git status
Get-ChildItem "L:\!Nova V2\bridge\nova_bridge\handoff\from_cursor\*.md" |
  Sort-Object LastWriteTime -Descending | Select -First 5 Name, LastWriteTime
```

A.6 Schrijf `./status/baseline.json`:
```json
{
  "timestamp": "<iso>",
  "bridge_online": true|false,
  "v1_workflows": <count>,
  "v2_workflows": <count>,
  "skip_agents_healthy": {"01": true, "02": true, "10": true, "20": true, "21": true},
  "containers": {...},
  "pending_handoffs": [...]
}
```

### FASE B — BRIDGE EXPANSION (max 90 min)

Doel: bridge adapters 003-005 live krijgen zodat alle 11 tools bereikbaar zijn
(FreeCAD/QGIS werken al).

B.1 Installeer missende software op PC
- GIMP → https://www.gimp.org/downloads/
- Inkscape → https://inkscape.org/release/
- GRASS GIS → https://grass.osgeo.org/download/

Installeer elk, daarna verifieer via CLI:
```powershell
& "C:\Program Files\GIMP 2\bin\gimp-2.10.exe" --version
& "C:\Program Files\Inkscape\bin\inkscape.exe" --version
& "C:\Program Files\GRASS GIS 8.4\grass84.bat" --version
```

B.2 Pak `bridge_expansion.zip` uit in `L:\!Nova V2\bridge\nova_host_bridge\adapters\`

B.3 Voer handoff 003 (Blender + Aseprite + PyQt5)
- Kopieer adapter-files naar `adapters/blender_adapter.py`,
  `adapters/aseprite_adapter.py`, `adapters/pyqt_sprite_adapter.py`
- Registreer in `app/main.py` → routes `/tools/blender/render`,
  `/tools/aseprite/process`, `/tools/pyqt/sprite_build`
- Bridge herstart (Ctrl+C + opnieuw starten)
- Smoke test elke endpoint:
  ```powershell
  curl -X POST http://localhost:8500/tools/blender/render -d '{"test":true}'
  curl -X POST http://localhost:8500/tools/aseprite/process -d '{"test":true}'
  curl -X POST http://localhost:8500/tools/pyqt/sprite_build -d '{"test":true}'
  ```
- Schrijf `./bridge/nova_bridge/handoff/from_cursor/003_complete.md`

B.4 Voer handoff 004 (Godot adapter)
- Adapter `adapters/godot_adapter.py` → route `/tools/godot/import`
- Godot 4.6.2 moet via `godot --headless --script` aanroepbaar zijn
- Smoke test: dummy scene open + close
- Schrijf `./bridge/nova_bridge/handoff/from_cursor/004_complete.md`

B.5 Voer handoff 005 (GRASS + GIMP + Krita + Inkscape adapters)
- `adapters/grass_adapter.py` (CLI via grass --exec)
- `adapters/gimp_adapter.py` (CLI via gimp --no-interface --batch)
- `adapters/krita_adapter.py` — NB: Krita --script werkt niet. Fallback:
  PyQt5 direct (volgens hard-grens regel 5). Registreer route als stub die
  intern naar pyqt_sprite_adapter delegeert waar mogelijk.
- `adapters/inkscape_adapter.py` (CLI via inkscape --actions)
- Smoke test + handoff-rapport

B.6 TB-001 Bridge Task Scheduler entry
Maak `L:\!Nova V2\bridge\scripts\start_bridge.bat`:
```batch
@echo off
cd /d "L:\!Nova V2\bridge\nova_host_bridge"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8500 --log-file "L:\!Nova V2\logs\bridge.log"
```
Voeg toe aan Task Scheduler:
```powershell
schtasks /Create /TN "NOVA_Bridge" /TR "L:\!Nova V2\bridge\scripts\start_bridge.bat" /SC ONSTART /RL HIGHEST /RU "$env:USERNAME"
```
Test met reboot-simulatie of stop+start van de task.

B.7 Update shared_state
```
L:\!Nova V2\bridge\nova_bridge\handoff\shared_state\current_baseline.md
```
met: 11 tools bereikbaar, alle adapters getest, TB-001 actief.

### FASE C — JUDGE + SELF-HEAL LAAG (max 2 uur)

Voordat we 29 agents bouwen, eerst de evaluatielaag deployen. Anders is alles
wat we daarna bouwen on-gevalideerd.

C.1 Schrijf / verifieer `core/nova_judge.py` volgens NOVA_JUDGE_MODULE spec
(Deel 3.4). Lokale tests:
```bash
pytest tests/test_judge.py  # 4 scenarios PASS verwacht
```

C.2 Schrijf / verifieer `core/judge_hook.py` (wrapper). Lokale tests:
```bash
pytest tests/test_judge_hook.py  # 4 scenarios PASS verwacht
```

C.3 Deploy judge-laag als Docker service `nova-v2-judge` onder
`/docker/nova-v2/services/judge/`. FastAPI endpoint op intern Docker-netwerk
(geen externe poort). Voeg toe aan `/docker/nova-v2/docker-compose.yml`.

C.4 Self-healing patch in worker
Patch `core/worker.py` met het reject-block uit Deel 3.5. Tests:
```bash
pytest tests/test_self_heal.py
# scenarios:
# - accept first try → no retry
# - reject once → retry succeeds
# - reject twice → status=failed
# - override misuse → hard fail (geen retry)
```

C.5 Integreer judge in N8n workflow template
Elke nieuw gebouwde agent-workflow MOET eindigen op:
```
[Agent logic] → [HTTP Request naar nova-v2-judge /evaluate]
             → [IF verdict==reject] → [Apply fix_prompt]
                                    → [Retry max 2x]
             → [IF accept OR retry_exhausted] → [Write result to Postgres]
```

C.6 Deploy Asset Registry
Postgres tabel `nova_assets`:
```sql
CREATE TABLE nova_assets (
  asset_id UUID PRIMARY KEY,
  asset_type TEXT NOT NULL, -- sprite|model|audio|gis|...
  path TEXT NOT NULL,
  producer_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  judge_score NUMERIC,
  judge_verdict TEXT,
  metadata JSONB
);
CREATE INDEX idx_assets_type_verdict ON nova_assets(asset_type, judge_verdict);
```

### FASE D — V1 ORCHESTRATOR BRIEFEN (max 45 min)

D.1 Bouw master briefing
`./briefings/master_build_brief.md` met: skip-lijst (5 agents), bouwlijst (30
agents), delegatie format, escalatiepaden, naar wie welke V1-agent delegeren.

D.2 Test V1 capability matrix
Stuur testtaak naar V1 orchestrator:
```bash
POST http://178.104.207.194:5678/webhook/nova-orchestrator
{
  "task_type": "capability_check",
  "requested_capabilities": [
    "python_code_generation",
    "fastapi_scaffolding",
    "pytest_generation",
    "dockerfile_build",
    "n8n_workflow_json_gen",
    "ssh_deploy_to_v2"
  ]
}
```

Per ontbrekende capability: fallback-mode voor die specifieke stap (Cursor
doet het zelf). Log in `./status/v1_capabilities.json`.

D.3 Als V1 orchestrator geen standaard `build_v2_agent` task_type ondersteunt:
maak aparte V1-workflow `nova_v2_build_orchestrator` via V1 API. Deze workflow
ontvangt Delegation Format (Deel 6) en deelt op naar bestaande V1 codegen /
scaffolder / test / deploy agents.

### FASE E — AGENT BOUW LOOP (hoofdwerk, 12-20 uur)

Voor elke agent uit de bouwlijst (Deel 5, skip de 5 gebouwde), loop:

E.x.1 Lees agent spec uit project files (bijv. `03_audio_jury.md`)
E.x.2 Delegeer naar V1 via Delegation Format (Deel 6)
E.x.3 Ontvang output, schrijf naar `./v2_services/<agent_name>/`
E.x.4 Lokale validatie
```bash
python -m py_compile v2_services/<agent>/main.py
# + ruff check, + dry-run pip install, + docker build check
```
E.x.5 Deploy naar Hetzner
```bash
scp -r v2_services/<agent>/ root@178.104.207.194:/docker/nova-v2/services/
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose up -d <agent>"
sleep 10
ssh root@178.104.207.194 "docker compose ps <agent>"
```
E.x.6 Import N8n workflow + judge-wiring (Fase C.5 template)
E.x.7 E2E test (dummy input door workflow, verwacht verdict terug)
E.x.8 Update `./status/agent_<NN>_status.json`:
```json
{
  "agent_number": "03",
  "name": "audio_jury",
  "status": "built|deployed|tested|active|failed",
  "built_at": "<iso>",
  "deployed_at": "<iso>",
  "tests_passed": true,
  "notes": "..."
}
```

Elke 5 agents: schrijf `./status/progress_milestone_N.md` met lijst active /
failed / skipped + health van judge-laag + resource-usage Hetzner.

### FASE F — PIPELINE INTEGRATIES (3-5 uur)

Na alle agents live, schakel pipelines in elkaar:

F.1 Shmup / Raptor pipeline (Black Ledger + Tyrian Kloon)
```
Design Fase (20) → FreeCAD Parametric (21) → Blender Game Renderer (22)
  → Aseprite Processor (23) → Aseprite Animation Jury (24)
  → PyQt5 Assembly (25) → Sprite Jury (01) → Godot Import (26)
```
End-to-end test: 1 dummy ship van design tot Godot scene, alle jury-verdicts
active, asset-registry rows aanwezig.

F.2 Bake pipeline (FINN / NORA / HeliosMeter grondstof)
```
PDOK Downloader (13) → QGIS Processor (15) → QGIS Analysis (31)
  → GRASS GIS Analysis (32) → Blender Baker (14) → 3D Model Jury (04)
  → GIS Jury (05) → Distribution Agent (19)
```
End-to-end test: Hoogeveen postcode 7901, binnen 4 uur compleet gebakken.

F.3 Story pipeline (Surilians)
```
Story Text Integration (28) → Narrative Jury (07)
  → Storyboard Visual Agent (27) → Character Art Jury (08)
  → 2D Illustration Jury (09)
  → [optioneel] ElevenLabs Audio (29) → Audio Asset Jury (30)
```

F.4 Bake + render architectuur walkthrough
```
GIS jury approved site → Blender Architecture Walkthrough (33)
  → [optioneel] Unreal Engine Import (34)
```

F.5 Monitor + Cost Guard + Error Agent + Prompt Director actief over alles

### FASE G — FINALE RAPPORT + HANDOFF (max 1 uur)

G.1 Schrijf `./docs/v2_build_report_<timestamp>.md`:
- X/30 agents active (target: >= 26 = 85%)
- Judge-laag uptime sinds Fase C
- Skip-agents nog gezond (5/5)
- Pipeline E2E tests: shmup, bake, story, archviz → pass/fail
- Kosten API-calls tijdens build (uit Cost Guard log)
- Known issues per failed agent
- 3 concrete next steps voor Alex

G.2 Backup configureren
- Cron op Hetzner: dagelijkse pg_dump + MinIO snapshot naar `/backup/`
- .env backup naar `L:\!Nova V2\secrets\backups\<date>\`
- Git tag `v2.0-built-<date>` in `L:\!Nova V2`

G.3 Update shared_state files
- `current_baseline.md` → nieuwe baseline
- `decisions.md` → appendix met alle architectuurbeslissingen tijdens build
- `to_build.md` → leeg of resterende known-failed agents

================================================================================
DEEL 5 — AGENT BOUWLIJST (30 te bouwen, 5 skip)
================================================================================

Volgorde is gebaseerd op dependencies. Parallel waar mogelijk (zie PARALLEL
markers).

GROEP 1 — Juries (foundation, al gedeeltelijk gebouwd)
[SKIP]  01 Sprite Jury POC
[SKIP]  02 Code Jury
 E1.    03 Audio Jury                  PARALLEL met 04
 E2.    04 3D Model Jury               PARALLEL met 03
 E3.    05 GIS Jury                    PARALLEL met 06
 E4.    06 CAD Jury                    PARALLEL met 05
 E5.    07 Narrative Jury              (na E1-E4)
 E6.    08 Character Art Jury          PARALLEL met 09
 E7.    09 2D Illustration Jury        PARALLEL met 08
[SKIP]  10 Game Balance Jury

GROEP 2 — Operationele core
 E8.    11 Monitor Agent               EERST (backbone)
 E9.    13 PDOK Downloader             PARALLEL met 14, 15
 E10.   14 Blender Baker               PARALLEL met 13, 15
 E11.   15 QGIS Processor              PARALLEL met 13, 14
 E12.   12 Bake Orchestrator           (na E9-E11)
 E13.   16 Cost Guard
 E14.   17 Error Agent                 (na 11)
 E15.   18 Prompt Director
 E16.   19 Distribution Agent

GROEP 3 — Game asset productie
[SKIP]  20 Design Fase
[SKIP]  21 FreeCAD Parametric
 E17.   22 Blender Game Renderer       (depends op 21 STEP output)
 E18.   23 Aseprite Processor          (depends op 22)
 E19.   24 Aseprite Animation Jury     (depends op 23)
 E20.   25 PyQt5 Assembly              (depends op 23, 24)
 E21.   26 Godot Import                (depends op 25)

GROEP 4 — Story
 E22.   27 Storyboard Visual Agent     (depends op 08, 09)
 E23.   28 Story Text Integration      (depends op 07)

GROEP 5 — Audio
 E24.   29 ElevenLabs Audio Agent      PARALLEL met 30
 E25.   30 Audio Asset Jury            PARALLEL met 29, depends op 03

GROEP 6 — GIS advanced
 E26.   31 QGIS Analysis               (depends op 15)
 E27.   32 GRASS GIS Analysis          PARALLEL met 31

GROEP 7 — Architectuur visualisatie
 E28.   33 Blender Architecture Walkthrough  (depends op 22, 04)
 E29.   34 Unreal Engine Import              (depends op 33)

GROEP 8 — Utility
 E30.   35 Raster 2D Processor         (GIMP/Krita/Inkscape via bridge)

================================================================================
DEEL 6 — DELEGATION FORMAT (Cursor → V1)
================================================================================

Per agent stuur je naar V1 orchestrator:

```bash
POST http://178.104.207.194:5678/webhook/nova-orchestrator
Headers:
  Content-Type: application/json
  X-N8N-API-KEY: <v1_key from secrets>
  X-Task-Source: cursor_unified_build
  X-Task-Priority: normal
```

Body:
```json
{
  "task_id": "build_agent_<NN>_<name>_<unix_ts>",
  "task_type": "build_v2_agent",
  "v2_agent": {
    "number": "<NN>",
    "name": "<snake_case_name>",
    "category": "jury_judge|operational|asset_production|story|audio|gis|archviz|utility",
    "spec_file_path": "L:/!Nova V2/specs/<NN>_<name>.md",
    "spec_content": "<full markdown spec as string>",
    "target_directory": "L:/!Nova V2/v2_services/<name>/"
  },
  "requirements": {
    "language": "python",
    "python_version": "3.11",
    "framework": "FastAPI",
    "async": true,
    "include_tests": true,
    "include_dockerfile": true,
    "include_n8n_workflow": true,
    "judge_wired": true,
    "self_heal_enabled": true
  },
  "dependencies": {
    "ollama": true,
    "postgres": true,
    "redis": false,
    "minio": true,
    "qdrant": true,
    "bridge_tools": ["blender", "freecad", ...]
  },
  "output_format": {
    "method": "return_inline",
    "structure": "folder",
    "include_readme": true
  },
  "deadline_minutes": 45,
  "escalation_contact": "cursor_build_receiver"
}
```

V1 succes-response (wacht max deadline_minutes):
```json
{
  "task_id": "...",
  "status": "completed|failed|partial",
  "output": {
    "files": [{"path":"main.py","content":"...","purpose":"..."}],
    "dockerfile": "...",
    "docker_compose_addition": "...",
    "n8n_workflow_json": {...},
    "test_suite": [...],
    "readme": "..."
  },
  "warnings": [...]
}
```

Cursor schrijft inline output naar lokale filesystem en gaat verder met
validatie (Fase E.x.4).

Als V1 `status=failed` of `capability_missing`: Cursor schakelt voor die
specifieke agent over naar FALLBACK MODE (Cursor genereert zelf code uit
agent spec `.md`, rest van pipeline ongewijzigd).

================================================================================
DEEL 7 — ERROR ESCALATION (4 LEVELS)
================================================================================

LEVEL 1 — log en doorgaan
- retry successful
- kleine spec-inconsistentie
- non-kritieke warning van V1
Actie: log, continue, noteer in final report

LEVEL 2 — pauzeer en rapporteer, ga door met andere agents
- agent faalt na 2 retries
- capability_missing voor 1 agent (fallback mode geactiveerd)
- test faalt maar agent deploy lukt
Actie: mark `needs_manual_review`, `./status/escalations.md`, skip en door

LEVEL 3 — stop en wacht
- V1 productie breekt
- Hetzner down / V2 infra down
- Secrets file corrupt of missing
- Disk space kritiek (<2GB vrij)
- V1 orchestrator niet responsive na 15 min
Actie: stop nieuwe tasks, alert Alex via console
("LEVEL 3 ESCALATION: ..."), schrijf `./status/critical_halt.md`, wacht

LEVEL 4 — emergency rollback (automatisch)
- V1 agents accidenteel aangeraakt/gemodificeerd
- V2 deploy breekt V1 connectiviteit
- Data corruption gedetecteerd
- Unauthorized credentials change
Actie: stop alles, `docker compose down` alleen V2, restore V1 .env uit backup,
CRITICAL alert naar Alex, `./status/emergency.md`, geen verdere acties

================================================================================
DEEL 8 — VERDICT CATEGORIEËN (standaard door hele pipeline)
================================================================================

Elk jury-judge resultaat = één van:

- `accept`        alle jury groen, direct productie
- `experimental`  gemengd maar interessant, → experimental bucket
- `review`        grenswaarden, menselijke check
- `reject`        onder drempel, log + fix_prompt + retry (self-heal)

Score-formules in `core/nova_judge.py` (Deel 3.4). Elk verdict wordt
geschreven naar Postgres `nova_assets.judge_verdict`.

================================================================================
DEEL 9 — CHECK-INS MET ALEX
================================================================================

Je werkt autonoom, maar pauzeert voor check-in op deze momenten:

1. Na Fase A (baseline) — vraag: "Baseline gereed, X/5 skip-agents gezond,
   door met bridge expansion?"
2. Na Fase B (bridge) — vraag: "11 tools bereikbaar via bridge, door met
   judge-laag?"
3. Na Fase C (judge) — vraag: "Judge + self-heal live, start agent-bouw?"
4. Elke 10 nieuwe agents in Fase E — korte status update
5. Bij elke LEVEL 3 of 4 escalatie — stop + alert
6. Na Fase F (pipelines) — vraag: "Pipelines draaien, schrijf finale rapport?"
7. Na Fase G (rapport) — dien rapport in

Buiten deze momenten: geen onderbrekingen tenzij LEVEL 2+ escalatie.

================================================================================
DEEL 10 — STARTSEQUENCE
================================================================================

Begin nu.

Stap 1: lees secrets-pad op
```powershell
Test-Path "L:\!Nova V2\secrets\nova_v2_passwords.txt"
```
Als False: vraag aan mij waar de secrets staan.

Stap 2: lees V1 en V2 API keys uit secrets file

Stap 3: bevestig SSH naar root@178.104.207.194 werkt:
```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 root@178.104.207.194 "echo OK"
```
Als False: vraag SSH setup (key locatie of password prompt toestaan).

Stap 4: start Fase A.

Rapporteer elke fase-afronding kort. Escaleer volgens Deel 7. Werk door tot
Fase G klaar is of je een LEVEL 3/4 event raakt.

Ga.
```

## ===PROMPT EINDE===

---

## WAT HIERMEE GEREGELD IS

- **Skip-lijst** (5 agents) expliciet en terugkerend in Deel 2, 5 en startsequence
- **V1 bouwt V2** via Delegation Format (Deel 6), V1 blijft read-only-geraakt
- **NovaJudge** (hard-fail routing + score-drempel) uit `NOVA_JUDGE_MODULE` → Deel 3.4 en Fase C
- **Self-healing** (max 2 retries, judge na retry) uit `NOVA_SELF_HEALING_PATCH` → Deel 3.5 en Fase C.4
- **Judge hook opt-in** uit `NOVA_RECOVERY_REPORT` → Deel 3.6
- **Bridge expansion** handoffs 003-005 + TB-001 Task Scheduler → Fase B
- **Jury-Judge standaard** met universele archetypes → Deel 3.2
- **Lokaal-first Ollama + RTX-upgrade plan** → Deel 3.3
- **Pull model / geen Cloudflare** → hard-grens 4
- **Krita CLI niet, PyQt5 altijd** → hard-grens 5 + Fase B.5
- **Max 2 pogingen ook architectureel** → hard-grens 6
- **Shmup / Raptor pipeline** → Fase F.1
- **Bake pipeline (FINN/NORA)** → Fase F.2
- **Story pipeline (Surilians)** → Fase F.3
- **Archviz pipeline** → Fase F.4
- **4-level error escalation** → Deel 7
- **Asset Registry + Cost Guard** → Deel 3.9
- **Geen gespreksafrondende zinnen** → hard-grens 7
- **Git: private `origin`, PAT via Credential Manager, branch `main`** → Deel 1.5

## WAT JE NOG ZELF MOET DOEN VOORDAT JE PLAKT

1. Verifieer dat `bridge_expansion.zip` daadwerkelijk bereikbaar is (bijv.
   `L:\!Nova V2\!CCChat Starter\bridge_expansion.zip` of gekopieerd naar
   `L:\!Nova V2\bridge\`) en de handoffs 003/004/005 bevat; uitpakken naar
   `L:\!Nova V2\bridge\nova_host_bridge\adapters\` volgens Fase B.2
2. Verifieer dat de 5 skip-agents inderdaad de gezonde endpoints hebben die in
   Deel 2.2 genoemd zijn (quick GET /health per stuk)
3. Controleer dat V1 orchestrator webhook bereikbaar is op
   `/webhook/nova-orchestrator` — zo niet, zoek de juiste path op in de
   V1 workflows-lijst en pas aan in Deel 6
4. Zorg dat `secrets/nova_v2_passwords.txt` zowel `N8N_V1_API_KEY` als
   `N8N_V2_API_KEY` bevat (anders vult Cursor dat eerst in)

## INDIEN CURSOR TUSSENTIJDS STOPT

Plak dit om te hervatten:

```
Resume NOVA v2 unified build. Lees laatste ./status/progress_milestone_*.md,
check baseline.json, hervat waar gestopt. Skip agents met status=active,
failed-skipped, of in skip-lijst (01/02/10/20/21). Continue volgens oorspronkelijke
prompt.
```
