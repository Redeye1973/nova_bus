"""NOVA v2 Agent 27 — Storyboard Visual Agent (Cost Guard precheck; FLUX optional)."""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 27 - Storyboard Visual", version="0.1.0")

COST_GUARD_URL = os.getenv("COST_GUARD_URL", "").rstrip("/")
FLUX_API_URL = os.getenv("FLUX_API_URL", "").rstrip("/")
FLUX_API_KEY = os.getenv("FLUX_API_KEY", "")
# rough EUR estimate per panel for budget pre-check
ESTIMATE_EUR_PER_PANEL = float(os.getenv("STORYBOARD_EUR_PER_PANEL", "0.02"))


def _cost_precheck(estimated_eur: float) -> None:
    if not COST_GUARD_URL:
        return
    try:
        with httpx.Client(timeout=3.0) as c:
            r = c.post(
                f"{COST_GUARD_URL}/cost/check",
                json={"estimated_cost_eur": estimated_eur},
            )
        if r.status_code == 429:
            raise HTTPException(status_code=429, detail=r.json())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, detail=f"cost_guard_unreachable:{exc}") from exc


class StoryboardBody(BaseModel):
    scene_description: str = Field(..., min_length=4)
    style_bible: Optional[str] = None
    panel_count: int = Field(default=3, ge=1, le=12)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "27_storyboard", "version": "0.1.0"}


@app.post("/storyboard/generate")
def storyboard_generate(body: StoryboardBody) -> Dict[str, Any]:
    est = ESTIMATE_EUR_PER_PANEL * body.panel_count
    _cost_precheck(est)
    job_id = str(uuid.uuid4())
    panels: List[Dict[str, Any]] = []
    for i in range(body.panel_count):
        panels.append(
            {
                "panel_index": i + 1,
                "prompt": f"{body.scene_description} | panel {i + 1}/{body.panel_count}"
                + (f" | style: {body.style_bible}" if body.style_bible else ""),
                "resolution": [1920, 1080],
                "image_url": None,
            }
        )
    out: Dict[str, Any] = {
        "job_id": job_id,
        "status": "planned",
        "panels": panels,
        "estimated_cost_eur": round(est, 4),
        "created_at": time.time(),
    }
    if FLUX_API_URL and FLUX_API_KEY:
        out["status"] = "queued_external"
        out["flux_endpoint"] = FLUX_API_URL
    else:
        out["status"] = "dry_run_no_flux_credentials"
    return out


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    if body.get("action") == "generate":
        return storyboard_generate(StoryboardBody.model_validate(body.get("payload", body)))
    return {"hint": "POST /storyboard/generate", "keys": list(body.keys())}
