"""Tests for Agent 35 stub."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health():
    assert TestClient(main.app).get("/health").json()["status"] == "pending_full_bridge"


def test_process_503():
    assert TestClient(main.app).post("/process").status_code == 503
