"""Tests for Agent 25 stub."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health():
    assert TestClient(main.app).get("/health").json()["mode"] == "stub"


def test_assemble_503():
    assert TestClient(main.app).post("/assemble").status_code == 503
