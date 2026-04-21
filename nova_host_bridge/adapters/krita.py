"""Krita adapter: export via krita.exe --export flag."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("bridge.krita")

DEFAULT_KRITA_BIN = r"C:\Program Files\Krita (x64)\bin"


class KritaUnavailable(RuntimeError):
    pass


def _resolve_exe(krita_bin: Optional[str]) -> Path:
    bin_dir = Path(krita_bin or os.getenv("KRITA_BIN") or DEFAULT_KRITA_BIN)
    exe = bin_dir / "krita.exe"
    if not exe.is_file():
        raise KritaUnavailable(f"krita.exe not found at {exe}")
    return exe


def is_available(krita_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_exe(krita_bin)
    except KritaUnavailable as e:
        return {"available": False, "reason": str(e)}
    try:
        r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=20)
        version = (r.stdout or r.stderr or "").strip().splitlines()[0] if (r.stdout or r.stderr) else ""
        return {"available": True, "exe": str(exe), "version": version}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def export_png(
    source: str,
    workdir_root: Path,
    krita_bin: Optional[str] = None,
    timeout_s: float = 120.0,
) -> Dict[str, Any]:
    """Export a .kra file to PNG via `krita --export --export-filename out.png source.kra`."""
    exe = _resolve_exe(krita_bin)
    src = Path(source)
    if not src.is_file():
        raise KritaUnavailable(f"source file not found: {source}")

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"krita_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    out_png = workdir / f"{src.stem}.png"

    cmd = [str(exe), "--export", "--export-filename", str(out_png), str(src)]
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False, "job_id": job_id, "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:], "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    ok = out_png.is_file() and out_png.stat().st_size > 0
    result: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "files": {"png": str(out_png) if out_png.is_file() else None},
    }
    if not ok:
        result["stdout_tail"] = (proc.stdout or "")[-500:]
        result["stderr_tail"] = (proc.stderr or "")[-500:]
    return result


def cleanup_workdir(workdir: str) -> bool:
    p = Path(workdir)
    if not p.exists() or not p.is_dir():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True
