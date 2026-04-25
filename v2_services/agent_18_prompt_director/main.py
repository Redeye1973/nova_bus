"""NOVA v2 Agent 18 — Prompt Director (versioned templates + prompt registry).

Extended with H13 prompt registry: run tracking, success rates, leaderboard.
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 18 - Prompt Director", version="0.2.0")

TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "build_v2_agent": [
        {
            "version": 1,
            "approved": True,
            "body": "You are NOVA. Implement the agent spec as FastAPI + Dockerfile + tests.",
        },
        {
            "version": 2,
            "approved": True,
            "body": "You are NOVA. Implement the agent spec; include self-heal hooks and judge wiring.",
        },
    ],
    "jury_review": [
        {"version": 1, "approved": True, "body": "Score the artifact using the rubric; return JSON verdict."},
    ],
}

PROMPT_RUNS: Deque[Dict[str, Any]] = deque(maxlen=10_000)
PROMPT_STATS: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0})


class TemplateUpsert(BaseModel):
    name: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    approved: bool = False
    tags: Optional[List[str]] = None
    model_target: Optional[str] = None
    agent_target: Optional[str] = None


class PromptFeedback(BaseModel):
    prompt_name: str = Field(..., min_length=1)
    version: Optional[int] = None
    rendered_prompt: Optional[str] = None
    success: bool = True
    judge_verdict: Optional[str] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "18_prompt_director", "version": "0.2.0"}


@app.get("/templates/{name}")
def get_template(name: str, version: Optional[int] = None) -> Dict[str, Any]:
    versions = TEMPLATES.get(name)
    if not versions:
        raise HTTPException(404, detail=f"unknown_template:{name}")
    if version is None:
        approved = [v for v in versions if v.get("approved")]
        pick = approved[-1] if approved else versions[-1]
        stats = PROMPT_STATS.get(name, {})
        runs = stats.get("runs", 0)
        success_rate = stats.get("successes", 0) / max(runs, 1)
        return {"name": name, "latest": pick, "all_versions": len(versions),
                "runs": runs, "success_rate": round(success_rate, 3)}
    for v in versions:
        if int(v.get("version", 0)) == int(version):
            return {"name": name, "template": v}
    raise HTTPException(404, detail=f"unknown_version:{version}")


@app.post("/templates")
def upsert_template(body: TemplateUpsert) -> Dict[str, Any]:
    lst = TEMPLATES.setdefault(body.name, [])
    nv = max((int(x.get("version", 0)) for x in lst), default=0) + 1
    rec = {
        "version": nv, "approved": body.approved, "body": body.body,
        "tags": body.tags or [], "model_target": body.model_target,
        "agent_target": body.agent_target, "created_at": time.time(),
    }
    lst.append(rec)
    return {"name": body.name, "version": nv, "approved": body.approved}


@app.get("/templates")
def list_templates() -> Dict[str, Any]:
    result = []
    for name, versions in sorted(TEMPLATES.items()):
        latest = versions[-1] if versions else {}
        stats = PROMPT_STATS.get(name, {})
        runs = stats.get("runs", 0)
        result.append({
            "name": name,
            "versions": len(versions),
            "latest_version": latest.get("version"),
            "approved": latest.get("approved", False),
            "tags": latest.get("tags", []),
            "runs": runs,
            "success_rate": round(stats.get("successes", 0) / max(runs, 1), 3),
        })
    return {"count": len(result), "templates": result}


@app.get("/prompts/search")
def search_prompts(q: str = "", tag: Optional[str] = None) -> Dict[str, Any]:
    results = []
    for name, versions in TEMPLATES.items():
        latest = versions[-1] if versions else {}
        if q and q.lower() not in name.lower() and q.lower() not in latest.get("body", "").lower():
            continue
        if tag and tag not in latest.get("tags", []):
            continue
        results.append({"name": name, "versions": len(versions), "body_preview": latest.get("body", "")[:100]})
    return {"count": len(results), "results": results}


@app.post("/prompts/feedback")
def prompt_feedback(body: PromptFeedback) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    run = {
        "run_id": run_id,
        "prompt_name": body.prompt_name,
        "version": body.version,
        "success": body.success,
        "judge_verdict": body.judge_verdict,
        "latency_ms": body.latency_ms,
        "cost_usd": body.cost_usd,
        "ts": time.time(),
        "metadata": body.metadata or {},
    }
    PROMPT_RUNS.append(run)

    stats = PROMPT_STATS[body.prompt_name]
    stats["runs"] += 1
    if body.success:
        stats["successes"] += 1
    if body.latency_ms:
        stats["total_latency_ms"] += body.latency_ms
    return {"recorded": True, "run_id": run_id}


@app.get("/prompts/leaderboard")
def prompt_leaderboard(limit: int = 10) -> Dict[str, Any]:
    ranked = []
    for name, stats in PROMPT_STATS.items():
        runs = stats.get("runs", 0)
        if runs == 0:
            continue
        ranked.append({
            "name": name,
            "runs": runs,
            "success_rate": round(stats["successes"] / runs, 3),
            "avg_latency_ms": round(stats["total_latency_ms"] / runs) if runs else 0,
        })
    ranked.sort(key=lambda x: (-x["success_rate"], -x["runs"]))
    return {"leaderboard": ranked[:limit]}


@app.get("/prompts/recent")
def prompt_recent(limit: int = 20) -> Dict[str, Any]:
    items = list(PROMPT_RUNS)[-min(limit, 200):]
    return {"count": len(items), "runs": items}


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    action = str(body.get("action", "")).lower()
    if action == "get":
        return get_template(str(body.get("name", "")), body.get("version"))
    if action == "list":
        return list_templates()
    if action == "search":
        return search_prompts(str(body.get("q", "")), body.get("tag"))
    if action == "leaderboard":
        return prompt_leaderboard(int(body.get("limit", 10)))
    return {"hint": "actions: get, list, search, leaderboard", "keys": list(body.keys())}
