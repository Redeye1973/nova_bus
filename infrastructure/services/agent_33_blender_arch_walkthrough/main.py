"""NOVA v2 Agent 33 — Blender architecture walkthrough (stub until bridge adapters)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException

app = FastAPI(title="NOVA v2 Agent 33 - Blender Arch Walkthrough", version="0.1.0-stub")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "pending_full_bridge", "mode": "stub", "agent": "33_blender_arch_walkthrough"}


@app.post("/walkthrough")
def walkthrough() -> None:
    raise HTTPException(
        status_code=503,
        detail="Bridge not fully wired. See session 08+.",
    )


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "pending_full_bridge", "agent": "33"}
