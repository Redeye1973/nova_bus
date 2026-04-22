from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_bake_stub():
    r = TestClient(app).post("/bake", json={"tile_id": "t1"})
    assert r.status_code == 200
    assert r.json()["status"] == "stub"


def test_invoke():
    r = TestClient(app).post("/invoke", json={"tile_id": "x"})
    assert r.status_code == 200
