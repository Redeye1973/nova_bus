from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_get_template():
    r = TestClient(app).get("/templates/build_v2_agent")
    assert r.status_code == 200
    assert "latest" in r.json()


def test_upsert_and_version():
    c = TestClient(app)
    c.post("/templates", json={"name": "custom", "body": "hello", "approved": True})
    r = c.get("/templates/custom")
    assert r.status_code == 200
