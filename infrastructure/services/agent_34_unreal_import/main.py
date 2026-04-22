"""NOVA v2 Agent 34 — Unreal import prep (FBX/USD validation, path rewrite mapping; no UE runtime)."""
from __future__ import annotations

import base64
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 34 - Unreal Import Prep", version="0.1.0")


def _inspect_fbx(raw: bytes) -> Dict[str, Any]:
    if len(raw) < 32:
        return {"valid": False, "kind": None, "reason": "too_small"}
    head = raw[:64]
    if b"Kaydara FBX Binary" in head or (head.startswith(b"Kaydara") and b"FBX" in head):
        return {"valid": True, "kind": "fbx_binary", "size_bytes": len(raw)}
    try:
        prefix = raw[: min(240, len(raw))].decode("ascii", errors="ignore")
    except Exception:
        prefix = ""
    if "Kaydara" in prefix and "FBX" in prefix:
        return {"valid": True, "kind": "fbx_ascii", "size_bytes": len(raw)}
    return {"valid": False, "kind": None, "reason": "fbx_magic_not_found"}


def _inspect_usd(text: str) -> Dict[str, Any]:
    if not text.strip():
        return {"valid": False, "kind": None}
    lower = text.lower()
    if "#usda" in lower or "usda" in lower[:20]:
        kind = "usda"
    elif lower.lstrip().startswith("pxrusd"):
        kind = "usdc_text_probe"
    else:
        kind = "usd_unknown"
    prims = re.findall(r"def\s+(\w+)\s+\"([^\"]+)\"", text)
    materials = [p for p in prims if p[0] == "Material"]
    meshes = [p for p in prims if p[0] in ("Mesh", "Xform")]
    return {
        "valid": True,
        "kind": kind,
        "material_count": len(materials),
        "meshish_prim_count": len(meshes),
    }


def _rewrite_texture_paths(text: str) -> Dict[str, Any]:
    """Map common UE-style /Game/ paths to a portable /Project/Content/ convention."""
    rewritten = text.replace("/Game/", "/Project/Content/")
    changed = rewritten != text
    return {"changed": changed, "text": rewritten, "replacements": int(text.count("/Game/"))}


class PrepBody(BaseModel):
    fbx_b64: Optional[str] = None
    usd_text: Optional[str] = None
    material_map: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional Unreal→glTF style material name hints",
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "34_unreal_import", "version": "0.1.0"}


@app.post("/unreal/prep")
def unreal_prep(body: PrepBody) -> Dict[str, Any]:
    if not body.fbx_b64 and not body.usd_text:
        raise HTTPException(400, detail="provide_fbx_b64_or_usd_text")
    fbx_report: Optional[Dict[str, Any]] = None
    usd_report: Optional[Dict[str, Any]] = None
    path_report: Optional[Dict[str, Any]] = None
    if body.fbx_b64:
        try:
            raw = base64.b64decode(body.fbx_b64, validate=True)
        except Exception as exc:
            raise HTTPException(400, detail=f"invalid_fbx_b64:{exc}") from exc
        fbx_report = _inspect_fbx(raw)
    if body.usd_text is not None:
        usd_report = _inspect_usd(body.usd_text)
        path_report = _rewrite_texture_paths(body.usd_text)
    return {
        "fbx": fbx_report,
        "usd": usd_report,
        "texture_paths": path_report,
        "material_map": body.material_map or {},
        "unreal_py_stub": "import unreal  # noqa: F401 — runtime import reserved for editor builds",
    }


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(body, dict) and ("fbx_b64" in body or "usd_text" in body):
        return unreal_prep(PrepBody.model_validate(body))
    return {"hint": "POST /unreal/prep", "keys": list(body.keys()) if isinstance(body, dict) else []}
