"""NOVA v2 Agent 16 — Cost Guard (in-memory daily cap; Postgres DDL in scripts/)."""
from __future__ import annotations

import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DAILY_CAP_EUR = float(os.getenv("COST_GUARD_DAILY_CAP_EUR", "5.0"))

app = FastAPI(title="NOVA v2 Agent 16 - Cost Guard", version="0.1.0")

LOG: Deque[Dict[str, Any]] = deque(maxlen=10_000)


def _day_key(ts: float | None = None) -> str:
    t = datetime.fromtimestamp(ts or time.time(), tz=timezone.utc).date().isoformat()
    return t


def _spent_today() -> float:
    today = _day_key()
    return sum(float(e.get("actual_cost_eur") or 0) for e in LOG if e.get("day") == today)


class CostRecord(BaseModel):
    service: str = Field(..., min_length=1)
    operation: Optional[str] = None
    estimated_cost_eur: Optional[float] = None
    actual_cost_eur: float = 0.0
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CostCheck(BaseModel):
    estimated_cost_eur: float = Field(..., ge=0.0)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "16_cost_guard", "version": "0.1.0"}


@app.get("/budget")
def budget() -> Dict[str, Any]:
    spent = _spent_today()
    return {
        "day": _day_key(),
        "daily_cap_eur": DAILY_CAP_EUR,
        "spent_eur": round(spent, 4),
        "remaining_eur": round(max(0.0, DAILY_CAP_EUR - spent), 4),
        "entries_today": sum(1 for e in LOG if e.get("day") == _day_key()),
    }


@app.post("/cost/record")
def cost_record(rec: CostRecord) -> Dict[str, Any]:
    spent = _spent_today()
    add = float(rec.actual_cost_eur or 0.0)
    if spent + add > DAILY_CAP_EUR + 1e-9:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "daily_budget_exceeded",
                "spent_eur": spent,
                "cap_eur": DAILY_CAP_EUR,
                "would_add": add,
            },
        )
    row = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "day": _day_key(),
        "service": rec.service,
        "operation": rec.operation,
        "estimated_cost_eur": rec.estimated_cost_eur,
        "actual_cost_eur": add,
        "agent_id": rec.agent_id,
        "metadata": rec.metadata or {},
    }
    LOG.append(row)
    return {"recorded": True, "id": row["id"], "spent_after_eur": round(_spent_today(), 4)}


@app.post("/cost/check")
def cost_check(chk: CostCheck) -> Dict[str, Any]:
    spent = _spent_today()
    if spent + float(chk.estimated_cost_eur) > DAILY_CAP_EUR + 1e-9:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "would_exceed_daily_cap",
                "spent_eur": spent,
                "cap_eur": DAILY_CAP_EUR,
                "estimate_eur": chk.estimated_cost_eur,
            },
        )
    return {"ok": True, "remaining_eur": round(DAILY_CAP_EUR - spent, 4)}


@app.get("/cost/log")
def cost_log(limit: int = 50) -> Dict[str, Any]:
    lim = max(1, min(500, limit))
    items: List[Dict[str, Any]] = list(LOG)[-lim:]
    return {"count": len(items), "items": items}


@app.get("/cost/daily/{date}")
def cost_daily(date: str) -> Dict[str, Any]:
    entries = [e for e in LOG if e.get("day") == date]
    by_service: Dict[str, float] = {}
    for e in entries:
        svc = e.get("service", "unknown")
        by_service[svc] = by_service.get(svc, 0.0) + float(e.get("actual_cost_eur", 0))
    return {
        "date": date,
        "total_eur": round(sum(by_service.values()), 4),
        "entries": len(entries),
        "by_service": {k: round(v, 4) for k, v in sorted(by_service.items())},
    }


@app.get("/cost/summary")
def cost_summary(days: int = 7) -> Dict[str, Any]:
    day_totals: Dict[str, float] = {}
    day_counts: Dict[str, int] = {}
    for e in LOG:
        d = e.get("day", "")
        day_totals[d] = day_totals.get(d, 0.0) + float(e.get("actual_cost_eur", 0))
        day_counts[d] = day_counts.get(d, 0) + 1
    sorted_days = sorted(day_totals.keys(), reverse=True)[:days]
    total = sum(day_totals.get(d, 0) for d in sorted_days)
    avg = total / max(len(sorted_days), 1)
    return {
        "period_days": len(sorted_days),
        "total_eur": round(total, 4),
        "daily_average_eur": round(avg, 4),
        "forecast_30d_eur": round(avg * 30, 2),
        "daily_cap_eur": DAILY_CAP_EUR,
        "days": [
            {"date": d, "total_eur": round(day_totals[d], 4), "entries": day_counts.get(d, 0)}
            for d in sorted_days
        ],
    }


@app.get("/cost/by_agent")
def cost_by_agent() -> Dict[str, Any]:
    by_agent: Dict[str, float] = {}
    by_agent_count: Dict[str, int] = {}
    for e in LOG:
        aid = e.get("agent_id") or "unknown"
        by_agent[aid] = by_agent.get(aid, 0.0) + float(e.get("actual_cost_eur", 0))
        by_agent_count[aid] = by_agent_count.get(aid, 0) + 1
    ranked = sorted(by_agent.items(), key=lambda x: x[1], reverse=True)
    return {
        "agents": [
            {"agent_id": k, "total_eur": round(v, 4), "calls": by_agent_count.get(k, 0)}
            for k, v in ranked
        ]
    }


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    action = str((body or {}).get("action", "budget")).lower()
    if action == "budget":
        return budget()
    if action == "log":
        return cost_log(int((body or {}).get("limit", 50)))
    if action == "summary":
        return cost_summary(int((body or {}).get("days", 7)))
    if action == "by_agent":
        return cost_by_agent()
    return {"error": "unknown_action", "valid": ["budget", "log", "summary", "by_agent"]}
