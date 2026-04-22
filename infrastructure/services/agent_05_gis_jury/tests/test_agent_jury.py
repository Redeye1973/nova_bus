from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    r = TestClient(app).get("/health")
    assert r.status_code == 200


def test_review_geojson_ok(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    art = {
        "epsg": 3857,
        "geometry": {"type": "Point", "coordinates": [5.1, 52.0]},
        "self_intersection": False,
        "properties": {"id": 1},
        "coverage_ratio": 0.9,
    }
    r = TestClient(app).post("/review", json={"job_id": "g1", "artifact": art, "context": {}})
    assert r.status_code == 200
    assert r.json()["job_id"] == "g1"


def test_review_sparse(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    r = TestClient(app).post("/review", json={"job_id": "g2", "artifact": {}, "context": {}})
    assert r.status_code == 200
