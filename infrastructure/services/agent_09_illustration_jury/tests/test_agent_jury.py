from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    assert TestClient(app).get("/health").status_code == 200


def test_review_dims(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    art = {
        "width": 1024,
        "height": 1024,
        "composition_score": 8.0,
        "style_consistency_score": 8.0,
        "readability_score": 8.0,
        "palette_adherence_score": 7.0,
    }
    r = TestClient(app).post("/review", json={"job_id": "i1", "artifact": art, "context": {}})
    assert r.status_code == 200


def test_review_empty(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    r = TestClient(app).post("/review", json={"job_id": "i2", "artifact": {}, "context": {}})
    assert r.status_code == 200
