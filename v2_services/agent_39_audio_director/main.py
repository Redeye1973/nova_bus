"""NOVA v2 Agent 39 — Audio Director (meta-judge audiolaag, poort 8139)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx
import yaml
from fastapi import FastAPI
from pydantic import BaseModel, Field

sys.path.insert(0, "/nova_shared")
sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from resume_part_update import notify_part_completed_async  # noqa: F401
except ImportError:
    async def notify_part_completed_async(**_kwargs):  # type: ignore[misc]
        return {"ok": False, "skipped": True, "reason": "resume_part_update_unavailable"}

try:
    from proof import make_and_record
except ImportError:
    def make_and_record(*_a, **_k):  # type: ignore[misc]
        return {}

app = FastAPI(title="Audio Director - Agent 39", version="1.1.0")

AGENT_ID = 39
PORT = int(os.getenv("AUDIO_DIRECTOR_PORT", "8139"))

BIBLE = Path(os.getenv("NOVA_AUDIO_BIBLE", "/config/audio_bible.yaml"))
if not BIBLE.is_file():
    BIBLE = Path(r"L:\!Nova V2\config\audio_bible.yaml")

ELEVENLABS_AGENT = os.getenv("ELEVENLABS_AGENT_URL", "http://agent-29-elevenlabs:8129").rstrip("/")
AUDIO_JURY = os.getenv("AUDIO_JURY_URL", "http://agent-30-audio-asset-jury:8130").rstrip("/")
COST_GUARD = os.getenv("COST_GUARD_URL", "http://agent-16-cost-guard:8116").rstrip("/")
AUDIOCRAFT_URL = os.getenv("AUDIOCRAFT_URL", "http://audiocraft:8080").rstrip("/")


class AudioPlan(BaseModel):
    domain: str
    project: str
    output_dir: str
    spec: dict = Field(default_factory=dict)


class AudioReview(BaseModel):
    domain: str
    audio_files: list[str]
    context: dict = Field(default_factory=dict)


class AudioDeliver(BaseModel):
    """Markeer een audio-asset als geleverd (parts progress)."""
    asset: str
    filepath: str = ""
    domain: str = "shmup"
    project: str = ""


def _resolve_path(raw: str) -> Path:
    mount = (os.getenv("NOVA_GAME_OUTPUT_MOUNT") or "").strip()
    win_prefix = (os.getenv("NOVA_GAME_OUTPUT_WIN_PREFIX") or r"L:\ZZZ ZZ NOVA GAME OUTPUT").strip()
    if raw and mount:
        norm = os.path.normpath(raw.replace("/", "\\"))
        prefix = os.path.normpath(win_prefix.replace("/", "\\"))
        if norm.lower().startswith(prefix.lower()):
            rel = norm[len(prefix) :].lstrip("\\/")
            return Path(mount) / rel.replace("\\", "/")
    return Path(raw)


def load_domain(domain: str) -> dict:
    bible = yaml.safe_load(BIBLE.read_text(encoding="utf-8"))
    return bible.get("domains", {}).get(domain, {})


def generate_music(req: AudioPlan) -> str:
    return "music_generation_queued"


def analyze_audio_technical(filepath: str) -> dict:
    try:
        import librosa
        import numpy as np

        resolved = _resolve_path(filepath)
        if not resolved.is_file():
            return {"error": f"file_not_found:{filepath}"}
        y, sr = librosa.load(str(resolved), sr=None, mono=True)
        peak = float(np.max(np.abs(y))) if len(y) else 0.0
        rms = float(np.sqrt(np.mean(y**2))) if len(y) else 0.0
        return {
            "peak": round(peak, 4),
            "rms": round(rms, 4),
            "clipping": peak >= 0.99,
            "duration_s": round(float(len(y) / sr), 3) if sr else 0.0,
        }
    except Exception as exc:
        return {"error": str(exc)}


def analyze_coherence(domain: str, files: list[str], context: dict, checks: list) -> dict:
    issues: List[str] = []
    names = " ".join(Path(f).stem.lower() for f in files)
    if domain == "shmup":
        if "music" not in names and "track" not in names:
            issues.append("Geen muziek gevonden — shmup heeft achtergrondmuziek nodig")
        if not any(w in names for w in ("weapon", "shot", "laser", "plasma")):
            issues.append("Geen wapen-SFX gevonden")
        if not any(e in names for e in ("explosion", "impact", "boom")):
            issues.append("Geen explosie-SFX gevonden")
    elif domain == "surilians":
        if "voice" not in names and not context.get("characters"):
            issues.append("Geen voice-audio voor een dialoog-zware scene")
    elif domain == "vr_archviz":
        if "ambience" not in names and "ambient" not in names:
            issues.append("Geen ambience gevonden voor VR walkthrough")
    return {"issues": issues, "ok": len(issues) == 0, "checks_reference": checks}


async def _probe_agent(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{url}/health")
        return {"url": url, "status_code": r.status_code, "ok": r.status_code == 200}
    except Exception as exc:
        return {"url": url, "ok": False, "error": str(exc)}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "agent": AGENT_ID,
        "name": "Audio Director",
        "port": PORT,
        "bible": str(BIBLE),
    }


@app.post("/plan")
async def plan(req: AudioPlan) -> Dict[str, Any]:
    domain_cfg = load_domain(req.domain)
    layers = domain_cfg.get("layers", [])
    tasks: List[Dict[str, Any]] = []

    out_path = _resolve_path(req.output_dir) if req.output_dir.startswith("L:") else Path(req.output_dir)
    try:
        out_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    downstream: Dict[str, Any] = {}
    for layer in layers:
        if layer == "music":
            tasks.append(
                {
                    "layer": "music",
                    "tool": "audiocraft",
                    "action": generate_music(req),
                    "route": AUDIOCRAFT_URL,
                }
            )
        elif layer.startswith("sfx") or layer == "sfx":
            tasks.append(
                {
                    "layer": layer,
                    "tool": "elevenlabs/supercollider",
                    "action": "sfx_queued",
                    "route": ELEVENLABS_AGENT,
                }
            )
        elif layer == "voice":
            tasks.append(
                {
                    "layer": "voice",
                    "tool": "agent_29",
                    "action": "voice_queued",
                    "route": ELEVENLABS_AGENT,
                }
            )
        elif layer in ("ambience", "spatial_sfx", "footsteps"):
            tasks.append(
                {
                    "layer": layer,
                    "tool": "audiocraft/sox",
                    "action": "ambience_queued",
                    "route": AUDIOCRAFT_URL,
                }
            )

    downstream["elevenlabs"] = await _probe_agent(ELEVENLABS_AGENT)
    downstream["audio_jury"] = await _probe_agent(AUDIO_JURY)
    downstream["cost_guard"] = await _probe_agent(COST_GUARD)

    import time as _time

    return {
        "agent": "Audio Director",
        "agent_id": AGENT_ID,
        "domain": req.domain,
        "project": req.project,
        "output_dir": str(out_path),
        "layers_planned": layers,
        "director_checks": domain_cfg.get("director_checks", []),
        "tasks": tasks,
        "downstream": downstream,
        "proof": make_and_record(
            "report",
            id=f"audio_plan_{req.project}_{int(_time.time())}",
            agent="39_audio_director",
            note=f"{len(tasks)} audio-taken gepland",
            context="audio_director_plan",
        ),
    }


@app.post("/review")
async def review(req: AudioReview) -> Dict[str, Any]:
    domain_cfg = load_domain(req.domain)
    checks = domain_cfg.get("director_checks", [])
    findings: List[Dict[str, Any]] = []

    for f in req.audio_files:
        tech = analyze_audio_technical(f)
        finding: Dict[str, Any] = {"file": f, "technical": tech}
        resolved = _resolve_path(f)
        if resolved.is_file() and not tech.get("error"):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    with resolved.open("rb") as fh:
                        r = await client.post(
                            f"{AUDIO_JURY}/audio/analyze",
                            files={"file": (resolved.name, fh, "application/octet-stream")},
                        )
                if r.status_code == 200:
                    finding["jury_metrics"] = r.json().get("metrics", {})
                else:
                    finding["jury_metrics"] = {"status_code": r.status_code}
            except Exception as exc:
                finding["jury_metrics"] = {"error": str(exc)}
        findings.append(finding)

    coherence = analyze_coherence(req.domain, req.audio_files, req.context, checks)
    overall = "accept" if coherence.get("ok") and all(
        not f.get("technical", {}).get("clipping") for f in findings
    ) else "review"

    import time as _time

    return {
        "agent": "Audio Director",
        "agent_id": AGENT_ID,
        "domain": req.domain,
        "checks_applied": checks,
        "technical_findings": findings,
        "coherence": coherence,
        "overall_verdict": overall,
        "proof": make_and_record(
            "report",
            id=f"audio_review_{req.domain}_{int(_time.time())}",
            agent="39_audio_director",
            note=f"verdict={overall}, {len(findings)} files",
            context="audio_director_review",
        ),
    }


@app.post("/deliver")
async def deliver(req: AudioDeliver) -> Dict[str, Any]:
    """Na succesvolle audio-levering: meld taak af bij Resume Agent."""
    resolved = _resolve_path(req.filepath) if req.filepath else None
    if req.filepath and (resolved is None or not resolved.is_file()):
        return {
            "ok": False,
            "error": f"audio_file_not_found:{req.filepath}",
        }
    # Fase 2: levering bewijzen met file-proof (hash) van het audiobestand
    deliver_proof = (
        make_and_record(
            "file",
            path=req.filepath,
            agent="39_audio_director",
            note=f"audio geleverd: {req.asset}",
            context="audio_director_deliver",
        )
        if req.filepath
        else make_and_record(
            "report",
            id=f"audio_deliver_{req.asset}",
            agent="39_audio_director",
            context="audio_director_deliver",
        )
    )
    part_update = await notify_part_completed_async(
        part="audio",
        completed_task=req.asset,
        project=req.project,
        proof=deliver_proof,
    )
    return {
        "agent": "Audio Director",
        "agent_id": AGENT_ID,
        "delivered": req.asset,
        "filepath": str(resolved) if resolved else "",
        "part_update": part_update,
        "proof": deliver_proof,
    }
