"""Tests for Agent 34."""
from __future__ import annotations

import base64

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    assert c.get("/health").json()["agent"] == "34_unreal_import"


def test_prep_fbx_and_usd():
    raw = b"Kaydara FBX Binary  " + b"\x00" * 120
    b64 = base64.b64encode(raw).decode("ascii")
    usd = '#usda 1.0\ndef Mesh "World"\n{\n}\ndef Material "M1"\n{\n}\n'
    c = TestClient(main.app)
    r = c.post("/unreal/prep", json={"fbx_b64": b64, "usd_text": usd})
    assert r.status_code == 200
    body = r.json()
    assert body["fbx"]["valid"] is True
    assert body["usd"]["material_count"] == 1
    assert body["texture_paths"]["replacements"] >= 0
