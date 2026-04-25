"""NOVA v2 Agent 26 — Godot Import.

H07e: upgraded from stub to working bridge integration.
Calls BRIDGE_URL/godot/* for project validation and script execution.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_26")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://host.docker.internal:8500")
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "")
BRIDGE_TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT_S", "180"))

app = FastAPI(title="NOVA v2 Agent 26 - Godot Import", version="0.2.0")


def _bridge_headers() -> Dict[str, str]:
    h: Dict[str, str] = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


class ValidateRequest(BaseModel):
    project_dir: str = Field(..., description="Path to Godot project directory on bridge host")
    timeout_s: float = 60.0


class ImportRequest(BaseModel):
    assets: List[str] = Field(default_factory=list, description="Asset paths to import")
    asset_type: str = Field("sprite", description="sprite|model|level")
    project_dir: str = Field(..., description="Target Godot project directory")
    timeout_s: float = 120.0


class ScriptRequest(BaseModel):
    script: str = Field(..., description="Path to .gd script on bridge host")
    project_dir: Optional[str] = None
    timeout_s: float = 120.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": "26_godot_import", "version": "0.2.0",
            "bridge_url": BRIDGE_URL}


@app.get("/availability")
async def availability() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BRIDGE_URL}/health", headers=_bridge_headers(), timeout=10)
            data = r.json()
            tools = data.get("tools", {})
            return {"bridge_reachable": True, "godot": tools.get("godot", {})}
    except Exception as e:
        return {"bridge_reachable": False, "error": str(e)}


@app.post("/validate")
async def validate(req: ValidateRequest) -> Dict[str, Any]:
    payload = {"project_dir": req.project_dir, "timeout_s": req.timeout_s}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/godot/validate",
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


@app.post("/import")
async def import_assets(req: ImportRequest) -> Dict[str, Any]:
    payload = {"assets": req.assets, "type": req.asset_type, "project_dir": req.project_dir}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/godot/import",
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
async def run_script(req: ScriptRequest) -> Dict[str, Any]:
    payload = {"script": req.script, "project_dir": req.project_dir, "timeout_s": req.timeout_s}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE_URL}/godot/script",
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
    action = str(body.get("action", "validate")).lower()
    if action == "availability":
        return await availability()
    if action == "validate":
        req = ValidateRequest(
            project_dir=body.get("project_dir", ""),
            timeout_s=float(body.get("timeout_s", 60)),
        )
        return await validate(req)
    if action == "import":
        req = ImportRequest(
            assets=body.get("assets", []),
            asset_type=body.get("type", "sprite"),
            project_dir=body.get("project_dir", ""),
            timeout_s=float(body.get("timeout_s", 120)),
        )
        return await import_assets(req)
    if action == "script":
        req = ScriptRequest(
            script=body.get("script", ""),
            project_dir=body.get("project_dir"),
            timeout_s=float(body.get("timeout_s", 120)),
        )
        return await run_script(req)
    return {"error": f"unknown_action: {action}", "valid": ["validate", "import", "script", "availability"]}
