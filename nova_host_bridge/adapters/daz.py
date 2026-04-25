"""DAZ Studio adapter: run DAZStudio.exe with a generated .dsa script (Windows).

CLI flags vary by DAZ build; override with env ``DAZSTUDIO_EXTRA_ARGS`` (space-separated
tokens inserted after the executable). Default follows the session-10 spec shape:
``-noPrompt`` and the ``.dsa`` path as the last argument.
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("bridge.daz")

DEFAULT_DAZ_EXE = Path(r"C:\Program Files\DAZ 3D\DAZStudio4\DAZStudio.exe")


def _exe_candidates_from_base(p: Path) -> List[Path]:
    """Resolve ``DAZStudio.exe`` from a config ``bin`` path (file or directory).

    Supports a **direct** DAZ install folder, or a **shared tools root** (e.g.
    ``L:\\ZZZ Software``) with DAZ under common subpaths.
    """
    out: List[Path] = []
    if p.suffix.lower() == ".exe" and p.is_file():
        return [p.resolve()]
    if not p.is_dir():
        return out
    # Direct install dir
    out.extend(
        [
            (p / "DAZStudio.exe").resolve(),
            (p / "DAZStudio4" / "DAZStudio.exe").resolve(),
        ]
    )
    # Typical layouts under ``L:\ZZZ Software``-style roots
    out.extend(
        [
            (p / "Dazz" / "DAZStudio.exe").resolve(),
            (p / "Dazz" / "DAZStudio4" / "DAZStudio.exe").resolve(),
            (p / "DAZ 3D" / "DAZStudio4" / "DAZStudio.exe").resolve(),
        ]
    )
    return out


class DAZUnavailable(RuntimeError):
    pass


def _resolve_exe(daz_bin: Optional[str]) -> Path:
    candidates: List[Path] = []
    if daz_bin:
        p = Path(daz_bin.strip().strip('"'))
        candidates.extend(_exe_candidates_from_base(p))
    env = os.getenv("DAZSTUDIO_EXE", "").strip()
    if env:
        candidates.append(Path(env))
    candidates.append(DEFAULT_DAZ_EXE)
    for c in candidates:
        if c.is_file():
            return c.resolve()
    raise DAZUnavailable("DAZStudio.exe not found (set host_tools.daz.bin or DAZSTUDIO_EXE)")


def is_available(daz_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_exe(daz_bin)
    except DAZUnavailable as e:
        return {"available": False, "reason": str(e)}
    return {"available": True, "exe": str(exe)}


def _safe_output_dir(workdir_root: Path, output_dir: str) -> Path:
    root = workdir_root.resolve()
    p = Path(output_dir)
    if not p.is_absolute():
        p = (root / p).resolve()
    else:
        p = p.resolve()
    allow = os.getenv("DAZ_OUTPUT_ALLOW_ABSOLUTE", "").lower() in ("1", "true", "yes")
    if not allow and root not in p.parents and p != root:
        if not str(p).startswith(str(root)):
            raise DAZUnavailable(
                "output_dir must be inside BRIDGE_WORKDIR unless DAZ_OUTPUT_ALLOW_ABSOLUTE=1",
            )
    p.mkdir(parents=True, exist_ok=True)
    return p


def render_script(
    script_content: str,
    output_dir: str,
    workdir_root: Path,
    daz_bin: Optional[str] = None,
    timeout_s: float = 900.0,
) -> Dict[str, Any]:
    """Write ``script_content`` to a job-local ``.dsa`` and invoke DAZ Studio.

    Returns discovered ``*.png`` paths under ``output_dir`` (non-recursive).
    """
    exe = _resolve_exe(daz_bin)
    out = _safe_output_dir(workdir_root, output_dir)

    job_id = uuid.uuid4().hex[:12]
    jobdir = workdir_root / f"daz_{job_id}"
    jobdir.mkdir(parents=True, exist_ok=True)
    dsa_path = jobdir / "nova_run.dsa"
    dsa_path.write_text(script_content, encoding="utf-8", newline="\n")

    extra = os.getenv("DAZSTUDIO_EXTRA_ARGS", "").strip()
    if extra:
        cmd: List[str] = [str(exe)] + extra.split() + [str(dsa_path)]
    else:
        # Session 10 wording; adjust via DAZSTUDIO_EXTRA_ARGS if your build differs.
        cmd = [str(exe), "-noPrompt", str(dsa_path)]

    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "job_id": job_id,
            "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-800:],
            "stderr_tail": (e.stderr or "")[-800:],
            "dsa_path": str(dsa_path),
            "output_dir": str(out),
        }

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    pngs = sorted(str(p) for p in out.glob("*.png")) if out.is_dir() else []
    ok = proc.returncode == 0
    result: Dict[str, Any] = {
        "ok": ok,
        "job_id": job_id,
        "workdir": str(jobdir),
        "dsa_path": str(dsa_path),
        "output_dir": str(out),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "png_paths": pngs,
    }
    if not ok:
        result["stdout_tail"] = (proc.stdout or "")[-1200:]
        result["stderr_tail"] = (proc.stderr or "")[-1200:]
    logger.info("daz render job=%s ok=%s pngs=%d", job_id, ok, len(pngs))
    return result
