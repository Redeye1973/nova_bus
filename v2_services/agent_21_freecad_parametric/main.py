"""NOVA v2 Agent 21 — FreeCAD Parametric.

Two backends:

1. **bridge** — when HOST_BRIDGE_URL env var is set, parametric work is
   routed to the NOVA Host Bridge (real FreeCAD on the developer PC,
   reachable over Tailscale). Produces STEP + STL + FCStd. This is the
   preferred path.
2. **trimesh** — local fallback when the bridge is unreachable. Produces
   STL + GLB only and uses trimesh primitives. Same response shape so
   downstream consumers don't care about backend.

Endpoints:
- GET  /health
- POST /model/build-base       {category, dimensions, mount_points_config?}
- POST /variants/generate      {base_model, parameter_matrix, count?}
- POST /components/assemble    {components: [{base, mount?}], output_name?}
- POST /invoke                 {action: build_base|generate|assemble|info, payload}
"""
from __future__ import annotations

import itertools
import json
import logging
import os
import time
import uuid
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
import trimesh
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("freecad_parametric")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

OUTPUT_DIR = Path(os.getenv("FREECAD_OUTPUT_DIR", "/tmp/freecad_parametric"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HOST_BRIDGE_URL = (os.getenv("HOST_BRIDGE_URL") or "").rstrip("/") or None
BRIDGE_TOKEN = os.getenv("BRIDGE_TOKEN") or None
BRIDGE_TIMEOUT_S = float(os.getenv("HOST_BRIDGE_TIMEOUT_S", "60"))
BRIDGE_READ_TIMEOUT_S = float(os.getenv("HOST_BRIDGE_READ_TIMEOUT_S", "300"))
BRIDGE_PROBE_TIMEOUT_S = float(os.getenv("HOST_BRIDGE_PROBE_TIMEOUT_S", "4"))
BRIDGE_DEFAULT_EXPORTS = ["fcstd", "step", "stl"]

_FORBIDDEN_DIM_KEYS = frozenset({"x", "y", "z"})


def _bridge_http_timeout(*, read: float) -> httpx.Timeout:
    return httpx.Timeout(connect=10.0, read=read, write=60.0, pool=10.0)


def _reject_xyz_dimension_keys(dims: Optional[Dict[str, float]]) -> None:
    """FreeCAD_API_Referentie.md §4: sizes = length/width/height; x/y/z are axes, not box dims."""
    if not dims:
        return
    bad = _FORBIDDEN_DIM_KEYS.intersection({str(k).lower() for k in dims})
    if bad:
        raise HTTPException(
            status_code=400,
            detail=(
                f"dimensions_use_length_width_height_not_xyz:{sorted(bad)}; "
                "use placement.position for offsets (see FreeCAD_API_Referentie.md §11.A)"
            ),
        )


def _bridge_headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if BRIDGE_TOKEN:
        h["Authorization"] = f"Bearer {BRIDGE_TOKEN}"
    return h


def _bridge_probe() -> Dict[str, Any]:
    if not HOST_BRIDGE_URL:
        return {"available": False, "reason": "HOST_BRIDGE_URL_not_set"}
    try:
        r = httpx.get(
            f"{HOST_BRIDGE_URL}/tools",
            timeout=_bridge_http_timeout(read=BRIDGE_PROBE_TIMEOUT_S),
            headers=_bridge_headers(),
        )
        r.raise_for_status()
        info = r.json()
        fc = info.get("freecad", {})
        if not fc.get("available"):
            return {"available": False, "reason": fc.get("reason", "freecad_unavailable_at_bridge")}
        return {"available": True, "version": fc.get("version"), "url": HOST_BRIDGE_URL}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def _bridge_file_urls(bridge_resp: Dict[str, Any]) -> Dict[str, str]:
    """Convert bridge absolute Windows file paths to downloadable URLs.

    Bridge stores files at <bridge_url>/jobs/<workdir_name>/files/<basename>.
    Uses PureWindowsPath so backslash-separated paths from the bridge parse
    correctly even when this agent runs in a Linux container.
    """
    files = bridge_resp.get("files") or {}
    workdir = bridge_resp.get("workdir") or ""
    job_name = PureWindowsPath(workdir).name if workdir else ""
    out: Dict[str, str] = {}
    for kind, full_path in files.items():
        if not full_path or not job_name:
            continue
        basename = PureWindowsPath(full_path).name
        out[kind] = f"{HOST_BRIDGE_URL}/jobs/{job_name}/files/{basename}"
    return out


def _bridge_metrics_to_local(bridge_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Map FreeCAD-style metrics to the trimesh-style schema we expose."""
    bbox = (bridge_metrics or {}).get("bounding_box") or {}
    extents = bbox.get("extents") or [0.0, 0.0, 0.0]
    return {
        "extents": [float(x) for x in extents],
        "volume": float(bridge_metrics.get("volume", 0.0)) if bridge_metrics.get("volume") is not None else None,
        "surface_area": float(bridge_metrics.get("surface_area", 0.0)),
        "watertight": bool(bridge_metrics.get("is_closed", False)),
        "vertex_count": int(bridge_metrics.get("vertex_count", 0)),
        "face_count": int(bridge_metrics.get("face_count", 0)),
    }

CATEGORY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "box":       {"primitive": "box",       "default": {"length": 10.0, "width": 10.0, "height": 10.0}},
    "fighter":   {"primitive": "capsule", "default": {"length": 12.0, "radius": 1.5}},
    "ship":      {"primitive": "capsule", "default": {"length": 60.0, "radius": 6.0}},
    "boss":      {"primitive": "capsule", "default": {"length": 120.0, "radius": 18.0}},
    "vehicle":   {"primitive": "box",     "default": {"length": 4.5, "width": 1.8, "height": 1.6}},
    "building":  {"primitive": "box",     "default": {"length": 10.0, "width": 8.0, "height": 24.0}},
    "prop":      {"primitive": "cylinder","default": {"radius": 0.5, "height": 1.0}},
}

CATEGORY_BOUNDS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "fighter":   {"length": (4.0, 30.0)},
    "ship":      {"length": (20.0, 200.0)},
    "boss":      {"length": (60.0, 400.0)},
    "vehicle":   {"length": (1.0, 20.0)},
    "building":  {"height": (3.0, 200.0)},
    "prop":      {"radius": (0.05, 5.0)},
}


def _make_primitive(primitive: str, dims: Dict[str, float]) -> trimesh.Trimesh:
    if primitive == "box":
        ext = (
            float(dims.get("length", 1.0)),
            float(dims.get("width", 1.0)),
            float(dims.get("height", 1.0)),
        )
        mesh = trimesh.creation.box(extents=ext)
    elif primitive == "cylinder":
        mesh = trimesh.creation.cylinder(
            radius=float(dims.get("radius", 1.0)),
            height=float(dims.get("height", 1.0)),
            sections=32,
        )
    elif primitive == "capsule":
        mesh = trimesh.creation.capsule(
            radius=float(dims.get("radius", 1.0)),
            height=float(dims.get("length", 1.0)),
            count=[16, 16],
        )
    elif primitive == "sphere":
        mesh = trimesh.creation.icosphere(subdivisions=2, radius=float(dims.get("radius", 1.0)))
    else:
        raise HTTPException(400, detail=f"unknown_primitive:{primitive}")
    if not isinstance(mesh, trimesh.Trimesh):
        raise HTTPException(500, detail="primitive_not_trimesh")
    return mesh


def _bbox_metrics(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    bbox = mesh.bounding_box.extents.tolist()
    return {
        "extents": [float(x) for x in bbox],
        "volume": float(mesh.volume) if mesh.is_volume else None,
        "surface_area": float(mesh.area),
        "watertight": bool(mesh.is_watertight),
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
    }


def _save_mesh(mesh: trimesh.Trimesh, prefix: str) -> Dict[str, str]:
    uid = uuid.uuid4().hex[:10]
    job_dir = OUTPUT_DIR / "jobs" / uid
    job_dir.mkdir(parents=True, exist_ok=True)
    stl_path = job_dir / f"{prefix}.stl"
    glb_path = job_dir / f"{prefix}.glb"
    mesh.export(stl_path.as_posix())
    try:
        mesh.export(glb_path.as_posix())
        glb = glb_path.as_posix()
    except Exception:
        glb = ""
    return {"stl": stl_path.as_posix(), "glb": glb}


class BuildBaseRequest(BaseModel):
    category: str
    dimensions: Optional[Dict[str, float]] = None
    mount_points_config: Optional[Dict[str, List[float]]] = None
    placement: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Reserved: position/rotation per FreeCAD_API_Referentie.md §11.A (not forwarded to bridge yet).",
    )


class VariantGenRequest(BaseModel):
    base_model: BuildBaseRequest
    parameter_matrix: Dict[str, List[float]] = Field(default_factory=dict)
    count: Optional[int] = None


class ComponentRef(BaseModel):
    base: BuildBaseRequest
    mount: Optional[List[float]] = None


class AssembleRequest(BaseModel):
    components: List[ComponentRef]
    output_name: Optional[str] = None


app = FastAPI(title="NOVA v2 Agent 21 - FreeCAD Parametric", version="0.2.0")

_BRIDGE_INFO: Dict[str, Any] = {"available": False, "checked_at": 0.0}


def _refresh_bridge_info(force: bool = False) -> Dict[str, Any]:
    global _BRIDGE_INFO
    now = time.time()
    if force or (now - _BRIDGE_INFO.get("checked_at", 0)) > 30:
        info = _bridge_probe()
        info["checked_at"] = now
        _BRIDGE_INFO = info
    return _BRIDGE_INFO


@app.on_event("startup")
def _startup_bridge_probe() -> None:
    info = _refresh_bridge_info(force=True)
    if info.get("available"):
        logger.info("host_bridge available: %s @ %s", info.get("version"), info.get("url"))
    else:
        logger.warning("host_bridge unavailable: %s", info.get("reason"))


def _bridge_call_freecad(category: str, dimensions: Dict[str, float],
                         mounts: Optional[Dict[str, List[float]]] = None,
                         exports: Optional[List[str]] = None,
                         name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """POST /freecad/parametric on the host bridge. Returns None on failure."""
    if not HOST_BRIDGE_URL:
        return None
    payload: Dict[str, Any] = {
        "category": category,
        "dimensions": dimensions,
        "exports": exports or BRIDGE_DEFAULT_EXPORTS,
    }
    if mounts:
        payload["mount_points"] = mounts
    if name:
        payload["name"] = name
    try:
        r = httpx.post(
            f"{HOST_BRIDGE_URL}/freecad/parametric",
            json=payload,
            timeout=_bridge_http_timeout(read=max(BRIDGE_TIMEOUT_S, BRIDGE_READ_TIMEOUT_S)),
            headers=_bridge_headers(),
        )
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return data
        logger.warning("bridge freecad call returned ok=false: %s", data.get("error"))
        return None
    except httpx.TimeoutException as e:
        logger.warning("bridge freecad timeout: %s", e)
        return None
    except Exception as e:
        logger.warning("bridge freecad call failed: %s", e)
        return None


@app.get("/health")
def health() -> Dict[str, Any]:
    info = _refresh_bridge_info()
    bridge_up = bool(info.get("available"))
    return {
        "status": "ok",
        "agent": "21_freecad_parametric",
        "version": "0.2.0",
        "fallback_mode": not bridge_up,
        "fallback_reason": None if bridge_up else info.get("reason"),
        "engine": "freecad_via_bridge" if bridge_up else "trimesh",
        "bridge": {
            "configured": bool(HOST_BRIDGE_URL),
            "url": HOST_BRIDGE_URL,
            "available": bridge_up,
            "freecad_version": info.get("version"),
        },
    }


@app.post("/model/build-base")
def build_base(req: BuildBaseRequest) -> Dict[str, Any]:
    cat = req.category.lower()
    if cat not in CATEGORY_DEFAULTS:
        raise HTTPException(400, detail=f"unknown_category:{cat}; valid={list(CATEGORY_DEFAULTS)}")
    cfg = CATEGORY_DEFAULTS[cat]
    _reject_xyz_dimension_keys(req.dimensions)
    dims = {**cfg["default"], **(req.dimensions or {})}

    mounts: Dict[str, List[float]] = {}
    if req.mount_points_config:
        for name, xyz in req.mount_points_config.items():
            if not isinstance(xyz, list) or len(xyz) != 3:
                continue
            mounts[name] = [float(v) for v in xyz]

    bridge_info = _refresh_bridge_info()
    if bridge_info.get("available"):
        try:
            bridge_resp = _bridge_call_freecad(cat, dims, mounts=mounts)
            if bridge_resp is not None:
                return {
                    "category": cat,
                    "primitive": bridge_resp.get("primitive", cfg["primitive"]),
                    "dimensions": {k: float(v) for k, v in dims.items()},
                    "mount_points": mounts,
                    "placement": req.placement,
                    "files": _bridge_file_urls(bridge_resp),
                    "metrics": _bridge_metrics_to_local(bridge_resp.get("metrics") or {}),
                    "step_export": _bridge_file_urls(bridge_resp).get("step"),
                    "engine_used": "freecad_via_bridge",
                    "freecad_version": bridge_resp.get("freecad_version"),
                    "bridge_job_id": bridge_resp.get("job_id"),
                    "bridge_elapsed_ms": bridge_resp.get("elapsed_ms"),
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("build_base bridge path failed")
            raise HTTPException(status_code=502, detail={"status": "error", "message": f"{type(e).__name__}:{e}"}) from e
        logger.info("bridge build_base failed; falling back to trimesh for category=%s", cat)

    mesh = _make_primitive(cfg["primitive"], dims)
    paths = _save_mesh(mesh, prefix=f"base_{cat}")
    return {
        "category": cat,
        "primitive": cfg["primitive"],
        "dimensions": {k: float(v) for k, v in dims.items()},
        "mount_points": mounts,
        "files": paths,
        "metrics": _bbox_metrics(mesh),
        "step_export": None,
        "step_export_note": "freecad_not_available; STL/GLB only",
        "engine_used": "trimesh",
    }


def _evaluate_robustness(category: str, dims: Dict[str, float]) -> Dict[str, Any]:
    bounds = CATEGORY_BOUNDS.get(category, {})
    brittle: List[str] = []
    for k, (lo, hi) in bounds.items():
        if k in dims and not (lo <= dims[k] <= hi):
            brittle.append(f"{k}_out_of_range[{lo},{hi}]={dims[k]}")
    score = 10.0 - 3.0 * len(brittle)
    return {"robust": len(brittle) == 0, "brittle_params": brittle, "score": max(0.0, score)}


def _evaluate_dimensional(category: str, mesh: trimesh.Trimesh) -> Dict[str, Any]:
    bbox = mesh.bounding_box.extents
    issues: List[str] = []
    if any(x <= 0 for x in bbox.tolist()):
        issues.append("non_positive_extent")
    if mesh.volume is not None and mesh.volume <= 0:
        issues.append("non_positive_volume")
    return {
        "category": category,
        "bbox": [float(x) for x in bbox.tolist()],
        "issues": issues,
        "score": 10.0 if not issues else 4.0,
    }


def _evaluate_export_quality(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    issues: List[str] = []
    if not mesh.is_watertight:
        issues.append("not_watertight")
    if len(mesh.faces) < 4:
        issues.append("face_count_too_low")
    score = 10.0
    if "not_watertight" in issues:
        score -= 5.0
    if "face_count_too_low" in issues:
        score -= 5.0
    return {
        "score": max(0.0, score),
        "issues": issues,
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
    }


def _judge(robust: Dict[str, Any], dim: Dict[str, Any], exp: Dict[str, Any]) -> Dict[str, Any]:
    avg = (robust["score"] + dim["score"] + exp["score"]) / 3.0
    if avg >= 8.0:
        verdict = "accept"
    elif avg >= 5.0:
        verdict = "revise"
    else:
        verdict = "reject"
    return {"verdict": verdict, "average_score": round(avg, 2)}


@app.post("/variants/generate")
def variants_generate(req: VariantGenRequest) -> Dict[str, Any]:
    base = req.base_model
    cat = base.category.lower()
    if cat not in CATEGORY_DEFAULTS:
        raise HTTPException(400, detail=f"unknown_category:{cat}")
    cfg = CATEGORY_DEFAULTS[cat]
    _reject_xyz_dimension_keys(base.dimensions)
    base_dims = {**cfg["default"], **(base.dimensions or {})}

    keys = sorted(req.parameter_matrix.keys())
    grids = [req.parameter_matrix[k] for k in keys]
    if not keys:
        combos = [tuple()]
    else:
        combos = list(itertools.product(*grids))
    if req.count is not None:
        combos = combos[: max(0, int(req.count))]

    bridge_info = _refresh_bridge_info()
    bridge_up = bool(bridge_info.get("available"))
    engines_used: Dict[str, int] = {"freecad_via_bridge": 0, "trimesh": 0}

    variants: List[Dict[str, Any]] = []
    for combo in combos:
        dims = dict(base_dims)
        for k, v in zip(keys, combo):
            dims[k] = float(v)
        try:
            entry: Dict[str, Any] = {
                "params": {k: float(v) for k, v in zip(keys, combo)},
                "dimensions": {k: float(v) for k, v in dims.items()},
            }

            bridge_resp = _bridge_call_freecad(cat, dims) if bridge_up else None
            if bridge_resp is not None:
                metrics = _bridge_metrics_to_local(bridge_resp.get("metrics") or {})
                # Build a synthetic mesh-less jury using bridge metrics.
                robust = _evaluate_robustness(cat, dims)
                dim_issues: List[str] = []
                if any(x <= 0 for x in metrics["extents"]):
                    dim_issues.append("non_positive_extent")
                if (metrics.get("volume") or 0) <= 0:
                    dim_issues.append("non_positive_volume")
                dim = {"category": cat, "bbox": metrics["extents"], "issues": dim_issues,
                       "score": 10.0 if not dim_issues else 4.0}
                exp_issues: List[str] = []
                if not metrics["watertight"]:
                    exp_issues.append("not_watertight")
                if metrics["face_count"] < 4:
                    exp_issues.append("face_count_too_low")
                exp_score = 10.0 - (5.0 if "not_watertight" in exp_issues else 0.0) - (5.0 if "face_count_too_low" in exp_issues else 0.0)
                exp = {"score": max(0.0, exp_score), "issues": exp_issues,
                       "vertex_count": metrics["vertex_count"], "face_count": metrics["face_count"]}
                verdict = _judge(robust, dim, exp)
                entry.update({
                    "files": _bridge_file_urls(bridge_resp),
                    "metrics": metrics,
                    "jury": {"robustness": robust, "dimensional": dim, "export_quality": exp},
                    "verdict": verdict["verdict"],
                    "average_score": verdict["average_score"],
                    "engine_used": "freecad_via_bridge",
                    "freecad_version": bridge_resp.get("freecad_version"),
                })
                engines_used["freecad_via_bridge"] += 1
            else:
                mesh = _make_primitive(cfg["primitive"], dims)
                paths = _save_mesh(mesh, prefix=f"variant_{cat}")
                metrics = _bbox_metrics(mesh)
                jury = {
                    "robustness": _evaluate_robustness(cat, dims),
                    "dimensional": _evaluate_dimensional(cat, mesh),
                    "export_quality": _evaluate_export_quality(mesh),
                }
                verdict = _judge(jury["robustness"], jury["dimensional"], jury["export_quality"])
                entry.update({
                    "files": paths,
                    "metrics": metrics,
                    "jury": jury,
                    "verdict": verdict["verdict"],
                    "average_score": verdict["average_score"],
                    "engine_used": "trimesh",
                })
                engines_used["trimesh"] += 1
            variants.append(entry)
        except HTTPException:
            raise
        except Exception as e:
            variants.append({"params": dict(zip(keys, combo)), "error": f"{type(e).__name__}:{e}"})

    accepted = sum(1 for v in variants if v.get("verdict") == "accept")
    return {
        "category": cat,
        "primitive": cfg["primitive"],
        "variant_count": len(variants),
        "accepted": accepted,
        "engines_used": engines_used,
        "variants": variants,
    }


@app.post("/components/assemble")
def components_assemble(req: AssembleRequest) -> Dict[str, Any]:
    if not req.components:
        raise HTTPException(400, detail="no_components")
    parts: List[trimesh.Trimesh] = []
    metas: List[Dict[str, Any]] = []
    for idx, comp in enumerate(req.components):
        cat = comp.base.category.lower()
        if cat not in CATEGORY_DEFAULTS:
            raise HTTPException(400, detail=f"unknown_category:{cat}")
        cfg = CATEGORY_DEFAULTS[cat]
        dims = {**cfg["default"], **(comp.base.dimensions or {})}
        mesh = _make_primitive(cfg["primitive"], dims)
        if comp.mount:
            offset = np.array(comp.mount[:3], dtype=float)
            mesh = mesh.copy()
            mesh.apply_translation(offset)
            metas.append({"index": idx, "category": cat, "mount": offset.tolist(), "dimensions": dims})
        else:
            metas.append({"index": idx, "category": cat, "mount": [0.0, 0.0, 0.0], "dimensions": dims})
        parts.append(mesh)

    combined = trimesh.util.concatenate(parts)
    if not isinstance(combined, trimesh.Trimesh):
        raise HTTPException(500, detail="assemble_failed")
    name = req.output_name or f"assembly_{int(time.time())}"
    paths = _save_mesh(combined, prefix=name)
    return {
        "components": metas,
        "files": paths,
        "metrics": _bbox_metrics(combined),
        "assembly_method": "trimesh.util.concatenate",
        "step_export": None,
        "step_export_note": "freecad_not_installed; STL/GLB only",
    }


class InvokeBody(BaseModel):
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@app.post("/invoke")
def invoke(body: InvokeBody) -> Dict[str, Any]:
    action = (body.action or "info").lower()
    payload = body.payload or {}

    if action in ("build_base", "build-base", "model"):
        try:
            req = BuildBaseRequest(**payload) if payload else BuildBaseRequest(category="fighter")
        except Exception as e:
            raise HTTPException(400, detail=f"invalid_payload:{e}")
        return build_base(req)

    if action in ("generate", "variants", "variants_generate"):
        try:
            req = VariantGenRequest(**payload) if payload else VariantGenRequest(
                base_model=BuildBaseRequest(category="fighter"),
                parameter_matrix={"length": [8.0, 12.0, 16.0]},
            )
        except Exception as e:
            raise HTTPException(400, detail=f"invalid_payload:{e}")
        return variants_generate(req)

    if action in ("assemble", "components_assemble"):
        try:
            req = AssembleRequest(**payload)
        except Exception as e:
            raise HTTPException(400, detail=f"invalid_payload:{e}")
        return components_assemble(req)

    if action == "info":
        bi = _refresh_bridge_info()
        return {
            "categories": list(CATEGORY_DEFAULTS),
            "fallback_mode": not bi.get("available"),
            "fallback_reason": None if bi.get("available") else bi.get("reason"),
            "engine": "freecad_via_bridge" if bi.get("available") else "trimesh",
            "endpoints": ["/health", "/model/build-base", "/variants/generate", "/components/assemble", "/invoke"],
        }

    return {"error": f"unknown_action:{action}", "valid_actions": ["build_base", "generate", "assemble", "info"]}
