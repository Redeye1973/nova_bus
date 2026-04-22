"""Tests for Agent 33 stub."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health():
    assert TestClient(main.app).get("/health").json()["mode"] == "stub"


def test_walkthrough_503():
    assert TestClient(main.app).post("/walkthrough").status_code == 503
