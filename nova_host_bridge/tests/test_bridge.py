"""Bridge tests. Exercises the API surface; adapter calls stay offline-safe."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("BRIDGE_WORKDIR", str(ROOT / "jobs_test"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "nova_host_bridge"


def test_tools_endpoint_returns_both_adapters():
    c = TestClient(main.app)
    r = c.get("/tools")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"freecad", "qgis"}
    assert "available" in body["freecad"]
    assert "available" in body["qgis"]


def test_auth_blocks_when_token_set(monkeypatch):
    monkeypatch.setattr(main, "BRIDGE_TOKEN", "secret123")
    c = TestClient(main.app)
    assert c.get("/tools").status_code == 401
    assert c.get("/tools", headers={"Authorization": "Bearer secret123"}).status_code == 200


def test_invalid_job_dir_path_traversal_rejected():
    c = TestClient(main.app)
    r = c.get("/jobs/..%2Fother/files/x.txt")
    assert r.status_code in (400, 404)


def test_qgis_run_bad_payload_rejected():
    c = TestClient(main.app)
    r = c.post("/qgis/run", json={})
    assert r.status_code == 422


def test_freecad_request_validation():
    c = TestClient(main.app)
    r = c.post("/freecad/parametric", json={"category": "fighter"})
    assert r.status_code in (200, 503)
    body = r.json()
    if r.status_code == 200:
        assert "metrics" in body or "error" in body
    else:
        assert body["detail"]["reason"] in ("freecad_unavailable",)
