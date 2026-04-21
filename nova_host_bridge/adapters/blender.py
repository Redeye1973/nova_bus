"""Blender adapter: subprocess to blender.exe --background for renders/scripts."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("bridge.blender")

DEFAULT_BLENDER_BIN = r"C:\Program Files\Blender Foundation\Blender 4.3"


class BlenderUnavailable(RuntimeError):
    pass


def _resolve_exe(blender_bin: Optional[str]) -> Path:
    bin_dir = Path(blender_bin or os.getenv("BLENDER_BIN") or DEFAULT_BLENDER_BIN)
    exe = bin_dir / "blender.exe"
    if not exe.is_file():
        raise BlenderUnavailable(f"blender.exe not found at {exe}")
    return exe


def is_available(blender_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_exe(blender_bin)
    except BlenderUnavailable as e:
        return {"available": False, "reason": str(e)}
    try:
        r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=20)
        out = (r.stdout or r.stderr or "").strip()
        first = out.splitlines()[0] if out else ""
        return {"available": True, "exe": str(exe), "version": first}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def render_frame(
    source: str,
    workdir_root: Path,
    frame: int = 1,
    engine: Optional[str] = None,
    blender_bin: Optional[str] = None,
    timeout_s: float = 300.0,
) -> Dict[str, Any]:
    """Render a single frame from a .blend file.

    `engine`: optional ("CYCLES" | "BLENDER_EEVEE" | "BLENDER_WORKBENCH"); uses .blend default if None.
    Output: PNG at workdir/frame_{N:04d}.png.
    """
    exe = _resolve_exe(blender_bin)
    src = Path(source)
    if not src.is_file():
        raise BlenderUnavailable(f"source .blend not found: {source}")

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"blender_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    out_prefix = workdir / "frame_"

    args: List[str] = [str(exe), "--background", str(src)]
    if engine:
        args += ["--engine", engine]
    args += ["--render-output", str(out_prefix), "--render-format", "PNG", "--render-frame", str(frame)]

    started = time.perf_counter()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False, "job_id": job_id, "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:], "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    expected = workdir / f"frame_{frame:04d}.png"
    ok = proc.returncode == 0 and expected.is_file()
    result: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "frame": frame,
        "files": {"png": str(expected) if expected.is_file() else None},
    }
    if not ok:
        result["stdout_tail"] = (proc.stdout or "")[-1000:]
        result["stderr_tail"] = (proc.stderr or "")[-500:]
    return result


def run_script(
    script: str,
    workdir_root: Path,
    source: Optional[str] = None,
    blender_bin: Optional[str] = None,
    timeout_s: float = 300.0,
) -> Dict[str, Any]:
    """Run a Python script in Blender's background mode.

    `script`: path to .py file. `source`: optional .blend to load first.
    """
    exe = _resolve_exe(blender_bin)
    script_path = Path(script)
    if not script_path.is_file():
        raise BlenderUnavailable(f"script not found: {script}")

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"blender_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    args: List[str] = [str(exe), "--background"]
    if source:
        src = Path(source)
        if not src.is_file():
            raise BlenderUnavailable(f"source .blend not found: {source}")
        args.append(str(src))
    args += ["--python", str(script_path)]

    started = time.perf_counter()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout_s,
                              env={**os.environ, "BLENDER_WORKDIR": str(workdir)})
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False, "job_id": job_id, "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:], "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    return {
        "ok": proc.returncode == 0,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "stdout_tail": (proc.stdout or "")[-1500:],
        "stderr_tail": (proc.stderr or "")[-500:],
    }


def cleanup_workdir(workdir: str) -> bool:
    p = Path(workdir)
    if not p.exists() or not p.is_dir():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True
