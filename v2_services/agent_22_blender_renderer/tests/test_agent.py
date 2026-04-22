"""Tests for Agent 22 stub."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health_pending_bridge():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "pending_full_bridge"


def test_render_503():
    c = TestClient(main.app)
    r = c.post("/render")
    assert r.status_code == 503
