"""NOVA v2 Agent 16 — Cost Guard (daily cap + pipeline budgets)."""
from __future__ import annotations

import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

import httpx
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DAILY_CAP_EUR = float(os.getenv("COST_GUARD_DAILY_CAP_EUR", "5.0"))
DATABASE_URL = os.getenv("DATABASE_URL", "")
NOTIFICATION_HUB_URL = os.getenv("NOTIFICATION_HUB_URL", "http://nova-v2-notification-hub:8061")

app = FastAPI(title="NOVA v2 Agent 16 - Cost Guard", version="0.2.0")


def _get_db():
    if not DATABASE_URL:
        return None
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception:
        return None

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


class BudgetCheckBody(BaseModel):
    pipeline_id: str
    pipeline_type: str


class BudgetConsumeBody(BaseModel):
    pipeline_id: str
    pipeline_type: str
    cost: float = 0.0
    api_calls: int = 0
    gpu_seconds: int = 0


@app.post("/budget/check")
def budget_check(body: BudgetCheckBody) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"ok": True, "reason": "no_db_fallback_allow"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM pipeline_budgets WHERE pipeline_type = %s", (body.pipeline_type,))
            budget_row = cur.fetchone()
            if not budget_row:
                return {"ok": True, "reason": "no_budget_defined", "pipeline_type": body.pipeline_type}

            cur.execute("SELECT * FROM pipeline_usage WHERE pipeline_id = %s", (body.pipeline_id,))
            usage = cur.fetchone()

            remaining = {
                "cost_usd": float(budget_row["max_cost_usd"]) - float(usage["cost_usd"] if usage else 0),
                "api_calls": int(budget_row["max_api_calls"]) - int(usage["api_calls"] if usage else 0),
            }
            pct = (float(usage["cost_usd"]) / float(budget_row["max_cost_usd"]) * 100) if usage and float(budget_row["max_cost_usd"]) > 0 else 0

            return {
                "ok": remaining["cost_usd"] > 0,
                "pipeline_id": body.pipeline_id,
                "pipeline_type": body.pipeline_type,
                "used_pct": round(pct, 1),
                "remaining": remaining,
                "budget": {k: str(v) for k, v in budget_row.items()},
            }
    finally:
        conn.close()


@app.post("/budget/consume")
async def budget_consume(body: BudgetConsumeBody) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"ok": True, "reason": "no_db_fallback_allow"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM pipeline_usage WHERE pipeline_id = %s", (body.pipeline_id,))
            usage = cur.fetchone()

            if usage:
                cur.execute(
                    """UPDATE pipeline_usage
                       SET cost_usd = cost_usd + %s, api_calls = api_calls + %s,
                           gpu_seconds = gpu_seconds + %s, last_updated = NOW()
                       WHERE pipeline_id = %s RETURNING *""",
                    (body.cost, body.api_calls, body.gpu_seconds, body.pipeline_id),
                )
            else:
                cur.execute(
                    """INSERT INTO pipeline_usage (pipeline_id, pipeline_type, cost_usd, api_calls, gpu_seconds)
                       VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                    (body.pipeline_id, body.pipeline_type, body.cost, body.api_calls, body.gpu_seconds),
                )
            row = cur.fetchone()
            conn.commit()

            cur.execute("SELECT * FROM pipeline_budgets WHERE pipeline_type = %s", (body.pipeline_type,))
            budget_row = cur.fetchone()

            if budget_row:
                pct = float(row["cost_usd"]) / float(budget_row["max_cost_usd"]) * 100 if float(budget_row["max_cost_usd"]) > 0 else 0
                threshold = int(budget_row.get("notify_threshold_pct", 80))

                if pct >= 100:
                    try:
                        async with httpx.AsyncClient() as client:
                            await client.post(f"{NOTIFICATION_HUB_URL}/notify", json={
                                "severity": "critical",
                                "title": f"Pipeline budget EXCEEDED: {body.pipeline_type}",
                                "detail": f"Pipeline {body.pipeline_id} used {pct:.0f}% of budget",
                                "source": "agent_16_cost_guard",
                            }, timeout=5)
                    except Exception:
                        pass
                    return {"ok": False, "blocked": True, "used_pct": round(pct, 1)}
                elif pct >= threshold:
                    try:
                        async with httpx.AsyncClient() as client:
                            await client.post(f"{NOTIFICATION_HUB_URL}/notify", json={
                                "severity": "warning",
                                "title": f"Pipeline budget warning: {body.pipeline_type}",
                                "detail": f"Pipeline {body.pipeline_id} used {pct:.0f}% of budget",
                                "source": "agent_16_cost_guard",
                            }, timeout=5)
                    except Exception:
                        pass

            return {"ok": True, "pipeline_id": body.pipeline_id, "consumed": {
                "cost": body.cost, "api_calls": body.api_calls, "gpu_seconds": body.gpu_seconds
            }}
    finally:
        conn.close()


@app.get("/budget/status/{pipeline_id}")
def budget_status(pipeline_id: str) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"error": "database_unavailable"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM pipeline_usage WHERE pipeline_id = %s", (pipeline_id,))
            usage = cur.fetchone()
            if not usage:
                return {"pipeline_id": pipeline_id, "usage": None}
            cur.execute("SELECT * FROM pipeline_budgets WHERE pipeline_type = %s", (usage["pipeline_type"],))
            budget_row = cur.fetchone()
            return {
                "pipeline_id": pipeline_id,
                "pipeline_type": usage["pipeline_type"],
                "usage": {k: str(v) for k, v in usage.items() if k != "id"},
                "budget": {k: str(v) for k, v in budget_row.items()} if budget_row else None,
            }
    finally:
        conn.close()


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
