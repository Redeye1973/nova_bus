"""Unit tests for Agent 17 Error Handler."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "17_error_handler"
    assert body["pattern_count"] >= 5


def test_report_known_pattern_ollama():
    c = TestClient(main.app)
    r = c.post("/error/report", json={
        "service": "ollama_client",
        "message": "ConnectionError to ollama on 11434",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["classification"]["category"] == "ollama_connection_refused"
    assert body["classification"]["retry_able"] is True
    assert body["retry"]["attempt"] == 1


def test_report_unknown_then_resolve_and_history():
    c = TestClient(main.app)
    r = c.post("/error/report", json={
        "service": "weird_service",
        "severity": "low",
        "message": "totally novel error nobody has seen before zzzz",
    })
    body = r.json()
    eid = body["error_id"]
    assert body["classification"]["category"] == "unknown"

    r2 = c.post("/error/resolve", json={
        "error_id": eid,
        "action": "manual_restart",
        "success": True,
        "notes": "operator reset",
    })
    assert r2.status_code == 200
    assert r2.json()["resolved"] is True

    r3 = c.get("/repair/history", params={"service": "weird_service"})
    assert r3.status_code == 200
    items = r3.json()["items"]
    kinds = [i["kind"] for i in items]
    assert "report" in kinds and "resolve" in kinds


def test_invoke_dispatch_history_after_action():
    c = TestClient(main.app)
    c.post("/invoke", json={
        "action": "report",
        "payload": {"service": "blender", "message": "MemoryError in bpy.ops"},
    })
    r = c.post("/invoke", json={"action": "history", "service": "blender"})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1


def test_invoke_unknown_action():
    c = TestClient(main.app)
    r = c.post("/invoke", json={"action": "no_such_thing"})
    assert r.status_code == 200
    assert "error" in r.json()
