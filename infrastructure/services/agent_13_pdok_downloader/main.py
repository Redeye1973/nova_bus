"""POC stub — PDOK Downloader (Agent 13). Replace with full implementation."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

app = FastAPI(title="NOVA v2 Agent 13", version="0.0.1-poc")

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "13", "mode": "poc_stub"}

@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "agent": "13",
        "agent_name": "PDOK Downloader",
        "received_keys": list(body.keys()) if isinstance(body, dict) else [],
        "note": "POC stub — upgrade per spec",
    }
