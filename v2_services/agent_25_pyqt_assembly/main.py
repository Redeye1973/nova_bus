"""NOVA v2 Agent 25 — PyQt Assembly.

H07d: upgraded from stub. Assembles PyQt5/6 GUI from generated components.
Uses bridge to launch Python on host with PyQt environment.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_25")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://host.docker.internal:8500")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")
BRIDGE_TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT_S", "180"))

app = FastAPI(title="NOVA v2 Agent 25 - PyQt Assembly", version="0.2.0")


def _bridge_headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


class AssembleRequest(BaseModel):
    components: List[str] = Field(default_factory=list, description="UI component file paths")
    main_window: Optional[str] = None
    output_dir: Optional[str] = None
    timeout_s: float = 120.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": "25_pyqt_assembly", "version": "0.2.0",
            "bridge_url": BRIDGE_URL}


@app.get("/availability")
async def availability() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BRIDGE_URL}/health", headers=_bridge_headers(), timeout=10)
            return {"bridge_reachable": True, "bridge_status": r.json().get("status")}
    except Exception as e:
        return {"bridge_reachable": False, "error": str(e)}


@app.post("/assemble")
async def assemble(req: AssembleRequest) -> Dict[str, Any]:
    payload = {
        "script": req.main_window or "",
        "components": req.components,
        "output_dir": req.output_dir,
        "timeout_s": req.timeout_s,
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/pyqt/assemble",
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
    action = str(body.get("action", "assemble")).lower()
    if action == "availability":
        return await availability()
    if action == "assemble":
        req = AssembleRequest(
            components=body.get("components", []),
            main_window=body.get("main_window"),
            output_dir=body.get("output_dir"),
            timeout_s=float(body.get("timeout_s", 120)),
        )
        return await assemble(req)
    return {"error": f"unknown_action: {action}", "valid": ["assemble", "availability"]}
