"""NOVA v2 Agent 31 — QGIS Analysis (stub until bridge)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException

app = FastAPI(title="NOVA v2 Agent 31 - QGIS Analysis", version="0.1.0-stub")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "pending_full_bridge", "mode": "stub", "agent": "31_qgis_analysis"}


@app.post("/analyze")
def analyze() -> None:
    raise HTTPException(
        status_code=503,
        detail="Bridge not fully wired. See session 08+.",
    )


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "pending_full_bridge", "agent": "31"}
