from __future__ import annotations

from collections import deque

import main
from fastapi.testclient import TestClient


def test_health():
    assert TestClient(main.app).get("/health").status_code == 200


def test_budget_and_record(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)
    assert c.get("/budget").status_code == 200
    r = c.post(
        "/cost/record",
        json={"service": "test", "operation": "x", "actual_cost_eur": 1.0},
    )
    assert r.status_code == 200


def test_429_when_over_cap(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 0.01)
    c = TestClient(main.app)
    c.post("/cost/record", json={"service": "a", "actual_cost_eur": 0.01})
    r = c.post("/cost/check", json={"estimated_cost_eur": 1.0})
    assert r.status_code == 429
