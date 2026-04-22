"""NOVA v2 Agent 09 — 2D Illustration Jury (image heuristics + uniform /review)."""
from __future__ import annotations

import asyncio
import base64
import io
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from pipeline_judge import call_pipeline_judge

app = FastAPI(title="NOVA v2 2D Illustration Jury", version="1.0.0")
AGENT_TAG = "09_illustration_jury"


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


def _pil_info(b64: str | None) -> tuple[int, int, int] | None:
    if not b64:
        return None
    try:
        from PIL import Image

        raw = base64.b64decode(b64, validate=False)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = im.size
        px = im.getdata()
        colors = len({p for p in px[:: max(1, len(px) // 5000)]})
        return w, h, min(colors, 9999)
    except Exception:
        return None


def _run_sync(req: JuryRequest) -> Dict[str, Dict[str, Any]]:
    a = req.artifact
    b64 = a.get("image_base64") or a.get("png_base64")
    info = _pil_info(b64) if isinstance(b64, str) else None
    if info:
        w, h, ncol = info
        res = _member(8.0 if w >= 512 and h >= 512 else 6.0)
        palette = _member(8.0 if 8 <= ncol <= 4000 else 5.0)
    else:
        w = int(a.get("width", 0) or 0)
        h = int(a.get("height", 0) or 0)
        res = _member(7.0 if w >= 256 and h >= 256 else 3.0)
        palette = _member(float(a.get("palette_adherence_score", 6.0) or 6.0))

    comp = float(a.get("composition_score", 7.0) or 7.0)
    composition = _member(min(10.0, max(0.0, comp)))

    style = float(a.get("style_consistency_score", 7.0) or 7.0)
    style_m = _member(min(10.0, max(0.0, style)))

    read = float(a.get("readability_score", 7.0) or 7.0)
    readability = _member(min(10.0, max(0.0, read)))

    return {
        "resolution": res,
        "palette": palette,
        "composition": composition,
        "style": style_m,
        "readability": readability,
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
    return {"status": "ok", "agent": "09", "mode": "illustration_jury_v1"}


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
    return {"agent": "09", "scores": scores, **final}
