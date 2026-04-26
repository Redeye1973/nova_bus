"""Unit tests for Agent 21 FreeCAD Parametric (trimesh fallback)."""
from __future__ import annotations

import os

os.environ.setdefault("FREECAD_OUTPUT_DIR", os.path.join(os.path.dirname(__file__), ".out"))

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "21_freecad_parametric"
    # Without HOST_BRIDGE_URL set the agent must fall back to trimesh.
    assert body["bridge"]["configured"] is False
    assert body["fallback_mode"] is True
    assert body["engine"] == "trimesh"


def test_build_base_fighter():
    c = TestClient(main.app)
    r = c.post("/model/build-base", json={"category": "fighter", "dimensions": {"length": 14.0, "radius": 1.2}})
    assert r.status_code == 200
    body = r.json()
    assert body["primitive"] == "capsule"
    assert body["dimensions"]["length"] == 14.0
    assert body["metrics"]["face_count"] > 0
    assert os.path.exists(body["files"]["stl"])


def test_variants_generate_with_param_matrix():
    c = TestClient(main.app)
    r = c.post("/variants/generate", json={
        "base_model": {"category": "fighter"},
        "parameter_matrix": {"length": [8.0, 12.0, 16.0]},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["variant_count"] == 3
    assert all("metrics" in v for v in body["variants"])
    assert all("verdict" in v for v in body["variants"])


def test_components_assemble_returns_combined_metrics():
    c = TestClient(main.app)
    r = c.post("/components/assemble", json={
        "components": [
            {"base": {"category": "vehicle"}, "mount": [0, 0, 0]},
            {"base": {"category": "prop"}, "mount": [3, 0, 1]},
        ],
        "output_name": "test_assembly",
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["components"]) == 2
    assert body["metrics"]["face_count"] > 0
    assert os.path.exists(body["files"]["stl"])


def test_invoke_unknown_action():
    c = TestClient(main.app)
    r = c.post("/invoke", json={"action": "no_such"})
    assert r.status_code == 200
    assert "error" in r.json()


def test_rejects_xyz_dimension_keys():
    c = TestClient(main.app)
    r = c.post("/model/build-base", json={"category": "vehicle", "dimensions": {"x": 1, "y": 2, "z": 3}})
    assert r.status_code == 400
    detail = str(r.json().get("detail", "")).lower()
    assert "length" in detail or "xyz" in detail


def test_build_base_box_category():
    c = TestClient(main.app)
    r = c.post(
        "/model/build-base",
        json={"category": "box", "dimensions": {"length": 2.0, "width": 3.0, "height": 4.0}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["primitive"] == "box"
    assert body["dimensions"]["length"] == 2.0
