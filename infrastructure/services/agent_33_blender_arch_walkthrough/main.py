"""NOVA v2 Agent 33 — Blender Architecture Walkthrough.

H07h: upgraded from stub. Calls bridge Blender adapter for arch walkthroughs.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_33")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://host.docker.internal:8500")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")
BRIDGE_TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT_S", "360"))

app = FastAPI(title="NOVA v2 Agent 33 - Blender Arch Walkthrough", version="0.2.0")


def _bridge_headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


class WalkthroughRequest(BaseModel):
    source: str = Field(..., description="Path to .blend architecture file on bridge host")
    frames: List[int] = Field(default_factory=lambda: [1], description="Frame numbers to render")
    engine: str = "BLENDER_EEVEE"
    timeout_s: float = 300.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": "33_blender_arch_walkthrough", "version": "0.2.0",
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


@app.post("/walkthrough")
async def walkthrough(req: WalkthroughRequest) -> Dict[str, Any]:
    results = []
    for frame in req.frames:
        payload = {"source": req.source, "frame": frame, "engine": req.engine,
                   "timeout_s": req.timeout_s}
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{BRIDGE_URL}/blender/render",
                    json=payload,
                    headers=_bridge_headers(),
                    timeout=BRIDGE_TIMEOUT,
                )
                if r.status_code >= 500:
                    results.append({"frame": frame, "ok": False, "error": f"bridge {r.status_code}"})
                else:
                    results.append({"frame": frame, **r.json()})
        except httpx.TimeoutException:
            results.append({"frame": frame, "ok": False, "error": "timeout"})
        except httpx.ConnectError:
            results.append({"frame": frame, "ok": False, "error": "bridge unreachable"})
            break
    return {"frames_requested": len(req.frames), "results": results,
            "ok": all(r.get("ok") for r in results)}


@app.post("/invoke")
async def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    action = str(body.get("action", "walkthrough")).lower()
    if action == "availability":
        return await availability()
    if action == "walkthrough":
        req = WalkthroughRequest(
            source=body.get("source", ""),
            frames=body.get("frames", [1]),
            engine=body.get("engine", "BLENDER_EEVEE"),
            timeout_s=float(body.get("timeout_s", 300)),
        )
        return await walkthrough(req)
    return {"error": f"unknown_action: {action}", "valid": ["walkthrough", "availability"]}
