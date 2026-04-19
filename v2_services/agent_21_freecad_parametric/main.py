"""NOVA v2 Agent 21 — FreeCAD Parametric (trimesh-based fallback).

FreeCAD is not installed on this Hetzner deployment. This service implements the
spec'ed endpoints using the `trimesh` library to generate parametric primitives,
variants, and simple component assemblies. STEP export is not available in the
fallback path; STL/GLB are produced instead and metadata reports are emitted.

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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import trimesh
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("freecad_parametric")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

OUTPUT_DIR = Path(os.getenv("FREECAD_OUTPUT_DIR", "/tmp/freecad_parametric"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_DEFAULTS: Dict[str, Dict[str, Any]] = {
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
    stl_path = OUTPUT_DIR / f"{prefix}_{uid}.stl"
    glb_path = OUTPUT_DIR / f"{prefix}_{uid}.glb"
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


app = FastAPI(title="NOVA v2 Agent 21 - FreeCAD Parametric (trimesh fallback)", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "agent": "21_freecad_parametric",
        "version": "0.1.0",
        "fallback_mode": True,
        "fallback_reason": "freecad_not_installed",
        "engine": "trimesh",
    }


@app.post("/model/build-base")
def build_base(req: BuildBaseRequest) -> Dict[str, Any]:
    cat = req.category.lower()
    if cat not in CATEGORY_DEFAULTS:
        raise HTTPException(400, detail=f"unknown_category:{cat}; valid={list(CATEGORY_DEFAULTS)}")
    cfg = CATEGORY_DEFAULTS[cat]
    dims = {**cfg["default"], **(req.dimensions or {})}
    mesh = _make_primitive(cfg["primitive"], dims)

    mounts: Dict[str, List[float]] = {}
    if req.mount_points_config:
        for name, xyz in req.mount_points_config.items():
            if not isinstance(xyz, list) or len(xyz) != 3:
                continue
            mounts[name] = [float(v) for v in xyz]

    paths = _save_mesh(mesh, prefix=f"base_{cat}")
    return {
        "category": cat,
        "primitive": cfg["primitive"],
        "dimensions": {k: float(v) for k, v in dims.items()},
        "mount_points": mounts,
        "files": paths,
        "metrics": _bbox_metrics(mesh),
        "step_export": None,
        "step_export_note": "freecad_not_installed; STL/GLB only",
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
    base_dims = {**cfg["default"], **(base.dimensions or {})}

    keys = sorted(req.parameter_matrix.keys())
    grids = [req.parameter_matrix[k] for k in keys]
    if not keys:
        combos = [tuple()]
    else:
        combos = list(itertools.product(*grids))
    if req.count is not None:
        combos = combos[: max(0, int(req.count))]

    variants: List[Dict[str, Any]] = []
    for combo in combos:
        dims = dict(base_dims)
        for k, v in zip(keys, combo):
            dims[k] = float(v)
        try:
            mesh = _make_primitive(cfg["primitive"], dims)
            paths = _save_mesh(mesh, prefix=f"variant_{cat}")
            metrics = _bbox_metrics(mesh)
            jury = {
                "robustness": _evaluate_robustness(cat, dims),
                "dimensional": _evaluate_dimensional(cat, mesh),
                "export_quality": _evaluate_export_quality(mesh),
            }
            verdict = _judge(jury["robustness"], jury["dimensional"], jury["export_quality"])
            variants.append({
                "params": {k: float(v) for k, v in zip(keys, combo)},
                "dimensions": {k: float(v) for k, v in dims.items()},
                "files": paths,
                "metrics": metrics,
                "jury": jury,
                "verdict": verdict["verdict"],
                "average_score": verdict["average_score"],
            })
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
        return {
            "categories": list(CATEGORY_DEFAULTS),
            "fallback_mode": True,
            "fallback_reason": "freecad_not_installed",
            "engine": "trimesh",
            "endpoints": ["/model/build-base", "/variants/generate", "/components/assemble"],
        }

    return {"error": f"unknown_action:{action}", "valid_actions": ["build_base", "generate", "assemble", "info"]}
