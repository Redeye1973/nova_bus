"""Agent 10 — Game Balance Jury."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

from difficulty_curve_analyzer import review_difficulty
from economy_validator import review_economy
from judge_balance import verdict
from stat_progression_checker import review_stats

app = FastAPI(title="NOVA v2 Agent 10 Game Balance Jury", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "10_game_balance", "version": "0.1.0"}


@app.post("/review/stats")
def review_stats_ep(payload: Dict[str, Any]) -> Dict[str, Any]:
    return review_stats(payload)


@app.post("/review/economy")
def review_economy_ep(payload: Dict[str, Any]) -> Dict[str, Any]:
    return review_economy(payload)


@app.post("/review/difficulty_curve")
def review_diff_ep(payload: Dict[str, Any]) -> Dict[str, Any]:
    return review_difficulty(payload)


@app.post("/review")
def review_all(payload: Dict[str, Any]) -> Dict[str, Any]:
    st = review_stats(payload)
    ec = review_economy(payload)
    diff = review_difficulty(payload)
    v, avg, fb = verdict(st, ec, diff)
    return {
        "jury": {"stats": st, "economy": ec, "difficulty": diff},
        "verdict": v,
        "average_score": avg,
        "feedback": fb,
    }
