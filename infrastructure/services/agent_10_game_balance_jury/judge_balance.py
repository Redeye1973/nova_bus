"""Aggregate jury scores."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def verdict(stats: Dict[str, Any], economy: Dict[str, Any], difficulty: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    scores = [
        float(stats.get("score", 0)),
        float(economy.get("score", 0)),
        float(difficulty.get("score", 0)),
    ]
    avg = sum(scores) / 3.0
    fb: List[str] = []
    if not stats.get("valid", True):
        fb.append("stats")
    if not economy.get("valid", True):
        fb.append("economy")
    if not difficulty.get("valid", True):
        fb.append("difficulty")

    if avg >= 7.5:
        v = "accept"
    elif avg >= 5.0:
        v = "revise"
    else:
        v = "reject"
    return v, round(avg, 3), fb
