from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_publish_requires_key():
    r = TestClient(app).post("/publish", json={"asset_id": "a1", "consumer_id": "c1"})
    assert r.status_code == 401


def test_publish_ok():
    r = TestClient(app).post(
        "/publish",
        json={"asset_id": "a1", "consumer_id": "c1"},
        headers={"X-Consumer-Key": "secret-key-001"},
    )
    assert r.status_code == 200
    assert "release_id" in r.json()
