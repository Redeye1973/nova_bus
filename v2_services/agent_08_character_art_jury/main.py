"""NOVA v2 Agent 08 — Character Art Jury (image heuristics + uniform /review)."""
from __future__ import annotations

import asyncio
import base64
import io
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from pipeline_judge import call_pipeline_judge

app = FastAPI(title="NOVA v2 Character Art Jury", version="1.0.0")
AGENT_TAG = "08_character_art_jury"


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


def _pil_dims(b64: str | None) -> tuple[int, int] | None:
    if not b64:
        return None
    try:
        from PIL import Image

        raw = base64.b64decode(b64, validate=False)
        im = Image.open(io.BytesIO(raw))
        return im.size
    except Exception:
        return None


def _run_sync(req: JuryRequest) -> Dict[str, Dict[str, Any]]:
    a = req.artifact
    b64 = a.get("image_base64") or a.get("png_base64")
    size = _pil_dims(b64) if isinstance(b64, str) else None
    w, h = (size or (0, 0))
    pixel = _member(8.0 if w >= 64 and h >= 64 else 3.0)

    pal = int(a.get("palette_size", 32) or 32)
    palette = _member(8.0 if 4 <= pal <= 256 else 5.0)

    sil = float(a.get("silhouette_score", 7.0) or 7.0)
    silhouette = _member(min(10.0, max(0.0, sil)))

    expr = float(a.get("expression_score", 7.0) or 7.0)
    expression = _member(min(10.0, max(0.0, expr)))

    q = int(a.get("qdrant_similarity_hits", 1) or 0)
    consistency = _member(8.0 if q > 0 else 4.0)

    outfit = float(a.get("outfit_context_score", 7.0) or 7.0)
    outfit_m = _member(min(10.0, max(0.0, outfit)))

    return {
        "pixel_integrity": pixel,
        "palette": palette,
        "silhouette": silhouette,
        "expression": expression,
        "consistency": consistency,
        "outfit": outfit_m,
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
    return {"status": "ok", "agent": "08", "mode": "character_art_jury_v1"}


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
    return {"agent": "08", "scores": scores, **final}
