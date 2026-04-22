from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_review_accept(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    art = {
        "face_count": 1000,
        "vertex_count": 800,
        "is_watertight": True,
        "uv_valid": True,
        "bbox_max_dim": 10.0,
        "visual_score": 8.0,
    }
    c = TestClient(app)
    r = c.post("/review", json={"job_id": "j1", "artifact": art, "context": {}})
    assert r.status_code == 200
    b = r.json()
    assert b["job_id"] == "j1"
    assert b["verdict"] in ("accept", "revise", "reject")


def test_review_reject_low_scores(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    art = {
        "face_count": 2_000_000,
        "vertex_count": 0,
        "is_watertight": False,
        "uv_valid": False,
        "bbox_max_dim": 0,
        "visual_score": 1.0,
    }
    c = TestClient(app)
    r = c.post("/review", json={"job_id": "j2", "artifact": art, "context": {}})
    assert r.status_code == 200
    assert r.json()["verdict"] in ("accept", "revise", "reject")


def test_invoke(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    c = TestClient(app)
    r = c.post("/invoke", json={"job_id": "x", "face_count": 500, "is_watertight": True})
    assert r.status_code == 200
    assert "verdict" in r.json()
