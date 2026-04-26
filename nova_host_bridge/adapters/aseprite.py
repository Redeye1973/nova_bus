"""Aseprite adapter: CLI via --batch. Per-job workdir; Popen timeout + kill."""
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


def _eff_aseprite_timeout(timeout_s: Optional[float]) -> float:
    if timeout_s is not None:
        return float(timeout_s)
    return float(os.environ.get("BRIDGE_ASEPRITE_TIMEOUT_S", "120"))


def _aseprite_stderr_failed(stderr: str, stdout: str = "") -> bool:
    t = (stderr or "") + (stdout or "")
    return "Error:" in t or "Traceback" in t or "lua:" in t.lower() or "attempt to" in t.lower()


def _aseprite_popen_communicate(cmd: List[str], timeout_s: Optional[float]) -> tuple[int, str, str, bool, float]:
    eff = _eff_aseprite_timeout(timeout_s)
    proc: Optional[subprocess.Popen[str]] = None
    out, err = "", ""
    t0 = time.perf_counter()
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ.copy())
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
        return -1, out or "", (err or "") + "\naseprite_killed_after_timeout", True, (time.perf_counter() - t0) * 1000.0


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
    timeout_s: Optional[float] = None,
) -> Dict[str, Any]:
    """Export an .aseprite/.ase file as a spritesheet PNG + JSON metadata."""
    exe = _resolve_exe(aseprite_bin)
    src = Path(source)
    if not src.is_file():
        raise AsepriteUnavailable(f"source file not found: {source}")

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"aseprite_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    local_src = workdir / src.name
    shutil.copy2(src, local_src)
    sheet_png = workdir / f"{local_src.stem}_sheet.png"
    sheet_json = workdir / f"{local_src.stem}_sheet.json"

    cmd = [
        str(exe), "--batch", "--sheet-type", sheet_type, "--sheet", str(sheet_png), "--data", str(sheet_json),
        "--format", "json-array", str(local_src),
    ]
    rc, stdout, stderr, killed, elapsed_ms = _aseprite_popen_communicate(cmd, timeout_s)
    if killed:
        return {
            "ok": False,
            "job_id": job_id,
            "workdir": str(workdir),
            "error": f"timeout_after_{_eff_aseprite_timeout(timeout_s)}s_killed",
            "stdout_tail": stdout[-500:],
            "stderr_tail": stderr[-500:],
            "elapsed_ms": round(elapsed_ms, 2),
        }
    lua_err = _aseprite_stderr_failed(stderr, stdout)
    ok = rc == 0 and sheet_png.is_file() and not lua_err
    result: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": rc,
        "elapsed_ms": round(elapsed_ms, 2),
        "files": {"sheet": str(sheet_png) if sheet_png.is_file() else None, "data": str(sheet_json) if sheet_json.is_file() else None},
    }
    if lua_err:
        result["error_kind"] = "lua_or_cli_error_in_output"
    if sheet_json.is_file():
        try:
            result["metadata"] = json.loads(sheet_json.read_text(encoding="utf-8"))
        except Exception:
            pass
    if not ok:
        result["stdout_tail"] = stdout[-500:]
        result["stderr_tail"] = stderr[-500:]
    return result


def batch_save_as(
    source: str,
    workdir_root: Path,
    aseprite_bin: Optional[str] = None,
    timeout_s: Optional[float] = None,
) -> Dict[str, Any]:
    """Batch convert image (e.g. PNG) to PNG inside isolated job workdir."""
    exe = _resolve_exe(aseprite_bin)
    src = Path(source)
    if not src.is_file():
        raise AsepriteUnavailable(f"source file not found: {source}")
    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"aseprite_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    local_in = workdir / f"in{src.suffix.lower()}"
    shutil.copy2(src, local_in)
    out_png = workdir / "out.png"
    cmd = [str(exe), "-b", str(local_in), "--save-as", str(out_png)]
    rc, stdout, stderr, killed, elapsed_ms = _aseprite_popen_communicate(cmd, timeout_s)
    if killed:
        return {
            "ok": False,
            "job_id": job_id,
            "workdir": str(workdir),
            "error": f"timeout_after_{_eff_aseprite_timeout(timeout_s)}s_killed",
            "stdout_tail": stdout[-500:],
            "stderr_tail": stderr[-500:],
            "elapsed_ms": round(elapsed_ms, 2),
        }
    lua_err = _aseprite_stderr_failed(stderr, stdout)
    ok = rc == 0 and out_png.is_file() and not lua_err
    r: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": rc,
        "elapsed_ms": round(elapsed_ms, 2),
        "files": {"png": str(out_png) if out_png.is_file() else None},
    }
    if lua_err:
        r["error_kind"] = "lua_or_cli_error_in_output"
    if not ok:
        r["stdout_tail"] = stdout[-500:]
        r["stderr_tail"] = stderr[-500:]
    return r


def run_lua_script(
    script: str,
    workdir_root: Path,
    source: Optional[str] = None,
    aseprite_bin: Optional[str] = None,
    timeout_s: Optional[float] = None,
) -> Dict[str, Any]:
    """Run a .lua script in batch mode; optional image path before --script."""
    exe = _resolve_exe(aseprite_bin)
    lua_path = Path(script)
    if not lua_path.is_file():
        raise AsepriteUnavailable(f"lua script not found: {script}")
    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"aseprite_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    local_lua = workdir / lua_path.name
    shutil.copy2(lua_path, local_lua)
    cmd: List[str] = [str(exe), "-b"]
    if source:
        sp = Path(source)
        if not sp.is_file():
            raise AsepriteUnavailable(f"source not found: {source}")
        local_src = workdir / sp.name
        shutil.copy2(sp, local_src)
        cmd.append(str(local_src))
    cmd += ["--script", str(local_lua)]
    rc, stdout, stderr, killed, elapsed_ms = _aseprite_popen_communicate(cmd, timeout_s)
    if killed:
        return {
            "ok": False,
            "job_id": job_id,
            "workdir": str(workdir),
            "error": f"timeout_after_{_eff_aseprite_timeout(timeout_s)}s_killed",
            "stdout_tail": stdout[-800:],
            "stderr_tail": stderr[-500:],
            "elapsed_ms": round(elapsed_ms, 2),
        }
    lua_err = _aseprite_stderr_failed(stderr, stdout)
    ok = rc == 0 and not lua_err
    r: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": rc,
        "elapsed_ms": round(elapsed_ms, 2),
        "stdout_tail": stdout[-800:],
        "stderr_tail": stderr[-500:],
    }
    if lua_err:
        r["error_kind"] = "lua_or_cli_error_in_output"
    return r


def cleanup_workdir(workdir: str) -> bool:
    p = Path(workdir)
    if not p.exists() or not p.is_dir():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True
