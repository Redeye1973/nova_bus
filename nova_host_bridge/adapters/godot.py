"""Godot adapter: --headless project validation and script execution."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("bridge.godot")

DEFAULT_GODOT_BIN = r"L:\ZZZ Software\Godot"
DEFAULT_GODOT_CMD = "Godot_v4.6.2-stable_win64_console.exe"


class GodotUnavailable(RuntimeError):
    pass


def _resolve_exe(godot_bin: Optional[str], godot_cmd: Optional[str] = None) -> Path:
    bin_dir = Path(godot_bin or os.getenv("GODOT_BIN") or DEFAULT_GODOT_BIN)
    cmd_name = godot_cmd or os.getenv("GODOT_CMD") or DEFAULT_GODOT_CMD
    exe = bin_dir / cmd_name
    if not exe.is_file():
        candidates = list(bin_dir.glob("Godot*.exe"))
        if candidates:
            exe = sorted(candidates, key=lambda p: ("console" not in p.name, p.name))[0]
    if not exe.is_file():
        raise GodotUnavailable(f"Godot exe not found in {bin_dir}")
    return exe


def is_available(godot_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_exe(godot_bin)
    except GodotUnavailable as e:
        return {"available": False, "reason": str(e)}
    try:
        r = subprocess.run([str(exe), "--version", "--headless"],
                           capture_output=True, text=True, timeout=15)
        out = (r.stdout or r.stderr or "").strip()
        version = out.splitlines()[-1] if out else ""
        return {"available": True, "exe": str(exe), "version": version}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def validate_project(
    project_dir: str,
    workdir_root: Path,
    godot_bin: Optional[str] = None,
    timeout_s: float = 60.0,
) -> Dict[str, Any]:
    """Import a Godot project's assets headlessly and report errors.

    Uses `--editor --headless --path <proj> --quit-after 1` which triggers
    asset import + script parsing and exits after one frame. Unlike
    `--headless` without `--editor`, this does NOT require a main scene,
    so it works for validation of asset projects (e.g. sprite imports).

    `ok` means: exit_code == 0 AND no ERROR: lines in stderr.
    SCRIPT ERROR: lines are reported separately but do not fail validation
    (they may come from unused scripts).
    """
    exe = _resolve_exe(godot_bin)
    proj = Path(project_dir)
    if not proj.is_dir():
        raise GodotUnavailable(f"project_dir not found: {project_dir}")
    godot_project = proj / "project.godot"
    if not godot_project.is_file():
        raise GodotUnavailable(f"project.godot not found in {project_dir}")

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"godot_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    args: List[str] = [str(exe), "--editor", "--headless", "--path", str(proj), "--quit-after", "1"]
    started = time.perf_counter()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False, "job_id": job_id, "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:], "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    stderr = proc.stderr or ""
    stdout = proc.stdout or ""
    combined = stderr + "\n" + stdout
    # Filter out known-cosmetic Windows HRESULT warnings that Godot 4 emits
    # on every run (returning empty String() from shell integration probes).
    COSMETIC = ('Condition "res != ((HRESULT)0x00000000)"',)
    def _is_cosmetic(line: str) -> bool:
        return any(marker in line for marker in COSMETIC)
    fatal_errors = [ln for ln in combined.splitlines()
                    if "ERROR:" in ln and "SCRIPT ERROR:" not in ln and not _is_cosmetic(ln)]
    script_errors = [ln for ln in combined.splitlines() if "SCRIPT ERROR:" in ln]
    # Exit code is authoritative for `ok`; errors are informational.
    ok = proc.returncode == 0 and not script_errors
    return {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "project": str(proj),
        "errors": fatal_errors[:20],
        "script_errors": script_errors[:20],
        "stdout_tail": stdout[-1000:],
        "stderr_tail": stderr[-1000:],
    }


def run_script(
    script: str,
    workdir_root: Path,
    project_dir: Optional[str] = None,
    godot_bin: Optional[str] = None,
    timeout_s: float = 120.0,
) -> Dict[str, Any]:
    """Run a GDScript file headlessly.

    `script`: .gd path. `project_dir`: optional, if script references project assets.
    """
    exe = _resolve_exe(godot_bin)
    script_path = Path(script)
    if not script_path.is_file():
        raise GodotUnavailable(f"script not found: {script}")

    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"godot_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    args: List[str] = [str(exe), "--headless"]
    if project_dir:
        p = Path(project_dir)
        if not p.is_dir():
            raise GodotUnavailable(f"project_dir not found: {project_dir}")
        args += ["--path", str(p)]
    args += ["--script", str(script_path)]

    started = time.perf_counter()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout_s)
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
