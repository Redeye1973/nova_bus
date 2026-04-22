"""NOVA v2 Agent 29 — ElevenLabs Audio (Cost Guard precheck; dry-run without API key)."""
from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 29 - ElevenLabs Audio", version="0.1.0")

COST_GUARD_URL = os.getenv("COST_GUARD_URL", "").rstrip("/")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVEN_BASE = os.getenv("ELEVENLABS_API_BASE", "https://api.elevenlabs.io").rstrip("/")
ESTIMATE_CHARS = float(os.getenv("ELEVENLABS_EUR_PER_1K_CHARS", "0.05"))

VOICES: Dict[str, Dict[str, Any]] = {}
AUDIO_CACHE: Dict[str, Dict[str, Any]] = {}


def _cost_precheck(estimated_eur: float) -> None:
    if not COST_GUARD_URL:
        return
    try:
        with httpx.Client(timeout=3.0) as c:
            r = c.post(
                f"{COST_GUARD_URL}/cost/check",
                json={"estimated_cost_eur": estimated_eur},
            )
        if r.status_code == 429:
            raise HTTPException(status_code=429, detail=r.json())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, detail=f"cost_guard_unreachable:{exc}") from exc


class VoiceRegister(BaseModel):
    voice_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    character_id: Optional[str] = None


class TtsBody(BaseModel):
    voice_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=8000)


def _cache_key(voice_id: str, text: str) -> str:
    h = hashlib.sha256(f"{voice_id}\n{text}".encode()).hexdigest()
    return h[:48]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "29_elevenlabs", "version": "0.1.0"}


@app.get("/voices")
def voices_list() -> Dict[str, Any]:
    return {"voices": list(VOICES.values())}


@app.post("/voices/register")
def voices_register(body: VoiceRegister) -> Dict[str, Any]:
    VOICES[body.voice_id] = {
        "voice_id": body.voice_id,
        "label": body.label,
        "character_id": body.character_id,
        "registered_at": time.time(),
    }
    return {"registered": True, "voice_id": body.voice_id}


@app.post("/tts")
def tts_synthesize(body: TtsBody) -> Dict[str, Any]:
    if body.voice_id not in VOICES:
        raise HTTPException(400, detail="unknown_voice_register_first")
    est = ESTIMATE_CHARS * (len(body.text) / 1000.0)
    _cost_precheck(est)
    ck = _cache_key(body.voice_id, body.text)
    if ck in AUDIO_CACHE:
        return {"status": "cache_hit", "cache_key": ck, **AUDIO_CACHE[ck]}
    if not ELEVEN_KEY:
        rec = {
            "cache_key": ck,
            "format": "dry_run",
            "bytes": 0,
            "estimated_cost_eur": round(est, 4),
            "minio_key": f"tts/{ck}.mp3",
        }
        AUDIO_CACHE[ck] = rec
        return {"status": "dry_run", **rec}
    url = f"{ELEVEN_BASE}/v1/text-to-speech/{body.voice_id}"
    try:
        with httpx.Client(timeout=60.0) as c:
            r = c.post(
                url,
                headers={"xi-api-key": ELEVEN_KEY, "accept": "audio/mpeg"},
                json={"text": body.text},
            )
        if r.status_code >= 400:
            raise HTTPException(r.status_code, detail=r.text[:500])
        rec = {
            "cache_key": ck,
            "format": "audio/mpeg",
            "bytes": len(r.content),
            "estimated_cost_eur": round(est, 4),
            "minio_key": f"tts/{ck}.mp3",
        }
        AUDIO_CACHE[ck] = rec
        return {"status": "ok", **rec}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, detail=str(exc)) from exc


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    act = str(body.get("action", "")).lower()
    if act == "register":
        return voices_register(VoiceRegister.model_validate(body.get("payload", body)))
    if act == "tts":
        return tts_synthesize(TtsBody.model_validate(body.get("payload", body)))
    return {"hint": "actions: register, tts", "keys": list(body.keys())}
