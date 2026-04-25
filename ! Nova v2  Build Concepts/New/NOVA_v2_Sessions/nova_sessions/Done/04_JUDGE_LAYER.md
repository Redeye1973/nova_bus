# SESSIE 04 — Judge + Self-Heal laag

**Doel:** Deploy NovaJudge en self-heal voordat agents gebouwd worden.
**Tijd:** 60-90 min
**Afhankelijkheden:** 01, 02, 03

Zonder deze laag zijn alle daarna gebouwde agents on-gevalideerd. Daarom FIRST.

---

### ===SESSION 04 START===

```
SESSIE 04 van 7 — Deploy Judge + Self-Heal Layer.

## Stap 1: judge module bouwen

mkdir "L:\!Nova V2\v2_services\judge"
cd "L:\!Nova V2\v2_services\judge"

File: judge\nova_judge.py
```python
import re

REQUIRED_FLOW = ["v1", "v2"]
GODOT_AGENT = "godot_import"

class NovaJudge:
    def evaluate(self, task_result: dict, logs: list) -> dict:
        errors = []
        score = 1.0

        if not self._check_routing(logs):
            errors.append("Invalid routing: must go V1 → V2 → agent")
            score -= 0.3

        if self._contains_localhost(logs):
            errors.append("Forbidden localhost usage detected")
            score -= 0.3

        if not self._check_override(logs):
            errors.append("Invalid LOCAL_AGENT_OVERRIDES usage")
            score -= 0.2

        if not self._valid_response(task_result):
            errors.append("Invalid response format")
            score -= 0.2

        score = max(0.0, round(score, 2))
        verdict = "accept" if score >= 0.75 else "reject"

        return {
            "score": score,
            "verdict": verdict,
            "errors": errors,
            "fix_prompt": self._generate_fix_prompt(errors)
        }

    def _check_routing(self, logs):
        s = " ".join(logs).lower()
        return all(x in s for x in REQUIRED_FLOW)

    def _contains_localhost(self, logs):
        s = " ".join(logs)
        return "localhost" in s or "127.0.0.1" in s

    def _check_override(self, logs):
        s = " ".join(logs).lower()
        if GODOT_AGENT in s:
            return "override=true" in s or "local" in s
        if "override=true" in s:
            return False
        return True

    def _valid_response(self, result):
        return isinstance(result, dict) and "status" in result

    def _generate_fix_prompt(self, errors):
        if not errors: return ""
        base = "Fix the NOVA pipeline issues:\n"
        for e in errors:
            if "routing" in e: base += "- Ensure flow: V1 → V2 dispatcher → agent\n"
            elif "localhost" in e: base += "- Remove ALL localhost/127.0.0.1 usage\n"
            elif "OVERRIDES" in e: base += "- Restrict LOCAL_AGENT_OVERRIDES to godot_import only\n"
            elif "response" in e: base += "- Ensure response format includes {status: ...}\n"
        base += "\nDo not modify unrelated systems."
        return base
```

## Stap 2: judge hook wrapper

File: judge\judge_hook.py
```python
from .nova_judge import NovaJudge

def execlog_tokens(log_lines):
    return [line.lower() for line in log_lines]

def run_with_judge(core, task, judge=None):
    judge = judge or NovaJudge()
    result = core.run(task)
    envelope = result if isinstance(result, dict) else {"status": "unknown"}
    tokens = execlog_tokens(result.get("logs", []))
    verdict = judge.evaluate(envelope, tokens)
    task["judge"] = verdict
    return task
```

## Stap 3: self-healing worker patch

File: judge\worker_self_heal.py
```python
from .judge_hook import run_with_judge

def worker_loop_with_self_heal(core, task):
    result = run_with_judge(core, task)

    if result.get("judge", {}).get("verdict") == "reject":
        retries = result.get("retry_count", 0) + 1
        result["retry_count"] = retries

        if retries > 2:
            result["status"] = "failed"
            return result

        # Apply fix hook (simple mutation)
        if "pipeline" in result and len(result["pipeline"]) > 0:
            result["pipeline"][0].setdefault("input", {})["variation"] = "adjusted"

        return run_with_judge(core, result)

    return result
```

## Stap 4: FastAPI service wrapper

File: main.py (in v2_services\judge\)
```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, List, Dict
from judge.nova_judge import NovaJudge

app = FastAPI(title="NOVA Judge", version="1.0.0")
judge = NovaJudge()

class EvaluateRequest(BaseModel):
    task_result: Dict[str, Any]
    logs: List[str]

@app.get("/health")
def health():
    return {"status": "ok", "service": "nova-judge"}

@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    return judge.evaluate(req.task_result, req.logs)
```

File: __init__.py in judge\ map (leeg).

File: requirements.txt:
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0

## Stap 5: tests

File: tests\test_judge.py
```python
import pytest
from judge.nova_judge import NovaJudge

j = NovaJudge()

def test_accept():
    r = j.evaluate({"status": "success"},
                   ["entrypoint=v1", "dispatch=v2", "agent=foo"])
    assert r["verdict"] == "accept"
    assert r["score"] >= 0.75

def test_reject_localhost():
    r = j.evaluate({"status": "success"},
                   ["entrypoint=v1", "dispatch=v2", "localhost:8080"])
    assert r["verdict"] == "reject"

def test_reject_routing():
    r = j.evaluate({"status": "success"}, ["random log"])
    assert r["verdict"] == "reject"

def test_reject_format():
    r = j.evaluate({"invalid": "no_status"},
                   ["entrypoint=v1", "dispatch=v2"])
    assert r["verdict"] == "reject"
```

Run: pytest tests\ -v
Alle 4 moeten PASS.

## Stap 6: Dockerfile

File: Dockerfile
```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Stap 7: deploy naar Hetzner

scp -r "L:\!Nova V2\v2_services\judge" root@178.104.207.194:/docker/nova-v2/services/

SSH + update docker-compose.yml om nova-judge service toe te voegen:

ssh root@178.104.207.194 << 'EOF'
cd /docker/nova-v2

# Voeg service toe aan compose als nog niet aanwezig
if ! grep -q "nova-judge:" docker-compose.yml; then
  cat >> docker-compose.yml << 'COMPOSE'

  nova-judge:
    build: ./services/judge
    container_name: nova-v2-judge
    restart: unless-stopped
    networks:
      - nova-v2-network
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
COMPOSE
fi

docker compose build nova-judge
docker compose up -d nova-judge
sleep 10
docker compose ps nova-judge
EOF

## Stap 8: deploy test

ssh root@178.104.207.194 "docker exec nova-v2-judge curl -s http://localhost:8000/health"

Verwacht: {"status":"ok","service":"nova-judge"}

## Stap 9: asset registry tabel in Postgres

$v2key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" |
  Select-String "^POSTGRES_PASSWORD=").ToString().Split("=",2)[1]

ssh root@178.104.207.194 "docker exec nova-v2-postgres psql -U postgres -d n8n_v2 -c \"
CREATE TABLE IF NOT EXISTS nova_assets (
  asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_type TEXT NOT NULL,
  path TEXT NOT NULL,
  producer_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  judge_score NUMERIC,
  judge_verdict TEXT,
  metadata JSONB
);
CREATE INDEX IF NOT EXISTS idx_assets_type_verdict ON nova_assets(asset_type, judge_verdict);
\""

## Stap 10: rapport

File: docs\session_04_report.md
# Sessie 04 Rapport
- Timestamp
- Judge module: gebouwd + 4/4 tests pass
- Self-heal worker: gebouwd
- Docker service nova-judge: running
- /health endpoint: responsive
- Postgres nova_assets tabel: aangemaakt
- Status: SUCCESS / PARTIAL / FAILED
- Next: sessie 05 (agent bouw batch 1)

git add v2_services/judge docs/session_04_report.md
git commit -m "session 04: judge + self-heal layer deployed"
git push origin main

Print "SESSION 04 COMPLETE — next: sessie 05 agent batch 1"

REGELS:
- Test nova-judge voordat door naar sessie 05
- Als deploy faalt: niet forceren, rapporteer en stop
- Judge moet bereikbaar zijn voor agents in sessie 05+

Ga.
```

### ===SESSION 04 EINDE===

---

## OUTPUT

- `v2_services/judge/` met werkende code + tests
- `nova-v2-judge` container draait op Hetzner
- Postgres `nova_assets` tabel
- `docs/session_04_report.md`

## VERIFIEREN

```powershell
ssh root@178.104.207.194 "docker exec nova-v2-judge curl -s http://localhost:8000/health"
Get-Content "L:\!Nova V2\docs\session_04_report.md"
```
