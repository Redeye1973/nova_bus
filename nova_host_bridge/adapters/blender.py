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


def _eff_blender_timeout(timeout_s: Optional[float]) -> float:
    if timeout_s is not None:
        return float(timeout_s)
    return float(os.environ.get("BRIDGE_BLENDER_TIMEOUT_S", "600"))


def _blender_popen_communicate(
    args: List[str],
    timeout_s: Optional[float],
    env_full: Optional[Dict[str, str]] = None,
) -> tuple[int, str, str, bool, float]:
    """Run blender subprocess; on timeout kill child. Returns (rc, stdout, stderr, killed, elapsed_ms)."""
    eff = _eff_blender_timeout(timeout_s)
    proc: Optional[subprocess.Popen[str]] = None
    out, err = "", ""
    t0 = time.perf_counter()
    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env_full or os.environ.copy(),
        )
        out, err = proc.communicate(timeout=eff)
        rc = int(proc.returncode) if proc.returncode is not None else -1
        return rc, out or "", err or "", False, (time.perf_counter() - t0) * 1000.0
    except subprocess.TimeoutExpired:
        if proc is not None:
            proc.kill()
            try:
                out, err = proc.communicate(timeout=30)
            except Exception:
                pass
        return -1, out or "", (err or "") + "\nblender_subprocess_killed_after_timeout", True, (time.perf_counter() - t0) * 1000.0


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
    timeout_s: Optional[float] = None,
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

    rc, stdout, stderr, killed, elapsed_ms = _blender_popen_communicate(args, timeout_s, os.environ.copy())
    if killed:
        return {
            "ok": False,
            "job_id": job_id,
            "workdir": str(workdir),
            "error": f"timeout_after_{_eff_blender_timeout(timeout_s)}s_killed",
            "stdout_tail": stdout[-500:],
            "stderr_tail": stderr[-500:],
            "elapsed_ms": round(elapsed_ms, 2),
        }

    expected = workdir / f"frame_{frame:04d}.png"
    ok = rc == 0 and expected.is_file()
    result: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": rc,
        "elapsed_ms": round(elapsed_ms, 2),
        "frame": frame,
        "files": {"png": str(expected) if expected.is_file() else None},
    }
    if not ok:
        result["stdout_tail"] = stdout[-1000:]
        result["stderr_tail"] = stderr[-500:]
    return result


def run_script(
    script: str,
    workdir_root: Path,
    source: Optional[str] = None,
    blender_bin: Optional[str] = None,
    timeout_s: Optional[float] = None,
) -> Dict[str, Any]:
    """Run a Python script in Blender's background mode.

    `script`: path to .py file. `source`: optional .blend to load first.
    Each invocation is a **new** `blender.exe` subprocess (no persistent server).
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

    env = {**os.environ, "BLENDER_WORKDIR": str(workdir)}
    rc, stdout, stderr, killed, elapsed_ms = _blender_popen_communicate(args, timeout_s, env)
    if killed:
        return {
            "ok": False,
            "job_id": job_id,
            "workdir": str(workdir),
            "exit_code": rc,
            "elapsed_ms": round(elapsed_ms, 2),
            "error": f"timeout_after_{_eff_blender_timeout(timeout_s)}s_killed",
            "stdout_tail": stdout[-1500:],
            "stderr_tail": stderr[-500:],
        }

    return {
        "ok": rc == 0,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": rc,
        "elapsed_ms": round(elapsed_ms, 2),
        "stdout_tail": stdout[-1500:],
        "stderr_tail": stderr[-500:],
    }


def cleanup_workdir(workdir: str) -> bool:
    p = Path(workdir)
    if not p.exists() or not p.is_dir():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True
