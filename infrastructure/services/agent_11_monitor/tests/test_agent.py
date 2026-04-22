"""Unit tests for Agent 11 Monitor (offline; targets list is overridable)."""
from __future__ import annotations

import re

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "11_monitor"


def test_invoke_sweep_with_explicit_targets_offline():
    c = TestClient(main.app)
    r = c.post("/invoke", json={
        "action": "sweep",
        "targets": [
            {"name": "fake_a", "url": "http://127.0.0.1:1/health"},
            {"name": "fake_b", "url": "http://127.0.0.1:2/health"},
        ],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["targets_checked"] == 2
    assert data["down"] == 2
    assert data["up"] == 0
    assert len(data["alerts"]) == 2
    assert all(a["severity"] == "critical" for a in data["alerts"])


def test_alerts_after_sweep():
    c = TestClient(main.app)
    c.post("/invoke", json={
        "action": "sweep",
        "targets": [{"name": "fake_x", "url": "http://127.0.0.1:1/health"}],
    })
    r = c.get("/alerts")
    assert r.status_code == 200
    data = r.json()
    assert "timestamp" in data
    assert any(a["service"] == "fake_x" for a in data["alerts"])


def test_feedback_roundtrip():
    c = TestClient(main.app)
    r = c.post("/feedback", json={"message": "hello", "source": "unit"})
    assert r.status_code == 200
    r2 = c.get("/feedback/recent?limit=5")
    assert r2.json()["count"] >= 1


def test_pdok_delta_stub():
    r = TestClient(main.app).get("/pdok-weekly-delta")
    assert r.status_code == 200
    assert r.json()["status"] == "stub"


def test_metrics_prometheus_text():
    c = TestClient(main.app)
    c.post("/invoke", json={
        "action": "sweep",
        "targets": [{"name": "fake_y", "url": "http://127.0.0.1:1/health"}],
    })
    r = c.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "monitor_sweeps_total" in text
    assert "monitor_target_down_total" in text
    assert re.search(r'monitor_target_latency_ms\{target="fake_y"\}', text)
