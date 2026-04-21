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
    """Run Godot in headless mode against a project dir and report if it loads cleanly.

    Uses `--check-only` via `--editor --quit-after 1` pattern: loads the project,
    imports assets, and exits. Non-zero code or error-lines in stderr -> not-ok.
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

    args: List[str] = [str(exe), "--headless", "--path", str(proj), "--quit-after", "1"]
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
    errors = [ln for ln in (stderr + "\n" + stdout).splitlines()
              if "ERROR:" in ln or "SCRIPT ERROR:" in ln]
    ok = proc.returncode == 0 and not errors
    return {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "project": str(proj),
        "errors": errors[:20],
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
