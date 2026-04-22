from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_download():
    r = TestClient(app).post("/download", json={"postcode": "5611AB", "layers": ["BAG", "BGT"]})
    assert r.status_code == 200
    b = r.json()
    assert "cache_key" in b
    assert b["minio_bucket"] == "nova-pdok-cache"


def test_invoke():
    r = TestClient(app).post("/invoke", json={"postcode": "1111XX", "layers": ["BAG"]})
    assert r.status_code == 200
