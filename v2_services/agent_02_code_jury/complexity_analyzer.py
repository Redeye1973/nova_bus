"""Complexity: radon (Python) / heuristics (GDScript)."""
from __future__ import annotations

import ast
from typing import Any, Dict

from radon.complexity import cc_visit


def analyze_python(code: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"score": 0.0, "max_cc": None, "issues": [f"syntax_error:{e}"], "avg_complexity": None}

    blocks = cc_visit(tree)
    if not blocks:
        return {"score": 10.0, "max_cc": 1, "issues": [], "avg_complexity": 1.0}

    complexities = [b.complexity for b in blocks]
    max_cc = max(complexities)
    avg_cc = sum(complexities) / len(complexities)

    issues: list[str] = []
    if max_cc > 15:
        issues.append(f"high_cyclomatic_complexity:{max_cc}")
    if max_cc > 25:
        issues.append("critical_complexity")

    # Penalize high complexity
    score = 10.0
    if max_cc > 10:
        score -= min(5.0, (max_cc - 10) * 0.25)
    if max_cc > 20:
        score -= 2.0
    score = max(0.0, min(10.0, score))

    return {
        "score": round(score, 2),
        "max_cc": max_cc,
        "avg_complexity": round(avg_cc, 2),
        "issues": issues,
    }


def analyze_gdscript(code: str) -> Dict[str, Any]:
    lines = [ln for ln in code.splitlines() if ln.strip()]
    n = len(lines)
    if n == 0:
        return {"score": 0.0, "max_cc": None, "issues": ["empty"], "avg_complexity": None}

    func_count = sum(1 for ln in lines if "func " in ln)
    if func_count == 0:
        return {"score": 0.0, "max_cc": None, "issues": ["no_functions"], "avg_complexity": None}

    avg_len = n / max(func_count, 1)
    if avg_len > 80:
        return {"score": 4.0, "max_cc": None, "issues": ["long_script_lines"], "avg_complexity": None}

    score = 10.0 if n < 200 else max(5.0, 10.0 - (n - 200) / 100)
    return {"score": round(score, 2), "max_cc": None, "issues": [], "avg_complexity": None}
