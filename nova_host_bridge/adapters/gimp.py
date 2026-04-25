"""GIMP adapter: batch processing via gimp-console Script-Fu."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("bridge.gimp")

DEFAULT_GIMP_BIN = r"L:\ZZZ Software\GIMP 3"


class GimpUnavailable(RuntimeError):
    pass


def _resolve_exe(gimp_bin: Optional[str]) -> Path:
    bin_dir = Path(gimp_bin or os.getenv("GIMP_BIN") or DEFAULT_GIMP_BIN)
    console = bin_dir / "bin" / "gimp-console-3.2.exe"
    if not console.is_file():
        console = bin_dir / "bin" / "gimp-console-3.exe"
    if not console.is_file():
        console = bin_dir / "bin" / "gimp-console.exe"
    if not console.is_file():
        raise GimpUnavailable(f"gimp-console not found in {bin_dir}")
    return console


def is_available(gimp_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_exe(gimp_bin)
    except GimpUnavailable as e:
        return {"available": False, "reason": str(e)}
    try:
        r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=15)
        version = (r.stdout or r.stderr or "").strip()
        return {"available": True, "exe": str(exe), "version": version}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def run_script_fu(
    script: str,
    workdir_root: Path,
    gimp_bin: Optional[str] = None,
    timeout_s: float = 120.0,
) -> Dict[str, Any]:
    """Run a Script-Fu expression in GIMP batch mode.

    Example script: '(gimp-version)'
    """
    exe = _resolve_exe(gimp_bin)
    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"gimp_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    cmd = [str(exe), "-i", "-b", script, "-b", "(gimp-quit 0)"]
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
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
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-500:],
    }


def batch_process(
    source: str,
    output_dir: str,
    script: str,
    gimp_bin: Optional[str] = None,
    timeout_s: float = 300.0,
) -> Dict[str, Any]:
    """Run a Script-Fu batch operation on a source image.

    The script should reference 'source-path' and 'output-dir' placeholders.
    """
    exe = _resolve_exe(gimp_bin)
    job_id = uuid.uuid4().hex[:12]

    actual_script = script.replace("{source}", source).replace("{output}", output_dir)

    cmd = [str(exe), "-i", "-b", actual_script, "-b", "(gimp-quit 0)"]
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False, "job_id": job_id, "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:], "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    return {
        "ok": proc.returncode == 0,
        "job_id": job_id,
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-500:],
    }


def cleanup_workdir(workdir: str) -> bool:
    p = Path(workdir)
    if not p.exists() or not p.is_dir():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True
