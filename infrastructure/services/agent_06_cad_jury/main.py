"""POC stub — CAD Jury (Agent 06). Replace with full implementation."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

app = FastAPI(title="NOVA v2 Agent 06", version="0.0.1-poc")

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "06", "mode": "poc_stub"}

@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "agent": "06",
        "agent_name": "CAD Jury",
        "received_keys": list(body.keys()) if isinstance(body, dict) else [],
        "note": "POC stub — upgrade per spec",
    }
