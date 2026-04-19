"""Difficulty curve — numpy/scipy light (POC)."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


def review_difficulty(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = payload.get("difficulty_curve") or payload.get("curve") or payload.get("values")
    if raw is None:
        return {"score": 4.0, "valid": False, "issues": ["missing_curve"], "smoothness": None}

    if not isinstance(raw, list) or len(raw) < 3:
        return {"score": 3.0, "valid": False, "issues": ["curve_too_short"], "smoothness": None}

    y = np.array([float(x) for x in raw], dtype=float)
    if np.any(y < 0):
        return {"score": 2.0, "valid": False, "issues": ["negative_difficulty"], "smoothness": None}

    # second-difference as smoothness proxy (lower = smoother steps)
    d2 = np.diff(y, n=2)
    rough = float(np.mean(np.abs(d2))) if len(d2) else 0.0

    # expect gentle increase for shmup-style
    gradient = np.diff(y)
    monotonic = bool(np.all(gradient >= -1e-9))

    issues: List[str] = []
    if rough > (np.mean(y) * 0.5 + 1e-6):
        issues.append("spiky_curve")
    if not monotonic:
        issues.append("non_increasing_difficulty")

    score = 10.0 - min(5.0, rough * 2.0) - (2.0 if not monotonic else 0.0)
    if issues:
        score -= 1.0 * len(issues)
    score = float(max(0.0, min(10.0, score)))

    return {
        "score": round(score, 2),
        "valid": len(issues) == 0,
        "issues": issues,
        "smoothness_metric": round(rough, 4),
        "monotonic_increasing": monotonic,
    }
