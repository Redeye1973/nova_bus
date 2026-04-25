"""NOVA v2 Agent 22 — Blender Game Renderer.

H07b: upgraded from stub to working bridge integration.
Calls BRIDGE_URL/blender/* for rendering and script execution.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_22")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://host.docker.internal:8500")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")
BRIDGE_TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT_S", "360"))

app = FastAPI(title="NOVA v2 Agent 22 - Blender Game Renderer", version="0.2.0")


def _bridge_headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


class RenderRequest(BaseModel):
    source: str = Field(..., description="Path to .blend file on bridge host")
    frame: int = 1
    engine: Optional[str] = None
    timeout_s: float = 300.0


class ScriptRequest(BaseModel):
    script: str = Field(..., description="Path to .py script on bridge host")
    source: Optional[str] = None
    timeout_s: float = 300.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": "22_blender_renderer", "version": "0.2.0",
            "bridge_url": BRIDGE_URL}


@app.get("/availability")
async def availability() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BRIDGE_URL}/health", headers=_bridge_headers(), timeout=10)
            data = r.json()
            tools = data.get("tools", {})
            return {"bridge_reachable": True, "blender": tools.get("blender", {})}
    except Exception as e:
        return {"bridge_reachable": False, "error": str(e)}


@app.post("/render")
async def render(req: RenderRequest) -> Dict[str, Any]:
    payload = {"source": req.source, "frame": req.frame, "engine": req.engine, "timeout_s": req.timeout_s}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/blender/render",
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


@app.post("/script")
async def script(req: ScriptRequest) -> Dict[str, Any]:
    payload = {"script": req.script, "source": req.source, "timeout_s": req.timeout_s}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/blender/script",
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
    action = str(body.get("action", "render")).lower()
    if action == "availability":
        return await availability()
    if action == "render":
        req = RenderRequest(
            source=body.get("source", ""),
            frame=int(body.get("frame", 1)),
            engine=body.get("engine"),
            timeout_s=float(body.get("timeout_s", 300)),
        )
        return await render(req)
    if action == "script":
        req = ScriptRequest(
            script=body.get("script", ""),
            source=body.get("source"),
            timeout_s=float(body.get("timeout_s", 300)),
        )
        return await script(req)
    return {"error": f"unknown_action: {action}", "valid": ["render", "script", "availability"]}
