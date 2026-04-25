"""NOVA v2 Agent 51 — GIMP Processor.

Photo editing, texture processing, background generation via GIMP 3 bridge.
Uses gimp-console Script-Fu for batch operations.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_51")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://host.docker.internal:8500")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")
BRIDGE_TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT_S", "180"))

app = FastAPI(title="NOVA v2 Agent 51 - GIMP Processor", version="0.1.0")


def _bridge_headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


class ScriptFuRequest(BaseModel):
    script: str = Field(..., description="Script-Fu expression to execute")
    timeout_s: float = 120.0


class BatchProcessRequest(BaseModel):
    source: str = Field(..., description="Path to source image on bridge host")
    output_dir: str = Field(..., description="Output directory on bridge host")
    script: str = Field(..., description="Script-Fu with {source} and {output} placeholders")
    timeout_s: float = 300.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": "51_gimp_processor", "version": "0.1.0",
            "bridge_url": BRIDGE_URL}


@app.get("/availability")
async def availability() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BRIDGE_URL}/health", headers=_bridge_headers(), timeout=10)
            data = r.json()
            tools = data.get("tools", {})
            return {"bridge_reachable": True, "gimp": tools.get("gimp", {})}
    except Exception as e:
        return {"bridge_reachable": False, "error": str(e)}


@app.post("/script")
async def run_script(req: ScriptFuRequest) -> Dict[str, Any]:
    payload = {"script": req.script, "timeout_s": req.timeout_s}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/gimp/script",
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


@app.post("/batch")
async def batch_process(req: BatchProcessRequest) -> Dict[str, Any]:
    payload = {"source": req.source, "output_dir": req.output_dir,
               "script": req.script, "timeout_s": req.timeout_s}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/gimp/batch",
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
    action = str(body.get("action", "script")).lower()
    if action == "availability":
        return await availability()
    if action == "script":
        req = ScriptFuRequest(
            script=body.get("script", ""),
            timeout_s=float(body.get("timeout_s", 120)),
        )
        return await run_script(req)
    if action == "batch":
        req = BatchProcessRequest(
            source=body.get("source", ""),
            output_dir=body.get("output_dir", ""),
            script=body.get("script", ""),
            timeout_s=float(body.get("timeout_s", 300)),
        )
        return await batch_process(req)
    return {"error": f"unknown_action: {action}", "valid": ["script", "batch", "availability"]}
