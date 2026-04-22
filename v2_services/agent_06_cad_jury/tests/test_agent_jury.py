from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    assert TestClient(app).get("/health").status_code == 200


def test_review_good_cad(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    art = {
        "constraints_ok": True,
        "feature_tree_depth": 12,
        "step_export_ok": True,
        "stl_export_ok": True,
        "bbox_diagonal_mm": 120.0,
    }
    r = TestClient(app).post("/review", json={"job_id": "c1", "artifact": art, "context": {}})
    assert r.status_code == 200
    assert r.json()["verdict"] in ("accept", "revise", "reject")


def test_review_bad_exports(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    art = {"constraints_ok": False, "step_export_ok": False, "stl_export_ok": False}
    r = TestClient(app).post("/review", json={"job_id": "c2", "artifact": art, "context": {}})
    assert r.status_code == 200
