"""NOVA v2 Agent 06 — CAD Jury (parametric metadata + uniform /review)."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from pipeline_judge import call_pipeline_judge

app = FastAPI(title="NOVA v2 CAD Jury", version="1.0.0")
AGENT_TAG = "06_cad_jury"


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
    constraints_ok = bool(a.get("constraints_ok", a.get("constraints_healthy", True)))
    depth = int(a.get("feature_tree_depth", 0) or 0)
    step_ok = bool(a.get("step_export_ok", True))
    stl_ok = bool(a.get("stl_export_ok", True))
    bbox = float(a.get("bbox_diagonal_mm", 100.0) or 100.0)

    cons = _member(8.0 if constraints_ok else 3.0)
    dim = _member(8.0 if 1.0 < bbox < 5000 else 4.0)
    feat = _member(7.0 if depth < 50 else 5.0, [] if depth < 80 else ["deep_feature_tree"])
    exp = _member(8.0 if step_ok and stl_ok else 3.0, [] if step_ok else ["step_export_fail"])

    return {"constraints": cons, "dimensions": dim, "feature_tree": feat, "export": exp}


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
    return {"status": "ok", "agent": "06", "mode": "cad_jury_v1"}


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
    return {"agent": "06", "scores": scores, **final}
