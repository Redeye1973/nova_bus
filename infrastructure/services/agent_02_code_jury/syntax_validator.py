"""Syntax validation: Python (ast) and GDScript (heuristic fallback, no Godot binary in container)."""
from __future__ import annotations

import ast
import re
from typing import Any, Dict, List


def validate_python(code: str) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    try:
        ast.parse(code)
        ok = True
    except SyntaxError as e:
        ok = False
        errors.append(
            {
                "line": e.lineno or 0,
                "column": e.offset or 0,
                "message": str(e.msg),
            }
        )
    return {"valid": ok, "errors": errors, "score": 10.0 if ok else 0.0}


def _gdscript_balance_braces(code: str) -> bool:
    depth = 0
    for ch in code:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def validate_gdscript(code: str) -> Dict[str, Any]:
    """Fallback without Godot: basic structure + brace balance."""
    errors: List[Dict[str, Any]] = []
    stripped = code.strip()
    if not stripped:
        return {"valid": False, "errors": [{"line": 1, "column": 0, "message": "empty"}], "score": 0.0}

    if not _gdscript_balance_braces(code):
        errors.append({"line": 0, "column": 0, "message": "unbalanced braces"})

    if not re.search(r"\bfunc\s+\w+\s*\(", stripped):
        errors.append({"line": 1, "column": 0, "message": "no func definitions found (heuristic)"})

    ok = len(errors) == 0
    score = 10.0 if ok else max(2.0, 10.0 - 3.0 * len(errors))
    return {"valid": ok, "errors": errors, "score": score}
