"""NOVA v2 Agent 26 — Godot Import (stub until bridge)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException

app = FastAPI(title="NOVA v2 Agent 26 - Godot Import", version="0.1.0-stub")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "pending_full_bridge", "mode": "stub", "agent": "26_godot_import"}


@app.post("/import")
def import_assets() -> None:
    raise HTTPException(
        status_code=503,
        detail="Bridge not fully wired. See session 08+.",
    )


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "pending_full_bridge", "agent": "26"}
