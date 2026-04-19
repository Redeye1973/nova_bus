"""Economy validator (POC)."""
from __future__ import annotations

from typing import Any, Dict, List


def review_economy(payload: Dict[str, Any]) -> Dict[str, Any]:
    income = float(payload.get("income_per_hour", payload.get("income", 0)) or 0)
    spend = float(payload.get("spend_per_hour", payload.get("spend", 0)) or 0)
    issues: List[str] = []

    if income < 0 or spend < 0:
        issues.append("negative_values")

    if income == 0 and spend == 0:
        return {"score": 5.0, "valid": True, "issues": ["empty_economy"], "ratio": None}

    if spend > income * 2 and income > 0:
        issues.append("spend_much_higher_than_income")

    ratio = spend / income if income else None
    score = 10.0
    if issues:
        score -= 2.5 * len(issues)
    if ratio and ratio > 3:
        score -= 2.0
    score = max(0.0, min(10.0, score))

    return {
        "score": round(score, 2),
        "valid": len(issues) == 0,
        "issues": issues,
        "ratio_spend_income": round(ratio, 4) if ratio is not None else None,
    }
