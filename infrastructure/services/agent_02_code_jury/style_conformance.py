"""Style: pycodestyle (Python) / GDScript heuristics."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List


def check_python_style(code: str) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pycodestyle", path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    finally:
        os.unlink(path)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    err_count = len(lines)
    score = max(0.0, 10.0 - min(10.0, err_count * 0.4))
    return {"score": round(score, 2), "error_count": err_count, "samples": lines[:12]}


def check_gdscript_style(code: str) -> Dict[str, Any]:
    issues: List[str] = []
    for i, ln in enumerate(code.splitlines(), 1):
        if len(ln) > 120:
            issues.append(f"line_{i}_long")
        if "\t" in ln and "    " in ln:
            issues.append(f"line_{i}_mixed_indent")
    score = max(0.0, 10.0 - len(issues) * 0.3)
    return {"score": round(score, 2), "error_count": len(issues), "samples": issues[:12]}
