"""Tests for Agent 27."""
from __future__ import annotations

import os

os.environ.pop("COST_GUARD_URL", None)
os.environ.pop("FLUX_API_KEY", None)
os.environ.pop("FLUX_API_URL", None)

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["agent"] == "27_storyboard"


def test_storyboard_dry_run():
    c = TestClient(main.app)
    r = c.post(
        "/storyboard/generate",
        json={"scene_description": "A corridor on a derelict station", "panel_count": 2},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "dry_run_no_flux_credentials"
    assert len(data["panels"]) == 2
