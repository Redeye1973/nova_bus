"""NOVA Host Bridge — single multi-tool service exposing FreeCAD + QGIS
(and future Blender/GIMP/etc.) over HTTP for Hetzner agents over Tailscale.

Bind 0.0.0.0:8500 by default. Optional bearer auth via env BRIDGE_TOKEN.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import requests

from adapters import freecad as fc_adapter
from adapters import qgis as qgis_adapter
from adapters import aseprite as aseprite_adapter
from adapters import krita as krita_adapter
from adapters import blender as blender_adapter
from adapters import godot as godot_adapter
from adapters import daz as daz_adapter

logger = logging.getLogger("bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = Path(__file__).resolve().parent
CONFIG_DEFAULT_PATH = Path(os.getenv("NOVA_CONFIG_PATH", r"L:\!Nova V2\nova_config.yaml"))
WORKDIR_ROOT = Path(os.getenv("BRIDGE_WORKDIR", str(ROOT / "jobs")))
WORKDIR_ROOT.mkdir(parents=True, exist_ok=True)
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN", "").strip()

# Where the local Agent 26 (godot_import) service listens. This is a
# same-host loopback by design: NovaCore reaches this bridge on the
# Tailscale IP (100.64.0.2:8500) and the bridge forwards here, so all
# NOVA v2 files Agent 26 writes land on the machine that owns Godot.
AGENT26_LOCAL_URL = os.getenv("AGENT26_LOCAL_URL", "http://127.0.0.1:8126/invoke")
AGENT26_TIMEOUT_S = int(os.getenv("AGENT26_TIMEOUT_S", "300"))


def _load_config() -> Dict[str, Any]:
    if CONFIG_DEFAULT_PATH.is_file():
        try:
            return yaml.safe_load(CONFIG_DEFAULT_PATH.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logger.warning("failed to load nova_config.yaml: %s", e)
    return {}


CONFIG = _load_config()
HOST_TOOLS = (CONFIG.get("host_tools") or {}) if isinstance(CONFIG, dict) else {}
FREECAD_BIN  = (HOST_TOOLS.get("freecad")  or {}).get("bin") if HOST_TOOLS else None
QGIS_BIN     = (HOST_TOOLS.get("qgis")     or {}).get("bin") if HOST_TOOLS else None
ASEPRITE_BIN = (HOST_TOOLS.get("aseprite") or {}).get("bin") if HOST_TOOLS else None
KRITA_BIN    = (HOST_TOOLS.get("krita")    or {}).get("bin") if HOST_TOOLS else None
BLENDER_BIN  = (HOST_TOOLS.get("blender")  or {}).get("bin") if HOST_TOOLS else None
GODOT_BIN    = (HOST_TOOLS.get("godot")    or {}).get("bin") if HOST_TOOLS else None
DAZ_BIN      = (HOST_TOOLS.get("daz")      or {}).get("bin") if HOST_TOOLS else None


def require_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not BRIDGE_TOKEN:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, detail="missing bearer token")
    if authorization.split(None, 1)[1].strip() != BRIDGE_TOKEN:
        raise HTTPException(401, detail="invalid bearer token")


app = FastAPI(title="NOVA Host Bridge", version="0.2.0")


def _tool_yaml_configured(tool: str) -> bool:
    """Snel: staat er in nova_config een bin-pad (zonder uitvoerbaarheid te testen)."""
    entry = (HOST_TOOLS.get(tool) or {}) if HOST_TOOLS else {}
    b = entry.get("bin")
    return bool(b and str(b).strip())


@app.get("/health")
def health() -> Dict[str, Any]:
    tools_configured = {
        "freecad": _tool_yaml_configured("freecad"),
        "qgis": _tool_yaml_configured("qgis"),
        "aseprite": _tool_yaml_configured("aseprite"),
        "krita": _tool_yaml_configured("krita"),
        "blender": _tool_yaml_configured("blender"),
        "godot": _tool_yaml_configured("godot"),
        "daz": _tool_yaml_configured("daz"),
        "gimp": _tool_yaml_configured("gimp"),
    }
    n_ok = sum(1 for v in tools_configured.values() if v)
    return {
        "status": "ok",
        "service": "nova_host_bridge",
        "version": "0.2.0",
        "auth_required": bool(BRIDGE_TOKEN),
        "config_loaded": CONFIG_DEFAULT_PATH.is_file(),
        "workdir": str(WORKDIR_ROOT),
        "tools_configured": tools_configured,
        "tools_configured_count": f"{n_ok}/{len(tools_configured)}",
    }


@app.get("/tools", dependencies=[Depends(require_token)])
def tools() -> Dict[str, Any]:
    return {
        "freecad":  fc_adapter.is_available(FREECAD_BIN),
        "qgis":     qgis_adapter.is_available(QGIS_BIN),
        "aseprite": aseprite_adapter.is_available(ASEPRITE_BIN),
        "krita":    krita_adapter.is_available(KRITA_BIN),
        "blender":  blender_adapter.is_available(BLENDER_BIN),
        "godot":    godot_adapter.is_available(GODOT_BIN),
        "daz":      daz_adapter.is_available(DAZ_BIN),
    }


# ---- FreeCAD ----------------------------------------------------------------

class FreeCADBuildRequest(BaseModel):
    category: Optional[str] = None
    primitive: Optional[str] = None
    dimensions: Optional[Dict[str, float]] = None
    mount_points: Optional[Dict[str, List[float]]] = None
    exports: Optional[List[str]] = Field(default_factory=lambda: ["fcstd", "step", "stl"])
    name: Optional[str] = None
    timeout_s: Optional[float] = None


@app.post("/freecad/parametric", dependencies=[Depends(require_token)])
def freecad_parametric(req: FreeCADBuildRequest) -> Dict[str, Any]:
    try:
        spec = req.model_dump(exclude_none=True)
        result = fc_adapter.build_parametric(
            spec=spec,
            workdir_root=WORKDIR_ROOT,
            freecad_bin=FREECAD_BIN,
            timeout_s=req.timeout_s,
        )
    except fc_adapter.FreeCADUnavailable as e:
        raise HTTPException(503, detail={"reason": "freecad_unavailable", "error": str(e)})
    return result


# ---- QGIS -------------------------------------------------------------------

class QGISRunRequest(BaseModel):
    algorithm: str
    params: Dict[str, Any] = Field(default_factory=dict)
    timeout_s: Optional[float] = 300.0


@app.post("/qgis/run", dependencies=[Depends(require_token)])
def qgis_run(req: QGISRunRequest) -> Dict[str, Any]:
    try:
        return qgis_adapter.run_algorithm(
            algorithm=req.algorithm,
            params=req.params,
            workdir_root=WORKDIR_ROOT,
            qgis_bin=QGIS_BIN,
            timeout_s=req.timeout_s or 300.0,
        )
    except qgis_adapter.QGISUnavailable as e:
        raise HTTPException(503, detail={"reason": "qgis_unavailable", "error": str(e)})


@app.get("/qgis/algorithms", dependencies=[Depends(require_token)])
def qgis_algorithms(limit: int = 50) -> Dict[str, Any]:
    try:
        return qgis_adapter.list_algorithms(QGIS_BIN, limit=limit)
    except qgis_adapter.QGISUnavailable as e:
        raise HTTPException(503, detail={"reason": "qgis_unavailable", "error": str(e)})


# ---- Aseprite ---------------------------------------------------------------

class AsepriteSheetRequest(BaseModel):
    source: str
    sheet_type: Optional[str] = "horizontal"
    timeout_s: Optional[float] = None


def _aseprite_timeout_response(result: Dict[str, Any]) -> bool:
    err = str(result.get("error") or "")
    return "timeout_after_" in err and err.endswith("_killed")


@app.post("/aseprite/spritesheet", dependencies=[Depends(require_token)])
def aseprite_spritesheet(req: AsepriteSheetRequest) -> Dict[str, Any]:
    try:
        result = aseprite_adapter.export_spritesheet(
            source=req.source,
            workdir_root=WORKDIR_ROOT,
            sheet_type=req.sheet_type or "horizontal",
            aseprite_bin=ASEPRITE_BIN,
            timeout_s=req.timeout_s,
        )
        if not result.get("ok") and _aseprite_timeout_response(result):
            raise HTTPException(status_code=504, detail=result)
        return result
    except aseprite_adapter.AsepriteUnavailable as e:
        raise HTTPException(503, detail={"reason": "aseprite_unavailable", "error": str(e)})


class AsepriteBatchSaveRequest(BaseModel):
    source: str
    timeout_s: Optional[float] = None


@app.post("/aseprite/batch-save", dependencies=[Depends(require_token)])
def aseprite_batch_save(req: AsepriteBatchSaveRequest) -> Dict[str, Any]:
    try:
        result = aseprite_adapter.batch_save_as(
            source=req.source,
            workdir_root=WORKDIR_ROOT,
            aseprite_bin=ASEPRITE_BIN,
            timeout_s=req.timeout_s,
        )
        if _aseprite_timeout_response(result):
            raise HTTPException(status_code=504, detail=result)
        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result)
        return result
    except aseprite_adapter.AsepriteUnavailable as e:
        raise HTTPException(503, detail={"reason": "aseprite_unavailable", "error": str(e)})


class AsepriteLuaRequest(BaseModel):
    script: str
    source: Optional[str] = None
    timeout_s: Optional[float] = None


@app.post("/aseprite/lua", dependencies=[Depends(require_token)])
def aseprite_lua(req: AsepriteLuaRequest) -> Dict[str, Any]:
    try:
        result = aseprite_adapter.run_lua_script(
            script=req.script,
            workdir_root=WORKDIR_ROOT,
            source=req.source,
            aseprite_bin=ASEPRITE_BIN,
            timeout_s=req.timeout_s,
        )
        if _aseprite_timeout_response(result):
            raise HTTPException(status_code=504, detail=result)
        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result)
        return result
    except aseprite_adapter.AsepriteUnavailable as e:
        raise HTTPException(503, detail={"reason": "aseprite_unavailable", "error": str(e)})


# ---- Krita ------------------------------------------------------------------

class KritaExportRequest(BaseModel):
    source: str
    timeout_s: Optional[float] = 120.0


@app.post("/krita/export", dependencies=[Depends(require_token)])
def krita_export(req: KritaExportRequest) -> Dict[str, Any]:
    try:
        return krita_adapter.export_png(
            source=req.source,
            workdir_root=WORKDIR_ROOT,
            krita_bin=KRITA_BIN,
            timeout_s=req.timeout_s or 120.0,
        )
    except krita_adapter.KritaUnavailable as e:
        raise HTTPException(503, detail={"reason": "krita_unavailable", "error": str(e)})


# ---- Blender ----------------------------------------------------------------

class BlenderRenderRequest(BaseModel):
    source: str
    frame: Optional[int] = 1
    engine: Optional[str] = None
    timeout_s: Optional[float] = None


def _blender_timeout_response(result: Dict[str, Any]) -> bool:
    err = str(result.get("error") or "")
    return "timeout_after_" in err and err.endswith("_killed")


@app.post("/blender/render", dependencies=[Depends(require_token)])
def blender_render(req: BlenderRenderRequest) -> Dict[str, Any]:
    try:
        result = blender_adapter.render_frame(
            source=req.source,
            workdir_root=WORKDIR_ROOT,
            frame=req.frame or 1,
            engine=req.engine,
            blender_bin=BLENDER_BIN,
            timeout_s=req.timeout_s,
        )
        if not result.get("ok") and _blender_timeout_response(result):
            raise HTTPException(status_code=504, detail=result)
        return result
    except blender_adapter.BlenderUnavailable as e:
        raise HTTPException(503, detail={"reason": "blender_unavailable", "error": str(e)})


class BlenderScriptRequest(BaseModel):
    script: str
    source: Optional[str] = None
    timeout_s: Optional[float] = None


@app.post("/blender/script", dependencies=[Depends(require_token)])
def blender_script(req: BlenderScriptRequest) -> Dict[str, Any]:
    try:
        result = blender_adapter.run_script(
            script=req.script,
            workdir_root=WORKDIR_ROOT,
            source=req.source,
            blender_bin=BLENDER_BIN,
            timeout_s=req.timeout_s,
        )
        if not result.get("ok") and _blender_timeout_response(result):
            raise HTTPException(status_code=504, detail=result)
        return result
    except blender_adapter.BlenderUnavailable as e:
        raise HTTPException(503, detail={"reason": "blender_unavailable", "error": str(e)})


# ---- Godot ------------------------------------------------------------------

class GodotValidateRequest(BaseModel):
    project_dir: str
    timeout_s: Optional[float] = 60.0


@app.post("/godot/validate", dependencies=[Depends(require_token)])
def godot_validate(req: GodotValidateRequest) -> Dict[str, Any]:
    try:
        return godot_adapter.validate_project(
            project_dir=req.project_dir,
            workdir_root=WORKDIR_ROOT,
            godot_bin=GODOT_BIN,
            timeout_s=req.timeout_s or 60.0,
        )
    except godot_adapter.GodotUnavailable as e:
        raise HTTPException(503, detail={"reason": "godot_unavailable", "error": str(e)})


# ---- DAZ --------------------------------------------------------------------

class DazRenderRequest(BaseModel):
    script_content: str
    output_dir: str = "L:\\! 2 Nova v2  OUTPUT !\\Dazz"
    timeout_s: Optional[float] = 900.0


@app.post("/daz/render", dependencies=[Depends(require_token)])
def daz_render(req: DazRenderRequest) -> Dict[str, Any]:
    try:
        return daz_adapter.render_script(
            script_content=req.script_content,
            output_dir=req.output_dir,
            workdir_root=WORKDIR_ROOT,
            daz_bin=DAZ_BIN,
            timeout_s=req.timeout_s or 900.0,
        )
    except daz_adapter.DAZUnavailable as e:
        raise HTTPException(503, detail={"reason": "daz_unavailable", "error": str(e)})


class GodotScriptRequest(BaseModel):
    script: str
    project_dir: Optional[str] = None
    timeout_s: Optional[float] = 120.0


@app.post("/godot/script", dependencies=[Depends(require_token)])
def godot_script(req: GodotScriptRequest) -> Dict[str, Any]:
    try:
        return godot_adapter.run_script(
            script=req.script,
            workdir_root=WORKDIR_ROOT,
            project_dir=req.project_dir,
            godot_bin=GODOT_BIN,
            timeout_s=req.timeout_s or 120.0,
        )
    except godot_adapter.GodotUnavailable as e:
        raise HTTPException(503, detail={"reason": "godot_unavailable", "error": str(e)})


# ---- Godot import forwarder (Agent 26) --------------------------------------
#
# NOVA v2 architecture contract:
#
#   NovaCore  --POST-->  http://100.64.0.2:8500/godot/import  (this route)
#                         │
#                         └── forwards to Agent 26 on same host (loopback)
#                                 │
#                                 └── copies assets into res://, runs headless
#                                     Godot via /godot/script, returns report
#
# Keeping this as a thin forwarder (rather than mounting Agent 26 in the
# bridge process) means Agent 26 can be restarted / replaced without
# touching the bridge, and the bridge can enforce auth uniformly.


@app.post("/godot/import", dependencies=[Depends(require_token)])
def godot_import_forwarder(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Forward a godot_import request to the local Agent 26 service.

    Accepts either:
      - ``{"agent_id": "godot_import", "task": {...}}`` (NovaCore envelope)
      - ``{"assets": [...], "type": "sprite|model|level"}`` (flat)

    Returns Agent 26's full response unchanged. HTTP status mirrors the
    agent's result (200 on agent success, 502 on agent error so callers
    can distinguish "bridge reached agent and agent failed" from
    "bridge couldn't reach agent" (504)).
    """
    logger.info(
        "godot/import forwarder -> %s (keys=%s)",
        AGENT26_LOCAL_URL, list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__,
    )
    try:
        r = requests.post(AGENT26_LOCAL_URL, json=payload, timeout=AGENT26_TIMEOUT_S)
    except requests.Timeout as exc:
        logger.exception("agent-26 timeout")
        raise HTTPException(
            status_code=504,
            detail={"reason": "agent_26_timeout", "error": str(exc), "agent_url": AGENT26_LOCAL_URL},
        )
    except requests.RequestException as exc:
        logger.exception("agent-26 unreachable")
        raise HTTPException(
            status_code=502,
            detail={"reason": "agent_26_unreachable", "error": str(exc), "agent_url": AGENT26_LOCAL_URL},
        )

    try:
        body = r.json() if r.text else {}
    except ValueError:
        body = {"raw": r.text[:2000]}

    if not r.ok:
        # Re-raise whatever the agent returned with a bridge-marker tag.
        detail = body if isinstance(body, dict) else {"raw": body}
        detail["forwarded_status_code"] = r.status_code
        raise HTTPException(status_code=502, detail=detail)
    return body if isinstance(body, dict) else {"value": body}


# ---- File retrieval ---------------------------------------------------------

@app.get("/jobs/{job_dir_name}/files/{filename:path}", dependencies=[Depends(require_token)])
def get_file(job_dir_name: str, filename: str) -> FileResponse:
    if "/" in job_dir_name or ".." in job_dir_name:
        raise HTTPException(400, detail="invalid job dir")
    base = (WORKDIR_ROOT / job_dir_name).resolve()
    if not str(base).startswith(str(WORKDIR_ROOT.resolve())):
        raise HTTPException(400, detail="path escape")
    if not base.is_dir():
        raise HTTPException(404, detail="job_dir_not_found")
    target = (base / filename).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(400, detail="path escape")
    if not target.is_file():
        raise HTTPException(404, detail="file_not_found")
    return FileResponse(str(target), filename=target.name)


@app.delete("/jobs/{job_dir_name}", dependencies=[Depends(require_token)])
def cleanup(job_dir_name: str) -> Dict[str, Any]:
    if "/" in job_dir_name or ".." in job_dir_name:
        raise HTTPException(400, detail="invalid job dir")
    base = (WORKDIR_ROOT / job_dir_name).resolve()
    if not str(base).startswith(str(WORKDIR_ROOT.resolve())):
        raise HTTPException(400, detail="path escape")
    if not base.is_dir():
        return {"removed": False, "reason": "not_found"}
    import shutil
    shutil.rmtree(base, ignore_errors=True)
    return {"removed": True, "job_dir": str(base)}
