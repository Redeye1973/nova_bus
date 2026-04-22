"""Tests for Agent 29."""
from __future__ import annotations

import os

from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.pop("COST_GUARD_URL", None)
os.environ.pop("ELEVENLABS_API_KEY", None)

import main


def test_health():
    c = TestClient(main.app)
    assert c.get("/health").status_code == 200


def test_tts_dry_run_after_register():
    c = TestClient(main.app)
    assert c.post("/voices/register", json={"voice_id": "v1", "label": "Test"}).status_code == 200
    r = c.post("/tts", json={"voice_id": "v1", "text": "Hello NOVA"})
    assert r.status_code == 200
    assert r.json()["status"] == "dry_run"


def test_tts_blocked_when_cost_guard_denies(monkeypatch):
    def _deny(_e: float) -> None:
        raise HTTPException(429, detail={"error": "would_exceed_daily_cap"})

    monkeypatch.setattr(main, "_cost_precheck", _deny)
    monkeypatch.setenv("COST_GUARD_URL", "http://fake-cost-guard:8116")
    c = TestClient(main.app)
    c.post("/voices/register", json={"voice_id": "v2", "label": "T2"})
    r = c.post("/tts", json={"voice_id": "v2", "text": "blocked"})
    assert r.status_code == 429
