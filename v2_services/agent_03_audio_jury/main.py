"""NOVA v2 Agent 03 — Audio Jury (WAV DSP + uniform /review)."""
from __future__ import annotations

import asyncio
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
from pipeline_judge import call_pipeline_judge

app = FastAPI(title="NOVA v2 Audio Jury", version="1.0.0")

AGENT_TAG = "03_audio_jury"


class JuryRequest(BaseModel):
    job_id: str
    artifact: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)


class JuryVerdict(BaseModel):
    job_id: str
    verdict: str
    scores: Dict[str, Dict[str, Any]]
    judge_decision: Dict[str, Any]


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


def _review_wav_item(item: AudioReviewItem) -> Dict[str, Any]:
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
        "jury_members": members,
        "verdict": verdict,
        "average_score": round(avg, 3),
        "notes": notes[:32],
    }


async def run_jury_members(req: JuryRequest) -> Dict[str, Dict[str, Any]]:
    art = req.artifact
    fmt = art.get("format", "wav")
    b64 = art.get("audio_base64")
    if fmt != "wav" or not b64 or not isinstance(b64, str):
        return {
            "technical": {"score": 0.0, "issues": ["missing_wav_payload"], "warnings": []},
            "spectral": {"score": 0.0, "issues": ["missing_wav_payload"], "warnings": []},
        }

    def _work() -> Dict[str, Dict[str, Any]]:
        item = AudioReviewItem.model_validate(
            {
                "format": "wav",
                "audio_base64": b64,
                "intended_genre": art.get("intended_genre"),
            }
        )
        out = _review_wav_item(item)
        members = out["jury_members"]
        return {"technical": members[0], "spectral": members[1]}

    return await asyncio.to_thread(_work)


def synthesize_verdict(scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    members = list(scores.values())
    verdict, avg, notes = verdict_from_members(members)
    return {
        "verdict": verdict,
        "average_score": round(avg, 3),
        "notes": notes[:24],
        "member_keys": list(scores.keys()),
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "03", "mode": "audio_jury_v1", "version": "1.0.0"}


@app.post("/review", response_model=JuryVerdict)
async def review(req: JuryRequest) -> JuryVerdict:
    scores = await run_jury_members(req)
    final = synthesize_verdict(scores)
    task_result: Dict[str, Any] = {
        "status": "success",
        "job_id": req.job_id,
        "jury_verdict": final["verdict"],
        "average_score": final["average_score"],
    }
    pj = call_pipeline_judge(task_result, AGENT_TAG)
    jd = {**final, "pipeline_judge": pj}
    return JuryVerdict(
        job_id=req.job_id,
        verdict=str(final["verdict"]),
        scores=scores,
        judge_decision=jd,
    )


@app.post("/review/audio")
def review_audio(body: AudioReviewItem) -> Dict[str, Any]:
    return _review_wav_item(body)


@app.post("/review/batch")
def review_batch(body: BatchPayload) -> Dict[str, Any]:
    if not body.items:
        raise HTTPException(400, detail="items_empty")
    out: List[Dict[str, Any]] = []
    for it in body.items:
        out.append(_review_wav_item(it))
    return {"count": len(out), "results": out}


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    """n8n compatibility."""
    if not isinstance(body, dict):
        return {"agent": "03", "error": "expected_object"}
    if body.get("format") == "wav" and body.get("audio_base64"):
        try:
            item = AudioReviewItem.model_validate(body)
            return _review_wav_item(item)
        except Exception as e:
            return {"agent": "03", "error": "validation_failed", "detail": str(e)[:200]}
    return {
        "agent": "03",
        "agent_name": "Audio Jury",
        "received_keys": list(body.keys()),
        "hint": "POST /review with {job_id, artifact:{format:wav,audio_base64}}",
    }
