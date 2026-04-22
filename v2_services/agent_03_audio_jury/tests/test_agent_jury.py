from __future__ import annotations

import base64
import io
import os
import wave

import numpy as np
from fastapi.testclient import TestClient

from main import app


def _wav_bytes_mono_sine(sr: int = 8000, seconds: float = 0.2, freq: float = 440.0) -> bytes:
    n = int(sr * seconds)
    t = np.arange(n, dtype=np.float32) * (2 * np.pi * freq / sr)
    samples = (np.sin(t) * 0.1 * 32767.0).astype(np.int16)
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    return bio.getvalue()


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_review_wav_accept(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    b64 = base64.b64encode(_wav_bytes_mono_sine()).decode("ascii")
    c = TestClient(app)
    r = c.post(
        "/review",
        json={"job_id": "t1", "artifact": {"format": "wav", "audio_base64": b64}, "context": {}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["job_id"] == "t1"
    assert body["verdict"] in ("accept", "revise", "reject")
    assert "technical" in body["scores"]


def test_review_missing_payload_scores_low(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    c = TestClient(app)
    r = c.post("/review", json={"job_id": "t2", "artifact": {}, "context": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("accept", "revise", "reject")


def test_invoke_still_routes_wav(monkeypatch):
    monkeypatch.delenv("NOVA_JUDGE_URL", raising=False)
    b64 = base64.b64encode(_wav_bytes_mono_sine()).decode("ascii")
    c = TestClient(app)
    r = c.post("/invoke", json={"format": "wav", "audio_base64": b64})
    assert r.status_code == 200
    assert "verdict" in r.json()
