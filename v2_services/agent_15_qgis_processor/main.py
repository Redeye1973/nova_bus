"""NOVA v2 Agent 15 — QGIS Processor (pending full bridge)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="NOVA v2 Agent 15 - QGIS Processor", version="0.1.0-pending")


class ProcessBody(BaseModel):
    operation: str = "buffer"
    geojson: Optional[Dict[str, Any]] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "15_qgis_processor", "mode": "pending_full_bridge"}


@app.post("/process")
def process(_body: ProcessBody) -> Dict[str, Any]:
    return {
        "status": "pending_full_bridge",
        "note": "QGIS headless execution will route via nova_host_bridge (qgis).",
    }


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(body, dict):
        return process(ProcessBody.model_validate(body))
    return {"error": "expected_object"}
