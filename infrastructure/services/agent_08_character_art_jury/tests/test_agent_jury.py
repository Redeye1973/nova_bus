from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    assert TestClient(app).get("/health").status_code == 200


def test_review_scores_only(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    art = {
        "width": 128,
        "height": 128,
        "palette_size": 64,
        "silhouette_score": 8.0,
        "expression_score": 7.5,
        "qdrant_similarity_hits": 2,
        "outfit_context_score": 8.0,
    }
    r = TestClient(app).post("/review", json={"job_id": "ch1", "artifact": art, "context": {}})
    assert r.status_code == 200


def test_review_minimal(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    r = TestClient(app).post("/review", json={"job_id": "ch2", "artifact": {}, "context": {}})
    assert r.status_code == 200
