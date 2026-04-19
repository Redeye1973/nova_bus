"""Heuristic stat progression checks (POC)."""
from __future__ import annotations

from typing import Any, Dict, List


def review_stats(payload: Dict[str, Any]) -> Dict[str, Any]:
    curve = payload.get("stat_curve") or payload.get("stats") or payload.get("values")
    if curve is None:
        return {"score": 4.0, "valid": False, "issues": ["missing_stat_curve"], "notes": "pass stat_curve: number[]"}

    if not isinstance(curve, list) or len(curve) < 2:
        return {"score": 3.0, "valid": False, "issues": ["curve_too_short"], "notes": "need >=2 points"}

    nums = [float(x) for x in curve]
    mono_up = all(nums[i] <= nums[i + 1] + 1e-9 for i in range(len(nums) - 1))
    mono_down = all(nums[i] >= nums[i + 1] - 1e-9 for i in range(len(nums) - 1))

    issues: List[str] = []
    if not mono_up and not mono_down:
        issues.append("non_monotonic_progression")

    span = max(nums) - min(nums)
    if span <= 0:
        issues.append("flat_curve")

    score = 10.0
    if issues:
        score -= 3.0 * len(issues)
    if not mono_up and not mono_down:
        score -= 2.0
    score = max(0.0, min(10.0, score))

    return {
        "score": round(score, 2),
        "valid": len(issues) == 0,
        "issues": issues,
        "monotonic_increasing": mono_up,
        "monotonic_decreasing": mono_down,
    }
