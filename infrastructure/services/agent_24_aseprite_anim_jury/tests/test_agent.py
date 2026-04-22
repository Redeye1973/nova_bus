"""Tests for Agent 24."""
from __future__ import annotations

import base64
import io
import os

os.environ.setdefault("OLLAMA_DISABLE", "1")

from fastapi.testclient import TestClient
from PIL import Image

import main


def _two_pngs() -> list[str]:
    out: list[str] = []
    for color in ("black", "white"):
        im = Image.new("RGB", (8, 8), color=color)
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        out.append(base64.b64encode(buf.getvalue()).decode("ascii"))
    return out


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["agent"] == "24_aseprite_anim_jury"


def test_animate_review():
    c = TestClient(main.app)
    r = c.post("/animate/review", json={"frames_b64": _two_pngs(), "fps_hint": 12.0})
    assert r.status_code == 200
    body = r.json()
    assert body["frame_count"] == 2
    assert "max_jump" in body["metrics"]


def test_invoke_review():
    c = TestClient(main.app)
    r = c.post("/invoke", json={"action": "review", "frames_b64": _two_pngs()})
    assert r.status_code == 200
