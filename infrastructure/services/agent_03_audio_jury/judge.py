"""Aggregate jury scores → verdict (POC rubric)."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Tuple

Verdict = Literal["accept", "revise", "reject"]


def verdict_from_members(members: List[Dict[str, Any]]) -> Tuple[Verdict, float, List[str]]:
    scores: List[float] = []
    notes: List[str] = []
    for m in members:
        s = float(m.get("score", 0.0))
        scores.append(s)
        if m.get("issues"):
            notes.extend(str(i) for i in m["issues"])
        if m.get("warnings"):
            notes.extend(str(w) for w in m["warnings"])
    avg = sum(scores) / max(len(scores), 1)
    if avg >= 7.0 and not any("clipping_detected" in n for n in notes):
        return "accept", avg, notes
    if avg >= 4.5:
        return "revise", avg, notes
    return "reject", avg, notes
