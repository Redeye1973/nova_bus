"""NOVA v2 Agent 03 — Audio Jury (WAV DSP POC, numpy)."""
from __future__ import annotations

import base64
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from audio_wav import load_wav_pcm
from judge import verdict_from_members
from jury.frequency_balance import analyze as spectral_analyze
from jury.frequency_balance import to_jury_dict as spectral_to_dict
from jury.technical_quality import analyze as technical_analyze
from jury.technical_quality import to_jury_dict as technical_to_dict

app = FastAPI(title="NOVA v2 Audio Jury", version="0.1.0-dsp")


class AudioReviewItem(BaseModel):
    format: Literal["wav"] = "wav"
    audio_base64: str
    intended_genre: Optional[str] = None


class BatchPayload(BaseModel):
    items: List[AudioReviewItem] = Field(default_factory=list)


def _decode_wav_b64(b64: str) -> tuple[Any, int]:
    try:
        raw = base64.b64decode(b64, validate=False)
    except Exception as e:
        raise HTTPException(400, detail=f"base64_decode_failed:{e}") from e
    try:
        return load_wav_pcm(raw)
    except Exception as e:
        raise HTTPException(400, detail=f"wav_parse_failed:{e}") from e


def _review_one(item: AudioReviewItem) -> Dict[str, Any]:
    if item.format != "wav":
        raise HTTPException(400, detail="only_wav_supported_in_this_build")
    samples, sr = _decode_wav_b64(item.audio_base64)
    tech = technical_analyze(samples, sr)
    spec = spectral_analyze(samples, sr)
    members = [technical_to_dict(tech), spectral_to_dict(spec)]
    verdict, avg, notes = verdict_from_members(members)
    return {
        "format": item.format,
        "sample_rate": sr,
        "shape": list(samples.shape) if hasattr(samples, "shape") else [],
        "intended_genre": item.intended_genre,
        "jury": members,
        "verdict": verdict,
        "average_score": round(avg, 3),
        "notes": notes[:32],
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "03", "mode": "dsp_wav_poc", "version": "0.1.0"}


@app.post("/review/audio")
def review_audio(body: AudioReviewItem) -> Dict[str, Any]:
    return _review_one(body)


@app.post("/review/batch")
def review_batch(body: BatchPayload) -> Dict[str, Any]:
    if not body.items:
        raise HTTPException(400, detail="items_empty")
    out: List[Dict[str, Any]] = []
    for it in body.items:
        out.append(_review_one(it))
    return {"count": len(out), "results": out}


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    """n8n compatibility: full JSON body; route to review when WAV payload present."""
    if not isinstance(body, dict):
        return {"agent": "03", "error": "expected_object"}
    if body.get("format") == "wav" and body.get("audio_base64"):
        try:
            item = AudioReviewItem.model_validate(body)
            return _review_one(item)
        except Exception as e:
            return {"agent": "03", "error": "validation_failed", "detail": str(e)[:200]}
    return {
        "agent": "03",
        "agent_name": "Audio Jury",
        "received_keys": list(body.keys()),
        "hint": "POST /review/audio with {format:wav, audio_base64:...} for analysis",
    }
