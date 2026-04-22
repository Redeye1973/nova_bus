from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    b = TestClient(app).get("/health").json()
    assert b["mode"] == "pending_full_bridge"


def test_process():
    r = TestClient(app).post("/process", json={"operation": "buffer"})
    assert r.status_code == 200
    assert r.json()["status"] == "pending_full_bridge"


def test_invoke():
    assert TestClient(app).post("/invoke", json={"operation": "buffer"}).status_code == 200
