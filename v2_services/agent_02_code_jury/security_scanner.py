"""Security: bandit (Python) / pattern scan (GDScript)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List


def scan_python(code: str) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        r = subprocess.run(
            [sys.executable, "-m", "bandit", "-f", "json", "-q", path],
            capture_output=True,
            text=True,
            timeout=90,
        )
        data = json.loads(r.stdout) if r.stdout.strip() else {"results": []}
    except Exception as e:
        return {"score": 5.0, "issues": [f"bandit_error:{e}"], "high_severity": 0, "medium_severity": 0}
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    issues_data = data.get("results", [])
    high = sum(1 for i in issues_data if i.get("issue_severity") == "HIGH")
    med = sum(1 for i in issues_data if i.get("issue_severity") == "MEDIUM")
    score = 10.0 - high * 3.0 - med * 1.0
    score = max(0.0, min(10.0, score))
    samples = [
        f"{i.get('issue_text')}:{i.get('line_number')}" for i in issues_data[:12]
    ]
    return {
        "score": round(score, 2),
        "issues": samples,
        "high_severity": high,
        "medium_severity": med,
    }


def scan_gdscript(code: str) -> Dict[str, Any]:
    issues: List[str] = []
    for i, ln in enumerate(code.splitlines(), 1):
        if "eval(" in ln or "exec(" in ln:
            issues.append(f"line_{i}:eval_or_exec")
        if "OS.execute" in ln or "OS.shell_open" in ln:
            issues.append(f"line_{i}:dangerous_os_call")
    score = 10.0 if not issues else max(0.0, 10.0 - len(issues) * 2.5)
    return {"score": round(score, 2), "issues": issues[:12], "high_severity": len(issues)}
