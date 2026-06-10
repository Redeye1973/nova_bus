"""NOVA v2 Agent 42 — Parts Planner (brief → parts-lijst → Resume agent)."""
from __future__ import annotations

import json
import os
import re
import sys
import time

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, "/nova_shared")
sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from proof import make_and_record
except ImportError:  # pragma: no cover
    def make_and_record(*_a, **_k):  # type: ignore[misc]
        return {}

app = FastAPI(title="Parts Planner - Agent 42")

AGENT_ID = 42
PORT = int(os.getenv("PARTS_PLANNER_PORT", "8142"))
OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
RESUME_AGENT = os.getenv("RESUME_AGENT_URL", "http://127.0.0.1:8141")
MODEL = os.getenv("PARTS_PLANNER_MODEL", "qwen2.5-coder:7b")

PLANNER_SYSTEM = """Je bent een projectplanner voor de NOVA game/content pipeline.
Je ontleedt een opdracht in PARTS (logische deelprojecten) met elk concrete TAKEN.

Regels:
- 3 tot 7 parts per project, elk een duidelijk afgebakend onderdeel
- 4 tot 10 concrete taken per part, in logische uitvoervolgorde
- taak-namen kort en in snake_case (bv. enemy_spawn, music_act1, save_system)
- alle taken beginnen onafgerond (done = leeg)
- gebruik domein-kennis: een shmup heeft core/leveldesign/audio/juice/persistence;
  archviz heeft data/model/lighting/camera/export; narrative heeft outline/chapters/edit
- label per part is mensvriendelijk (bv. "SM Part 3 (audio)")

Antwoord UITSLUITEND met geldige JSON, geen uitleg, geen markdown:
{
  "parts": {
    "<part_key>": {
      "label": "<mensvriendelijk label>",
      "tasks": ["task_1","task_2", ...],
      "done": []
    }
  }
}"""


class PlanRequest(BaseModel):
    project_id: str
    project_name: str
    domain: str = "shmup"
    brief: str
    register: bool = True


@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_ID, "name": "Parts Planner", "port": PORT}


def extract_json(text: str):
    text = re.sub(r"```(json)?", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


async def register_with_resume(req: PlanRequest, parts: dict):
    async with httpx.AsyncClient(timeout=30) as c:
        try:
            await c.get(
                f"{RESUME_AGENT}/resume/{req.project_id}",
                params={"name": req.project_name, "domain": req.domain},
            )
        except Exception:
            pass
        for part_key, part in parts.items():
            tasks = part.get("tasks", [])
            for i, task in enumerate(tasks):
                payload = {
                    "project": req.project_id,
                    "part": part_key,
                    "add_task": task,
                }
                if i == 0 and part.get("label"):
                    payload["label"] = part["label"]
                await c.post(f"{RESUME_AGENT}/part-update", json=payload)


@app.post("/plan")
async def plan(req: PlanRequest):
    prompt = f"""{PLANNER_SYSTEM}

DOMEIN: {req.domain}
PROJECT: {req.project_name}
OPDRACHT:
{req.brief}

Genereer de parts-lijst als JSON."""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }

    async with httpx.AsyncClient(timeout=180) as c:
        try:
            r = await c.post(OLLAMA, json=payload)
            r.raise_for_status()
            raw = r.json().get("response", "")
        except httpx.HTTPError as exc:
            return {"error": f"ollama niet bereikbaar: {exc}", "model": MODEL}

    parts = extract_json(raw)
    if not parts or "parts" not in parts:
        return {"error": "kon geen geldige parts genereren", "raw": raw}

    result = {
        "project_id": req.project_id,
        "project_name": req.project_name,
        "domain": req.domain,
        "parts": parts["parts"],
        "part_count": len(parts["parts"]),
        "total_tasks": sum(len(p.get("tasks", [])) for p in parts["parts"].values()),
    }

    if req.register:
        await register_with_resume(req, parts["parts"])
        result["registered"] = True

    # Fase 2 bewijs-standaard: elke "klaar"-response bevat een proof-object
    result["proof"] = make_and_record(
        "job",
        id=f"plan_{req.project_id}_{int(time.time())}",
        agent="42_parts_planner",
        note=f"parts-plan {result['part_count']} parts / {result['total_tasks']} taken",
        context="parts_planner_plan",
    )
    return result
