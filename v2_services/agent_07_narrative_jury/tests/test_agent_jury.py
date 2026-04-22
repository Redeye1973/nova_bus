from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    assert TestClient(app).get("/health").status_code == 200


def test_review_long_text(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    text = "Intro\n\nAct one\n\nAct two\n\n" + ("word " * 80)
    art = {"text": text, "canon_hits": 2, "cross_product_hits": 2}
    r = TestClient(app).post("/review", json={"job_id": "n1", "artifact": art, "context": {}})
    assert r.status_code == 200


def test_review_short(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    r = TestClient(app).post(
        "/review",
        json={"job_id": "n2", "artifact": {"text": "short", "canon_hits": 0}, "context": {}},
    )
    assert r.status_code == 200
