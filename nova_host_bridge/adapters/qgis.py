"""QGIS adapter: subprocess to qgis_process-qgis-ltr.bat (or qgis_process.exe)."""
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

logger = logging.getLogger("bridge.qgis")

DEFAULT_QGIS_BIN = r"C:\Program Files\QGIS 3.40.13\bin"


class QGISUnavailable(RuntimeError):
    pass


def _resolve_qgis_process(qgis_bin: Optional[str]) -> Path:
    bin_dir = Path(qgis_bin or os.getenv("QGIS_BIN") or DEFAULT_QGIS_BIN)
    candidates = [
        bin_dir / "qgis_process-qgis-ltr.bat",
        bin_dir / "qgis_process-qgis.bat",
        bin_dir / "qgis_process.exe",
        bin_dir.parent / "apps" / "qgis-ltr" / "bin" / "qgis_process.exe",
        bin_dir.parent / "apps" / "qgis" / "bin" / "qgis_process.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise QGISUnavailable(f"qgis_process binary not found near {bin_dir}")


def _run(exe: Path, args: List[str], timeout_s: float) -> subprocess.CompletedProcess:
    """Invoke QGIS CLI handling .bat-with-spaces quoting on Windows."""
    if exe.suffix.lower() == ".bat":
        cmd_str = subprocess.list2cmdline([str(exe)] + args)
        return subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=timeout_s)
    return subprocess.run([str(exe)] + args, capture_output=True, text=True, timeout=timeout_s)


def is_available(qgis_bin: Optional[str] = None) -> Dict[str, Any]:
    try:
        exe = _resolve_qgis_process(qgis_bin)
    except QGISUnavailable as e:
        return {"available": False, "reason": str(e)}
    try:
        r = _run(exe, ["--version"], timeout_s=30)
        out = (r.stdout or r.stderr or "").strip()
        first = out.splitlines()[0] if out else ""
        return {"available": True, "exe": str(exe), "version": first}
    except Exception as e:
        return {"available": False, "reason": f"{type(e).__name__}:{e}"}


def list_algorithms(qgis_bin: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    exe = _resolve_qgis_process(qgis_bin)
    r = _run(exe, ["list"], timeout_s=120)
    lines = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    algos = [ln for ln in lines if ":" in ln and not ln.startswith("--")]
    return {"count": len(algos), "first": algos[:limit], "exit_code": r.returncode}


def run_algorithm(
    algorithm: str,
    params: Dict[str, Any],
    workdir_root: Path,
    qgis_bin: Optional[str] = None,
    timeout_s: float = 300.0,
) -> Dict[str, Any]:
    """Run a QGIS Processing algorithm via qgis_process CLI.

    `algorithm`  e.g. "native:buffer", "qgis:bufferedlines"
    `params`     algorithm parameter dict (paths must be absolute or
                 will be resolved relative to workdir).
    Returns: {ok, job_id, workdir, stdout_tail, outputs (parsed if JSON)}.
    """
    exe = _resolve_qgis_process(qgis_bin)
    job_id = uuid.uuid4().hex[:12]
    workdir = workdir_root / f"qgis_{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    enriched: Dict[str, Any] = {}
    for k, v in params.items():
        if isinstance(v, str) and v.startswith("workdir:"):
            enriched[k] = str(workdir / v.split(":", 1)[1])
        else:
            enriched[k] = v

    args = ["run", algorithm, "--json"]
    for k, v in enriched.items():
        args.append(f"--{k}={v}")

    started = time.perf_counter()
    try:
        proc = _run(exe, args, timeout_s=timeout_s)
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "job_id": job_id,
            "error": f"timeout after {timeout_s}s",
            "stdout_tail": (e.stdout or "")[-500:],
            "stderr_tail": (e.stderr or "")[-500:],
        }
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    parsed: Optional[Dict[str, Any]] = None
    raw = proc.stdout or ""
    try:
        json_start = raw.find("{")
        if json_start >= 0:
            parsed = json.loads(raw[json_start:])
    except Exception:
        parsed = None

    return {
        "ok": proc.returncode == 0,
        "job_id": job_id,
        "workdir": str(workdir),
        "exit_code": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 2),
        "algorithm": algorithm,
        "params": enriched,
        "outputs": parsed,
        "stdout_tail": raw[-1000:],
        "stderr_tail": (proc.stderr or "")[-500:],
    }


def cleanup_workdir(workdir: str) -> bool:
    p = Path(workdir)
    if not p.exists() or not p.is_dir():
        return False
    shutil.rmtree(p, ignore_errors=True)
    return True
