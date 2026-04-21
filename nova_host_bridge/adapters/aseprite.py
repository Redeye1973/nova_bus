"""Aseprite adapter: pure CLI via --batch. Steam license reused from L:\\SteamLibrary."""
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

logger = logging.getLogger("bridge.aseprite")

DEFAULT_ASEPRITE_BIN = r"L:\SteamLibrary\steamapps\common\Aseprite"


class AsepriteUnavailable(RuntimeError):
    pass


def _resolve_exe(aseprite_bin: Optional[str]) -> Path:
    bin_dir = Path(aseprite_bin or os.getenv("ASEPRITE_BIN") or DEFAULT_ASEPRITE_BIN)
    exe = bin_dir / "Aseprite.exe"
    if not exe.is_file():
        raise AsepriteUnavailable(f"Aseprite.exe not found at {exe}")
    return exe


def is_available(aseprite_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_exe(aseprite_bin)
    except AsepriteUnavailable as e:
        return {"available": False, "reason": str(e)}
    try:
        r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=15)
        version = (r.stdout or r.stderr or "").strip().splitlines()[0] if (r.stdout or r.stderr) else ""
        return {"available": True, "exe": str(exe), "version": version}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def export_spritesheet(
    source: str,
    workdir_root: Path,
    sheet_type: str = "horizontal",
    aseprite_bin: Optional[str] = None,
    timeout_s: float = 120.0,
) -> Dict[str, Any]:
    """Export an .aseprite/.ase file as a spritesheet PNG + JSON metadata.

    sheet_type: horizontal | vertical | rows | columns | packed
    """
    exe = _resolve_exe(aseprite_bin)
    src = Path(source)
    if not src.is_file():
        raise AsepriteUnavailable(f"source file not found: {source}")

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"aseprite_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    sheet_png = workdir / f"{src.stem}_sheet.png"
    sheet_json = workdir / f"{src.stem}_sheet.json"

    cmd = [
        str(exe),
        "--batch",
        "--sheet-type", sheet_type,
        "--sheet", str(sheet_png),
        "--data", str(sheet_json),
        "--format", "json-array",
        str(src),
    ]
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False, "job_id": job_id, "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:], "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    ok = proc.returncode == 0 and sheet_png.is_file()
    result: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "files": {"sheet": str(sheet_png) if sheet_png.is_file() else None,
                  "data": str(sheet_json) if sheet_json.is_file() else None},
    }
    if sheet_json.is_file():
        try:
            result["metadata"] = json.loads(sheet_json.read_text(encoding="utf-8"))
        except Exception:
            pass
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
