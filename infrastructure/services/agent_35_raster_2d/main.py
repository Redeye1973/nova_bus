"""NOVA v2 Agent 35 — Raster 2D Processor.

H07c: upgraded from stub. Processes 2D raster outputs from Blender/Aseprite.
Uses bridge for Blender script execution for batch 2D operations.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_35")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://host.docker.internal:8500")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")
BRIDGE_TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT_S", "180"))

app = FastAPI(title="NOVA v2 Agent 35 - Raster 2D Processor", version="0.2.0")


def _bridge_headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


class ProcessRequest(BaseModel):
    source: str = Field(..., description="Path to source image/blend on bridge host")
    operation: str = Field("render", description="render|resize|composite")
    output_format: str = "png"
    timeout_s: float = 120.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": "35_raster_2d", "version": "0.2.0",
            "bridge_url": BRIDGE_URL}


@app.get("/availability")
async def availability() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BRIDGE_URL}/health", headers=_bridge_headers(), timeout=10)
            data = r.json()
            tools = data.get("tools", {})
            return {"bridge_reachable": True, "blender": tools.get("blender", {}),
                    "aseprite": tools.get("aseprite", {})}
    except Exception as e:
        return {"bridge_reachable": False, "error": str(e)}


@app.post("/process")
async def process(req: ProcessRequest) -> Dict[str, Any]:
    if req.operation == "render":
        payload = {"source": req.source, "frame": 1, "timeout_s": req.timeout_s}
        endpoint = f"{BRIDGE_URL}/blender/render"
    else:
        payload = {"source": req.source, "timeout_s": req.timeout_s}
        endpoint = f"{BRIDGE_URL}/blender/script"

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                endpoint, json=payload,
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
    action = str(body.get("action", "process")).lower()
    if action == "availability":
        return await availability()
    if action == "process":
        req = ProcessRequest(
            source=body.get("source", ""),
            operation=body.get("operation", "render"),
            output_format=body.get("output_format", "png"),
            timeout_s=float(body.get("timeout_s", 120)),
        )
        return await process(req)
    return {"error": f"unknown_action: {action}", "valid": ["process", "availability"]}
