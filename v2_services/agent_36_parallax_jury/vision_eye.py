"""NOVA vision eye — shared Ollama VL analysis against art_direction_bible."""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

import httpx
import yaml

def _ollama_generate_url() -> str:
    base = os.getenv("OLLAMA_URL", "").strip()
    if base:
        return base if base.endswith("/api/generate") else base.rstrip("/") + "/api/generate"
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/generate"


OLLAMA_URL = _ollama_generate_url()
DEFAULT_VISION_MODEL = os.getenv("NOVA_VISION_MODEL", "qwen2.5vl:7b")
BIBLE_PATH = Path(
    os.getenv(
        "NOVA_ART_DIRECTION_BIBLE",
        r"L:\!Nova V2\config\art_direction_bible.yaml",
    )
)
FALLBACK_BIBLE = Path(r"L:\ZZZZZ ZZ 31-05-2026\agents\art_direction_bible.yaml")
REFERENCES_DIR = Path(os.getenv("NOVA_REFERENCES_DIR", r"L:\!Nova V2\references\shmup"))


def load_bible() -> dict[str, Any]:
    for path in (BIBLE_PATH, FALLBACK_BIBLE):
        if path.is_file():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except Exception:
                continue
    return {}


def image_to_base64(image_path: str | Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _jury_rules_text(bible: dict[str, Any], jury_type: str) -> str:
    metrics = bible.get("jury_metrics", {}).get(jury_type, [])
    extra: dict[str, Any] = {}
    if jury_type == "parallax_jury":
        extra["parallax"] = bible.get("parallax", {})
    elif jury_type == "sprite_jury":
        extra["sprites"] = bible.get("sprites", {})
        extra["palette"] = bible.get("palette", {})
    # Fase 3: geleerde regels (via /feedback) tellen mee in elke jury-call
    learned = bible.get("geleerde_regels")
    if isinstance(learned, list) and learned:
        extra["geleerde_regels"] = [
            r for r in learned if isinstance(r, dict) and r.get("regel")
        ]
    ctx = {"jury_metrics": metrics, **extra}
    return yaml.dump(ctx, allow_unicode=True, default_flow_style=False)


def _parse_json_response(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


async def see(image_path: str | Path, question: str, model: str | None = None) -> str:
    """Send image + question to a vision model."""
    path = Path(image_path)
    if not path.is_file():
        return f"beeld niet gevonden: {image_path}"
    model = model or DEFAULT_VISION_MODEL
    img_b64 = image_to_base64(path)
    payload = {
        "model": model,
        "prompt": question,
        "images": [img_b64],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            return str(resp.json().get("response", ""))
    except Exception as exc:
        return f"vision_error:{type(exc).__name__}:{exc}"


async def see_with_bible(
    image_path: str | Path,
    domain: str = "shmup",
    jury_type: str = "sprite_jury",
    model: str | None = None,
) -> dict[str, Any]:
    """Score image against art_direction_bible jury metrics using vision."""
    model = model or DEFAULT_VISION_MODEL
    bible = load_bible()
    rules_text = _jury_rules_text(bible, jury_type)
    refs = list(REFERENCES_DIR.glob("ref_*.png")) if REFERENCES_DIR.is_dir() else []
    ref_hint = ", ".join(r.name for r in refs[:6]) if refs else "geen referenties geladen"

    question = f"""Je bent een visuele kwaliteitsbeoordelaar voor pixel art games
in de stijl van Raptor Call of the Shadows en Tyrian (domain: {domain}).

Beoordeel deze afbeelding tegen deze meetbare criteria:
{rules_text}

Referentie-ijkbeelden beschikbaar: {ref_hint}

Geef per criterium een score 0-10 en een korte concrete reden (noem pixels, contrast, outline, etc.).
Geef daarna een totaalscore 0-10 en verdict: accept (>=7), review (5-6), reject (<5).
Antwoord ALLEEN in JSON:
{{"criteria": {{"metric_name": {{"score": N, "reason": "..."}}}}, "total": X, "verdict": "...", "reason": "..."}}"""

    response = await see(image_path, question, model)
    parsed = _parse_json_response(response)
    return {
        "raw": response,
        "parsed": parsed,
        "model": model,
        "domain": domain,
        "jury_type": jury_type,
        "bible_loaded": bool(bible),
    }


async def compare_to_reference(
    image_path: str | Path,
    reference_path: str | Path,
    model: str | None = None,
) -> str:
    """Compare generated image against a Raptor/Tyrian reference screenshot."""
    model = model or DEFAULT_VISION_MODEL
    img_b64 = image_to_base64(image_path)
    ref_b64 = image_to_base64(reference_path)
    payload = {
        "model": model,
        "prompt": (
            "Het EERSTE beeld is gegenereerd, het TWEEDE is de Raptor/Tyrian referentie. "
            "Wat mist het eerste beeld om het niveau van de referentie te halen? "
            "Concrete punten: outline, contrast, metallic highlights, parallax-diepte, palet."
        ),
        "images": [img_b64, ref_b64],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(OLLAMA_URL, json=payload)
        resp.raise_for_status()
        return str(resp.json().get("response", ""))


async def see_bytes(png_bytes: bytes, question: str, model: str | None = None) -> str:
    """Vision query from in-memory PNG bytes."""
    model = model or DEFAULT_VISION_MODEL
    img_b64 = base64.b64encode(png_bytes).decode()
    payload = {
        "model": model,
        "prompt": question,
        "images": [img_b64],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(OLLAMA_URL, json=payload)
        resp.raise_for_status()
        return str(resp.json().get("response", ""))
