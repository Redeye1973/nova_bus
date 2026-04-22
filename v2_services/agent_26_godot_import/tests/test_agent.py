"""Tests for Agent 26 stub."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health():
    assert TestClient(main.app).get("/health").json()["agent"] == "26_godot_import"


def test_import_503():
    assert TestClient(main.app).post("/import").status_code == 503
