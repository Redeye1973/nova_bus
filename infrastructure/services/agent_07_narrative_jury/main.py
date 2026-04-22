"""NOVA v2 Agent 07 — Narrative Jury (text heuristics + uniform /review)."""
from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from pipeline_judge import call_pipeline_judge

app = FastAPI(title="NOVA v2 Narrative Jury", version="1.0.0")
AGENT_TAG = "07_narrative_jury"


class JuryRequest(BaseModel):
    job_id: str
    artifact: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)


class JuryVerdict(BaseModel):
    job_id: str
    verdict: str
    scores: Dict[str, Dict[str, Any]]
    judge_decision: Dict[str, Any]


def _member(score: float, issues: List[str] | None = None) -> Dict[str, Any]:
    return {"score": float(score), "issues": issues or [], "warnings": []}


def _run_sync(req: JuryRequest) -> Dict[str, Dict[str, Any]]:
    a = req.artifact
    text = str(a.get("text", a.get("body", "")) or "")
    wc = len(text.split())
    canon_hits = int(a.get("canon_hits", a.get("qdrant_hits", 1)) or 0)
    voice_ok = bool(a.get("voice_profile_matched", True))
    world_flags = int(a.get("world_logic_flags", 0) or 0)
    sections = len([s for s in re.split(r"\n{2,}", text) if s.strip()])
    cross = int(a.get("cross_product_hits", 1) or 0)

    canon = _member(8.0 if canon_hits > 0 and wc > 50 else 4.0)
    voice = _member(8.0 if voice_ok else 5.0)
    world = _member(8.0 if world_flags == 0 else 4.0)
    arc = _member(7.5 if sections >= 3 else 4.0)
    cross_p = _member(7.5 if cross > 0 else 4.0)

    return {
        "canon": canon,
        "character_voice": voice,
        "world_logic": world,
        "narrative_arc": arc,
        "cross_product": cross_p,
    }


async def run_jury_members(req: JuryRequest) -> Dict[str, Dict[str, Any]]:
    return await asyncio.to_thread(_run_sync, req)


def synthesize_verdict(scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    vals = [float(s.get("score", 0)) for s in scores.values()]
    avg = sum(vals) / max(len(vals), 1)
    if avg >= 7.0:
        v = "accept"
    elif avg >= 4.5:
        v = "revise"
    else:
        v = "reject"
    return {"verdict": v, "average_score": round(avg, 3)}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "07", "mode": "narrative_jury_v1"}


@app.post("/review", response_model=JuryVerdict)
async def review(req: JuryRequest) -> JuryVerdict:
    scores = await run_jury_members(req)
    final = synthesize_verdict(scores)
    task_result: Dict[str, Any] = {
        "status": "success",
        "job_id": req.job_id,
        "jury_verdict": final["verdict"],
        "average_score": final["average_score"],
    }
    pj = call_pipeline_judge(task_result, AGENT_TAG)
    jd = {**final, "pipeline_judge": pj}
    return JuryVerdict(
        job_id=req.job_id,
        verdict=str(final["verdict"]),
        scores=scores,
        judge_decision=jd,
    )


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    req = JuryRequest(job_id=str(body.get("job_id", "n8n")), artifact=body, context={})
    scores = _run_sync(req)
    final = synthesize_verdict(scores)
    return {"agent": "07", "scores": scores, **final}
