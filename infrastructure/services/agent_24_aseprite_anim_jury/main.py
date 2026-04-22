"""NOVA v2 Agent 24 — Aseprite Animation Jury (PIL frame coherence; optional Ollama verdict)."""
from __future__ import annotations

import base64
import io
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from PIL import Image, ImageChops, ImageStat

app = FastAPI(title="NOVA v2 Agent 24 - Aseprite Animation Jury", version="0.1.0")

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class AnimateReviewBody(BaseModel):
    """PNG frames as base64 (no data URL prefix). Minimum 2 frames for diff metrics."""

    frames_b64: List[str] = Field(..., min_length=2)
    fps_hint: Optional[float] = Field(default=None, ge=1.0, le=240.0)


def _decode_png(b64: str) -> Image.Image:
    raw = base64.b64decode(b64, validate=True)
    im = Image.open(io.BytesIO(raw))
    im.load()
    if im.mode not in ("RGB", "RGBA", "L"):
        im = im.convert("RGB")
    return im


def _coherence_metrics(frames: List[Image.Image]) -> Dict[str, Any]:
    means: List[float] = []
    ref = frames[0].convert("L")
    for nxt in frames[1:]:
        b = nxt.convert("L")
        if b.size != ref.size:
            b = b.resize(ref.size, Image.Resampling.BILINEAR)
        diff = ImageChops.difference(ref, b)
        stat = ImageStat.Stat(diff)
        means.append(float(stat.mean[0]))
        ref = nxt.convert("L")
    mx = max(means) if means else 0.0
    verdict = "pass" if mx < 40.0 else ("warn" if mx < 90.0 else "fail")
    return {
        "per_transition_mean_luma_diff": [round(m, 3) for m in means],
        "max_jump": round(mx, 3),
        "verdict": verdict,
    }


def _ollama_verdict(metrics: Dict[str, Any], fps_hint: Optional[float]) -> Optional[str]:
    if os.getenv("OLLAMA_DISABLE", "").lower() in ("1", "true", "yes"):
        return None
    prompt = (
        "You are an animation QA assistant. Given numeric frame diff metrics, "
        "reply in one short sentence: is motion coherent? "
        f"metrics={metrics!r} fps_hint={fps_hint!r}"
    )
    try:
        with httpx.Client(timeout=8.0) as c:
            r = c.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
        if r.status_code != 200:
            return None
        data = r.json()
        return str(data.get("response", "")).strip() or None
    except Exception:
        return None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "24_aseprite_anim_jury", "version": "0.1.0"}


@app.post("/animate/review")
def animate_review(body: AnimateReviewBody) -> Dict[str, Any]:
    try:
        frames = [_decode_png(x) for x in body.frames_b64]
    except Exception as exc:
        raise HTTPException(400, detail=f"invalid_frame_png: {exc}") from exc
    metrics = _coherence_metrics(frames)
    strip_w = sum(f.size[0] for f in frames)
    strip_h = max(f.size[1] for f in frames)
    ollama_note = _ollama_verdict(metrics, body.fps_hint)
    return {
        "frame_count": len(frames),
        "virtual_strip_px": {"w": strip_w, "h": strip_h},
        "metrics": metrics,
        "ollama_note": ollama_note,
    }


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    if body.get("action") == "review" and isinstance(body.get("frames_b64"), list):
        ar = AnimateReviewBody.model_validate(
            {"frames_b64": body["frames_b64"], "fps_hint": body.get("fps_hint")}
        )
        return animate_review(ar)
    return {"hint": "POST /animate/review or invoke action=review", "keys": list(body.keys())}
