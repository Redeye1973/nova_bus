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


# ---------------------------------------------------------------------------
# NEW: /cost/daily/{date} tests
# ---------------------------------------------------------------------------


def test_cost_daily_returns_breakdown_by_service(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)

    c.post("/cost/record", json={"service": "openai", "actual_cost_eur": 1.5})
    c.post("/cost/record", json={"service": "openai", "actual_cost_eur": 0.5})
    c.post("/cost/record", json={"service": "replicate", "actual_cost_eur": 2.0})

    today = main._day_key()
    r = c.get(f"/cost/daily/{today}")
    assert r.status_code == 200
    body = r.json()
    assert body["date"] == today
    assert body["entries"] == 3
    assert body["total_eur"] == 4.0
    assert body["by_service"]["openai"] == 2.0
    assert body["by_service"]["replicate"] == 2.0


def test_cost_daily_empty_date_returns_zero(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    c = TestClient(main.app)
    r = c.get("/cost/daily/2000-01-01")
    assert r.status_code == 200
    body = r.json()
    assert body["total_eur"] == 0.0
    assert body["entries"] == 0
    assert body["by_service"] == {}


# ---------------------------------------------------------------------------
# NEW: /cost/summary tests
# ---------------------------------------------------------------------------


def test_cost_summary_aggregates_correctly(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)

    c.post("/cost/record", json={"service": "svc_a", "actual_cost_eur": 3.0})
    c.post("/cost/record", json={"service": "svc_b", "actual_cost_eur": 7.0})

    r = c.get("/cost/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_eur"] == 10.0
    assert body["period_days"] >= 1
    assert body["daily_average_eur"] == body["total_eur"] / body["period_days"]
    assert body["daily_cap_eur"] == 100.0
    assert len(body["days"]) >= 1

    today_entry = body["days"][0]
    assert today_entry["total_eur"] == 10.0
    assert today_entry["entries"] == 2


def test_cost_summary_empty_log(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    c = TestClient(main.app)
    r = c.get("/cost/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_eur"] == 0.0
    assert body["period_days"] == 0
    assert body["days"] == []


def test_cost_summary_respects_days_param(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)
    c.post("/cost/record", json={"service": "x", "actual_cost_eur": 1.0})
    r = c.get("/cost/summary", params={"days": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["period_days"] <= 1


def test_cost_summary_includes_forecast(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)
    c.post("/cost/record", json={"service": "x", "actual_cost_eur": 2.0})
    r = c.get("/cost/summary")
    body = r.json()
    assert body["forecast_30d_eur"] == round(body["daily_average_eur"] * 30, 2)


# ---------------------------------------------------------------------------
# NEW: /cost/by_agent tests
# ---------------------------------------------------------------------------


def test_cost_by_agent_groups_correctly(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)

    c.post("/cost/record", json={"service": "openai", "actual_cost_eur": 1.0, "agent_id": "agent_14"})
    c.post("/cost/record", json={"service": "openai", "actual_cost_eur": 2.0, "agent_id": "agent_14"})
    c.post("/cost/record", json={"service": "replicate", "actual_cost_eur": 5.0, "agent_id": "agent_22"})

    r = c.get("/cost/by_agent")
    assert r.status_code == 200
    body = r.json()
    agents = {a["agent_id"]: a for a in body["agents"]}

    assert agents["agent_14"]["total_eur"] == 3.0
    assert agents["agent_14"]["calls"] == 2
    assert agents["agent_22"]["total_eur"] == 5.0
    assert agents["agent_22"]["calls"] == 1
    assert body["agents"][0]["agent_id"] == "agent_22"  # ranked by cost desc


def test_cost_by_agent_unknown_when_no_agent_id(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)

    c.post("/cost/record", json={"service": "svc", "actual_cost_eur": 0.5})
    r = c.get("/cost/by_agent")
    body = r.json()
    assert any(a["agent_id"] == "unknown" for a in body["agents"])


def test_cost_by_agent_empty_log(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    c = TestClient(main.app)
    r = c.get("/cost/by_agent")
    assert r.status_code == 200
    assert r.json()["agents"] == []


# ---------------------------------------------------------------------------
# NEW: integration — record + daily + summary + by_agent roundtrip
# ---------------------------------------------------------------------------


def test_full_cost_roundtrip(monkeypatch):
    monkeypatch.setattr(main, "LOG", deque(maxlen=100))
    monkeypatch.setattr(main, "DAILY_CAP_EUR", 100.0)
    c = TestClient(main.app)

    c.post("/cost/record", json={"service": "a", "actual_cost_eur": 1.0, "agent_id": "ag1"})
    c.post("/cost/record", json={"service": "b", "actual_cost_eur": 2.0, "agent_id": "ag2"})
    c.post("/cost/record", json={"service": "a", "actual_cost_eur": 0.5, "agent_id": "ag1"})

    today = main._day_key()
    daily = c.get(f"/cost/daily/{today}").json()
    assert daily["total_eur"] == 3.5
    assert daily["by_service"]["a"] == 1.5
    assert daily["by_service"]["b"] == 2.0

    summary = c.get("/cost/summary").json()
    assert summary["total_eur"] == 3.5

    by_agent = c.get("/cost/by_agent").json()
    agents_map = {a["agent_id"]: a for a in by_agent["agents"]}
    assert agents_map["ag1"]["total_eur"] == 1.5
    assert agents_map["ag1"]["calls"] == 2
    assert agents_map["ag2"]["total_eur"] == 2.0
