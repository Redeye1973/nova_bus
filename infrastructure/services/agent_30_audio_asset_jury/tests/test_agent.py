"""Tests for Agent 30."""
from __future__ import annotations

import io
import wave

from fastapi.testclient import TestClient

import main


def _short_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        frames = (b"\x00\x10" * 4096) + (b"\xff\xf0" * 4096)
        w.writeframes(frames)
    return buf.getvalue()


def test_health():
    c = TestClient(main.app)
    assert c.get("/health").status_code == 200


def test_analyze_wav():
    c = TestClient(main.app)
    raw = _short_wav()
    r = c.post("/audio/analyze", files={"file": ("t.wav", raw, "audio/wav")})
    assert r.status_code == 200
    m = r.json()["metrics"]
    assert m["duration_sec"] > 0
    assert m["sample_rate"] == 22050
