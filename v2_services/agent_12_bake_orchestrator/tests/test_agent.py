from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200


def test_create_and_advance_job():
    c = TestClient(app)
    r = c.post("/bake/jobs", json={"postcode": "1234AB", "layers": ["BAG"]})
    assert r.status_code == 200
    jid = r.json()["job_id"]
    r2 = c.get(f"/bake/jobs/{jid}")
    assert r2.json()["state"] == "queued"
    r3 = c.post(f"/bake/jobs/{jid}/advance")
    assert r3.json()["state"] == "pdok"


def test_invoke_create():
    c = TestClient(app)
    r = c.post("/invoke", json={"action": "create", "postcode": "9999ZZ", "layers": []})
    assert r.status_code == 200
    assert "job_id" in r.json()
