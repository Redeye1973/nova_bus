"""NOVA v2 Agent 05 — GIS Jury (GeoJSON-style artifact + uniform /review)."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from pipeline_judge import call_pipeline_judge

app = FastAPI(title="NOVA v2 GIS Jury", version="1.0.0")
AGENT_TAG = "05_gis_jury"


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
    epsg = a.get("epsg") or a.get("crs_epsg")
    proj = _member(8.0 if epsg else 3.0, [] if epsg else ["missing_epsg"])

    geom = a.get("geometry") or {}
    coords = geom.get("coordinates") if isinstance(geom, dict) else None
    nonempty = bool(coords)
    geom_valid = _member(8.0 if nonempty else 2.0)

    topo = _member(8.0 if not a.get("self_intersection", False) else 3.0)
    attrs = _member(8.0 if isinstance(a.get("properties"), dict) and a["properties"] else 4.0)
    cov = float(a.get("coverage_ratio", 0.8) or 0.0)
    coverage = _member(8.0 if cov >= 0.7 else 4.0)

    return {
        "projection": proj,
        "geometry": geom_valid,
        "topology": topo,
        "attributes": attrs,
        "coverage": coverage,
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
    return {"status": "ok", "agent": "05", "mode": "gis_jury_v1"}


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
    return {"agent": "05", "scores": scores, **final}
