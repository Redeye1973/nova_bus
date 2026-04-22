"""NOVA v2 Agent 14 — Blender Baker (stub; bridge headless later)."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="NOVA v2 Agent 14 - Blender Baker", version="0.1.0-stub")

BRIDGE = os.getenv("NOVA_BRIDGE_URL", "http://host.docker.internal:8500")


class BakeBody(BaseModel):
    geojson: Optional[Dict[str, Any]] = None
    tile_id: Optional[str] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "14_blender_baker", "mode": "stub_headless"}


@app.post("/bake")
def bake(body: BakeBody) -> Dict[str, Any]:
    return {
        "status": "stub",
        "output_format": "glb",
        "tile_id": body.tile_id or "unknown",
        "bridge_url": BRIDGE,
        "note": "Full bake: invoke Blender via nova_host_bridge when scene templates are ready.",
    }


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(body, dict) and (body.get("geojson") or body.get("tile_id")):
        return bake(BakeBody.model_validate(body))
    return {"hint": "POST /bake with geojson or tile_id", "keys": list(body.keys()) if isinstance(body, dict) else []}
