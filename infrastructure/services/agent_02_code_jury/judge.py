"""Aggregate jury scores into verdict."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def verdict_from_scores(
    syntax: Dict[str, Any],
    complexity: Dict[str, Any],
    style: Dict[str, Any],
    security: Dict[str, Any],
) -> Tuple[str, List[str], float]:
    scores = [
        float(syntax.get("score", 0)),
        float(complexity.get("score", 0)),
        float(style.get("score", 0)),
        float(security.get("score", 0)),
    ]
    avg = sum(scores) / 4.0
    feedback: List[str] = []
    if syntax.get("score", 10) < 6:
        feedback.append("syntax_needs_fix")
    if complexity.get("score", 10) < 6:
        feedback.append("reduce_complexity")
    if style.get("score", 10) < 6:
        feedback.append("style_conformance")
    if security.get("score", 10) < 6:
        feedback.append("security_issues")

    if avg >= 7.5:
        v = "accept"
    elif avg >= 5.0:
        v = "revise"
    else:
        v = "reject"
    return v, feedback, round(avg, 3)
