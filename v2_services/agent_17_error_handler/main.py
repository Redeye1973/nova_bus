"""NOVA v2 Agent 17 — Error Handler.

Pragmatic POC scope (no Postgres, no Telegram dependency):
- Pattern-library classification (regex) loaded from patterns.yaml
- In-memory ledger of errors and repair attempts
- Exponential-backoff retry advisor
- Auto "resolve" action that writes a repair record

Endpoints:
- GET  /health
- POST /error/report      {service, severity?, message, stack_trace?, context?, correlation_id?}
- POST /error/resolve     {error_id, action, success?, notes?}
- GET  /repair/history    [?service=..&since_minutes=..]
- POST /invoke            {action: report|resolve|history|patterns, ...}
"""
from __future__ import annotations

import logging
import os
import re
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("error_handler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

PATTERNS_PATH = Path(os.getenv("ERROR_PATTERNS_PATH", "/app/patterns.yaml"))
HISTORY_LIMIT = int(os.getenv("ERROR_HISTORY_LIMIT", "500"))
RETRY_BASE_S = float(os.getenv("ERROR_RETRY_BASE_S", "2"))
RETRY_MAX_S = float(os.getenv("ERROR_RETRY_MAX_S", "300"))


def _load_patterns() -> List[Dict[str, Any]]:
    if not PATTERNS_PATH.is_file():
        logger.warning("patterns file missing: %s", PATTERNS_PATH)
        return []
    try:
        data = yaml.safe_load(PATTERNS_PATH.read_text(encoding="utf-8")) or {}
        items = data.get("patterns", []) or []
        compiled = []
        for it in items:
            try:
                rx = re.compile(it["match"], re.IGNORECASE | re.DOTALL)
            except re.error as e:
                logger.warning("bad regex for %s: %s", it.get("name"), e)
                continue
            compiled.append({**it, "_rx": rx})
        return compiled
    except (yaml.YAMLError, OSError) as e:
        logger.error("cannot load patterns: %s", e)
        return []


PATTERNS = _load_patterns()
ERRORS: Dict[str, Dict[str, Any]] = {}
HISTORY: Deque[Dict[str, Any]] = deque(maxlen=HISTORY_LIMIT)


class ErrorReport(BaseModel):
    service: str = Field(..., min_length=1)
    severity: Optional[str] = None
    message: str = Field(..., min_length=1)
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class ErrorResolve(BaseModel):
    error_id: str
    action: str
    success: bool = True
    notes: Optional[str] = None


def _classify(report: ErrorReport) -> Dict[str, Any]:
    blob = "\n".join(filter(None, [report.message, report.stack_trace or ""]))
    for pat in PATTERNS:
        if pat["_rx"].search(blob):
            sev = pat.get("severity") or report.severity or "medium"
            return {
                "category": pat["name"],
                "severity_calibrated": sev,
                "retry_able": bool(pat.get("retry_able", False)),
                "fix": pat.get("fix"),
                "match_source": "pattern_library",
            }
    return {
        "category": "unknown",
        "severity_calibrated": report.severity or "medium",
        "retry_able": False,
        "fix": None,
        "match_source": "fallback",
    }


def _retry_plan(category: str, attempt: int) -> Dict[str, Any]:
    delay = min(RETRY_MAX_S, RETRY_BASE_S * (2 ** max(0, attempt - 1)))
    return {"attempt": attempt, "delay_seconds": round(delay, 2), "strategy": "exponential_backoff"}


app = FastAPI(title="NOVA v2 Agent 17 - Error Handler", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "agent": "17_error_handler",
        "version": "0.1.0",
        "pattern_count": len(PATTERNS),
    }


@app.post("/error/report")
def error_report(report: ErrorReport) -> Dict[str, Any]:
    error_id = str(uuid.uuid4())
    now = time.time()
    classification = _classify(report)
    record = {
        "error_id": error_id,
        "received_at": now,
        "service": report.service,
        "severity_input": report.severity,
        "message": report.message,
        "stack_trace": report.stack_trace,
        "context": report.context or {},
        "correlation_id": report.correlation_id,
        "classification": classification,
        "attempts": 0,
        "resolved": False,
    }
    ERRORS[error_id] = record
    HISTORY.append({
        "kind": "report",
        "error_id": error_id,
        "service": report.service,
        "category": classification["category"],
        "severity": classification["severity_calibrated"],
        "timestamp": now,
    })
    response: Dict[str, Any] = {
        "error_id": error_id,
        "classification": classification,
    }
    if classification["retry_able"]:
        record["attempts"] = 1
        response["retry"] = _retry_plan(classification["category"], record["attempts"])
    if classification["fix"] and not classification["retry_able"]:
        response["suggested_fix"] = classification["fix"]
    return response


@app.post("/error/resolve")
def error_resolve(req: ErrorResolve) -> Dict[str, Any]:
    rec = ERRORS.get(req.error_id)
    if rec is None:
        raise HTTPException(404, detail=f"unknown error_id:{req.error_id}")
    now = time.time()
    rec["resolved"] = True
    rec["resolved_at"] = now
    rec["resolved_action"] = req.action
    rec["resolved_success"] = req.success
    rec["resolved_notes"] = req.notes
    HISTORY.append({
        "kind": "resolve",
        "error_id": req.error_id,
        "service": rec["service"],
        "action": req.action,
        "success": req.success,
        "timestamp": now,
    })
    return {
        "error_id": req.error_id,
        "resolved": True,
        "success": req.success,
        "action": req.action,
        "service": rec["service"],
    }


@app.get("/repair/history")
def repair_history(service: Optional[str] = None, since_minutes: Optional[float] = None) -> Dict[str, Any]:
    cutoff = time.time() - since_minutes * 60.0 if since_minutes else None
    items: List[Dict[str, Any]] = []
    for rec in list(HISTORY):
        if service and rec.get("service") != service:
            continue
        if cutoff is not None and rec.get("timestamp", 0) < cutoff:
            continue
        items.append(rec)
    return {
        "count": len(items),
        "history_limit": HISTORY_LIMIT,
        "items": items,
        "outstanding": [
            {"error_id": e_id, "service": rec["service"], "category": rec["classification"]["category"]}
            for e_id, rec in ERRORS.items() if not rec.get("resolved")
        ],
    }


class InvokeBody(BaseModel):
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    service: Optional[str] = None
    since_minutes: Optional[float] = None


@app.post("/invoke")
def invoke(body: InvokeBody) -> Dict[str, Any]:
    action = (body.action or "report").lower()
    payload = body.payload or {}

    if action == "report":
        if "message" not in payload or "service" not in payload:
            payload = {
                "service": payload.get("service") or "unknown",
                "message": payload.get("message") or "no message provided",
                **payload,
            }
        try:
            report = ErrorReport(**payload)
        except Exception as e:
            raise HTTPException(400, detail=f"invalid_payload:{e}")
        return error_report(report)

    if action == "resolve":
        try:
            req = ErrorResolve(**payload)
        except Exception as e:
            raise HTTPException(400, detail=f"invalid_payload:{e}")
        return error_resolve(req)

    if action == "history":
        return repair_history(service=body.service, since_minutes=body.since_minutes)

    if action == "patterns":
        return {
            "count": len(PATTERNS),
            "patterns": [
                {k: v for k, v in p.items() if k != "_rx"}
                for p in PATTERNS
            ],
        }

    return {
        "error": f"unknown_action:{action}",
        "valid_actions": ["report", "resolve", "history", "patterns"],
    }
