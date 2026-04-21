"""FreeCAD adapter: subprocess to freecadcmd.exe with parametric script."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("bridge.freecad")

DEFAULT_FREECAD_BIN = r"L:\ZZZ Software\FreeCad\bin"
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "freecad_parametric.py"

CATEGORY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "fighter":   {"primitive": "capsule", "default": {"length": 12.0, "radius": 1.5}},
    "ship":      {"primitive": "capsule", "default": {"length": 60.0, "radius": 6.0}},
    "boss":      {"primitive": "capsule", "default": {"length": 120.0, "radius": 18.0}},
    "vehicle":   {"primitive": "box",     "default": {"length": 4.5, "width": 1.8, "height": 1.6}},
    "building":  {"primitive": "box",     "default": {"length": 10.0, "width": 8.0, "height": 24.0}},
    "prop":      {"primitive": "cylinder","default": {"radius": 0.5, "height": 1.0}},
}


class FreeCADUnavailable(RuntimeError):
    pass


def _resolve_freecadcmd(freecad_bin: Optional[str]) -> Path:
    bin_dir = Path(freecad_bin or os.getenv("FREECAD_BIN") or DEFAULT_FREECAD_BIN)
    exe = bin_dir / "freecadcmd.exe"
    if not exe.is_file():
        raise FreeCADUnavailable(f"freecadcmd.exe not found at {exe}")
    return exe


def is_available(freecad_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_freecadcmd(freecad_bin)
    except FreeCADUnavailable as e:
        return {"available": False, "reason": str(e)}
    try:
        r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=15)
        version = (r.stdout or r.stderr or "").strip().splitlines()[0] if (r.stdout or r.stderr) else ""
        return {"available": True, "exe": str(exe), "version": version}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def build_parametric(
    spec: Dict[str, Any],
    workdir_root: Path,
    freecad_bin: Optional[str] = None,
    timeout_s: float = 60.0,
) -> Dict[str, Any]:
    """Run the FreeCAD parametric script with the given spec.

    `spec` may include `category` (auto-fills primitive/dimensions defaults)
    or directly `primitive` + `dimensions`.
    """
    exe = _resolve_freecadcmd(freecad_bin)
    if not SCRIPT_PATH.is_file():
        raise FreeCADUnavailable(f"parametric script missing at {SCRIPT_PATH}")

    cat = (spec.get("category") or "").lower()
    if cat and cat in CATEGORY_DEFAULTS:
        cfg = CATEGORY_DEFAULTS[cat]
        primitive = spec.get("primitive") or cfg["primitive"]
        dims = {**cfg["default"], **(spec.get("dimensions") or {})}
    else:
        primitive = spec.get("primitive") or "box"
        dims = spec.get("dimensions") or {}

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"freecad_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    spec_full = {
        "name": spec.get("name") or f"base_{cat or primitive}",
        "primitive": primitive,
        "dimensions": dims,
        "mount_points": spec.get("mount_points") or {},
        "exports": spec.get("exports") or ["fcstd", "step", "stl"],
    }
    spec_path = workdir / "spec.json"
    result_path = workdir / "result.json"
    spec_path.write_text(json.dumps(spec_full, indent=2), encoding="utf-8")

    cmd = [str(exe), str(SCRIPT_PATH)]
    env = os.environ.copy()
    env["FC_SPEC"] = str(spec_path)
    env["FC_RESULT"] = str(result_path)
    env["FC_WORKDIR"] = str(workdir)
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "job_id": job_id,
            "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:],
            "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    if not result_path.is_file():
        return {
            "ok": False,
            "job_id": job_id,
            "error": "freecadcmd_did_not_write_result",
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-500:],
            "stderr_tail": (proc.stderr or "")[-500:],
            "elapsed_ms": round(elapsed_ms, 2),
        }
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload.setdefault("job_id", job_id)
    payload["elapsed_ms"] = round(elapsed_ms, 2)
    payload["workdir"] = str(workdir)
    payload["exit_code"] = proc.returncode
    if proc.returncode != 0 and payload.get("ok"):
        payload["ok"] = False
        payload["stderr_tail"] = (proc.stderr or "")[-500:]
    return payload


def cleanup_workdir(workdir: str) -> bool:
    p = Path(workdir)
    if not p.exists() or not p.is_dir():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True
