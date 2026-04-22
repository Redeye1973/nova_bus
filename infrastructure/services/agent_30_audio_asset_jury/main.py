"""NOVA v2 Agent 30 — Audio Asset Jury (librosa technical QA; optional Audio Jury ref)."""
from __future__ import annotations

import io
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
import numpy as np
import librosa

app = FastAPI(title="NOVA v2 Agent 30 - Audio Asset Jury", version="0.1.0")

AUDIO_JURY_URL = os.getenv("AUDIO_JURY_URL", "").rstrip("/")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "30_audio_asset_jury", "version": "0.1.0"}


def _analyze_buffer(raw: bytes) -> Dict[str, Any]:
    y, sr = librosa.load(io.BytesIO(raw), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    pulse = float(np.mean(onset_env)) if onset_env.size else 0.0
    tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
    ta = np.asarray(tempo_arr).astype(float).ravel()
    tempo = float(ta[0]) if ta.size else 0.0
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    pitch_class = int(np.argmax(np.mean(chroma, axis=1)))
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_hint = notes[pitch_class % 12]
    return {
        "sample_rate": int(sr),
        "duration_sec": round(duration, 3),
        "tempo_bpm_estimate": round(tempo, 2) if tempo > 0 else None,
        "mean_onset_strength": round(pulse, 4),
        "key_class_hint": key_hint,
    }


@app.post("/audio/analyze")
async def audio_analyze(
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(400, detail="missing_filename")
    raw = await file.read()
    if len(raw) < 64:
        raise HTTPException(400, detail="file_too_small")
    try:
        metrics = _analyze_buffer(raw)
    except Exception as exc:
        raise HTTPException(400, detail=f"librosa_failed:{exc}") from exc
    out: Dict[str, Any] = {"file": file.filename, "metrics": metrics}
    if AUDIO_JURY_URL:
        try:
            with httpx.Client(timeout=5.0) as c:
                r = c.post(
                    f"{AUDIO_JURY_URL}/invoke",
                    json={"action": "delegate", "filename": file.filename},
                )
            out["audio_jury_delegate"] = {"status_code": r.status_code, "body": r.text[:300]}
        except Exception as exc:
            out["audio_jury_delegate"] = {"error": str(exc)}
    return out


@app.post("/invoke")
async def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    return {"hint": "POST /audio/analyze with multipart file", "keys": list(body.keys()) if isinstance(body, dict) else []}
