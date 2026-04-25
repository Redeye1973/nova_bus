"""NOVA v2 Agent 32 — GRASS GIS.

H07g: upgraded from stub. Calls bridge for GRASS GIS operations.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_32")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://host.docker.internal:8500")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")
BRIDGE_TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT_S", "180"))

app = FastAPI(title="NOVA v2 Agent 32 - GRASS GIS", version="0.2.0")


def _bridge_headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


class GrassRequest(BaseModel):
    script: str = Field(..., description="GRASS Python script path on bridge host")
    location: Optional[str] = None
    mapset: Optional[str] = None
    timeout_s: float = 120.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": "32_grass_gis", "version": "0.2.0",
            "bridge_url": BRIDGE_URL}


@app.get("/availability")
async def availability() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BRIDGE_URL}/health", headers=_bridge_headers(), timeout=10)
            return {"bridge_reachable": True, "bridge_status": r.json().get("status")}
    except Exception as e:
        return {"bridge_reachable": False, "error": str(e)}


@app.post("/analyze")
async def analyze(req: GrassRequest) -> Dict[str, Any]:
    payload = {"script": req.script, "location": req.location,
               "mapset": req.mapset, "timeout_s": req.timeout_s}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/grass/script",
                json=payload,
                headers=_bridge_headers(),
                timeout=BRIDGE_TIMEOUT,
            )
            if r.status_code >= 500:
                raise HTTPException(502, detail=f"bridge returned {r.status_code}")
            return r.json()
    except httpx.TimeoutException:
        raise HTTPException(504, detail="bridge timeout")
    except httpx.ConnectError:
        raise HTTPException(503, detail="bridge unreachable")


@app.post("/invoke")
async def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    action = str(body.get("action", "analyze")).lower()
    if action == "availability":
        return await availability()
    if action == "analyze":
        req = GrassRequest(
            script=body.get("script", ""),
            location=body.get("location"),
            mapset=body.get("mapset"),
            timeout_s=float(body.get("timeout_s", 120)),
        )
        return await analyze(req)
    return {"error": f"unknown_action: {action}", "valid": ["analyze", "availability"]}
