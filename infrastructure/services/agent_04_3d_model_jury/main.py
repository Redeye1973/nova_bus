"""NOVA v2 Agent 04 — 3D Model Jury (metadata + uniform /review)."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from pipeline_judge import call_pipeline_judge

app = FastAPI(title="NOVA v2 3D Model Jury", version="1.0.0")
AGENT_TAG = "04_3d_model_jury"


class JuryRequest(BaseModel):
    job_id: str
    artifact: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)


class JuryVerdict(BaseModel):
    job_id: str
    verdict: str
    scores: Dict[str, Dict[str, Any]]
    judge_decision: Dict[str, Any]


def _member(score: float, issues: list[str] | None = None) -> Dict[str, Any]:
    return {"score": float(score), "issues": issues or [], "warnings": []}


def _run_sync(req: JuryRequest) -> Dict[str, Dict[str, Any]]:
    a = req.artifact
    faces = int(a.get("face_count", a.get("faces", 0)) or 0)
    verts = int(a.get("vertex_count", a.get("vertices", 0)) or 0)
    watertight = bool(a.get("is_watertight", a.get("watertight", False)))
    uv_valid = bool(a.get("uv_valid", False))
    bbox = float(a.get("bbox_max_dim", a.get("bbox_diagonal", 0.0)) or 0.0)
    visual = float(a.get("visual_score", 7.0) or 7.0)

    poly = _member(8.0 if faces > 0 and faces < 500_000 else 4.0)
    topo = _member(8.0 if watertight else 4.5)
    uv = _member(8.0 if uv_valid else 3.5)
    bbox_m = _member(8.0 if 0 < bbox < 500 else 5.0 if bbox else 4.0)
    vis = _member(min(10.0, max(0.0, visual)))
    meta = _member(7.5 if verts > 0 else 3.0)

    return {
        "polycount": poly,
        "topology": topo,
        "uv": uv,
        "bbox": bbox_m,
        "visual": vis,
        "vertices_meta": meta,
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
    return {"status": "ok", "agent": "04", "mode": "3d_model_jury_v1"}


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
    return {"agent": "04", "scores": scores, **final}
