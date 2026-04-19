"""
Sprite Jury POC — HTTP API for n8n integration.
Full Ollama/Qwen pipeline deferred; pixel check uses PIL; verdict is rule-based per spec.
"""
from __future__ import annotations

import io
import json
import logging
import statistics
from typing import Any

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger("sprite_jury")
logging.basicConfig(level=logging.INFO, format="%(message)s")

OLLAMA_BASE = "http://host.docker.internal:11434"

app = FastAPI(title="NOVA v2 Sprite Jury", version="0.1.0-poc")


class PixelCheckResult(BaseModel):
    score: float = Field(ge=0, le=10)
    issues: list[str]
    verdict: str  # ok | warning | broken


class VerdictRequest(BaseModel):
    pixel_integrity: float = Field(ge=0, le=10)
    jury_scores: list[float] = Field(default_factory=list)


class VerdictResponse(BaseModel):
    verdict: str
    reasoning: str


def _pixel_score_from_image(raw: bytes) -> tuple[float, list[str], str]:
    """Basic PNG/RGBA checks + rough edge noise heuristic."""
    try:
        from PIL import Image, ImageFilter
    except ImportError as e:
        raise HTTPException(500, detail=str(e)) from e

    issues: list[str] = []
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception as e:
        return 0.0, [f"decode_error:{e}"], "broken"

    if im.mode not in ("RGBA", "RGB", "P"):
        issues.append(f"mode:{im.mode}")

    if im.mode == "RGBA":
        alpha = im.split()[3]
        extrema = alpha.getextrema()
        if extrema == (255, 255):
            issues.append("opaque_alpha_suspicious")
    score = 8.0
    try:
        g = im.convert("L").filter(ImageFilter.FIND_EDGES)
        hist = g.histogram()
        edge_energy = sum(i * hist[i] for i in range(len(hist))) / (im.width * im.height + 1) / 255.0
        if edge_energy > 2.5:
            issues.append("high_edge_noise")
            score -= 2.0
    except Exception:
        pass

    if score >= 7.0 and not issues:
        verdict = "ok"
    elif score >= 5.0:
        verdict = "warning"
    else:
        verdict = "broken"
    return max(0.0, min(10.0, score)), issues, verdict


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "agent": "01_sprite_jury", "mode": "poc"}


@app.post("/v1/pixel-check", response_model=PixelCheckResult)
async def pixel_check(file: UploadFile | None = File(None)) -> PixelCheckResult:
    if file is None:
        raise HTTPException(400, detail="multipart file required")
    raw = await file.read()
    score, issues, v = _pixel_score_from_image(raw)
    return PixelCheckResult(score=score, issues=issues, verdict=v)


@app.post("/v1/verdict", response_model=VerdictResponse)
def verdict(req: VerdictRequest) -> VerdictResponse:
    """Judge rules from 01_sprite_jury.md (deterministic POC)."""
    pi = req.pixel_integrity
    scores = list(req.jury_scores)
    if pi < 5:
        return VerdictResponse(verdict="reject", reasoning="pixel_integrity < 5 (auto reject)")
    if not scores:
        return VerdictResponse(verdict="review", reasoning="no jury scores; manual review")
    mean = statistics.mean(scores)
    if all(s > 7 for s in scores):
        return VerdictResponse(verdict="accept", reasoning="all jury scores > 7")
    if mean >= 5 and len(scores) > 1:
        stdev = statistics.pstdev(scores)
        if 5 <= mean <= 7 and stdev > 1.5:
            return VerdictResponse(verdict="experimental", reasoning=f"mean={mean:.2f}, high variance")
        if 5 <= mean <= 7 and stdev <= 1.5:
            return VerdictResponse(verdict="review", reasoning=f"mean={mean:.2f}, low variance band")
    if mean < 5:
        return VerdictResponse(verdict="reject", reasoning=f"low mean={mean:.2f}")
    return VerdictResponse(verdict="review", reasoning=f"fallback mean={mean:.2f}")


@app.get("/v1/ollama-ready")
async def ollama_ready() -> dict[str, Any]:
    """Optional: check Ollama; never required for POC path."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{OLLAMA_BASE}/api/tags")
            return {"ok": r.status_code == 200}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


@app.middleware("http")
async def log_json(request, call_next):
    response = await call_next(request)
    rec = {"path": request.url.path, "method": request.method, "status": response.status_code}
    logger.info(json.dumps(rec))
    return response
