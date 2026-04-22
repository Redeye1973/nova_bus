"""NOVA v2 Agent 28 — Story Text Integration (in-memory canon + YAML profiles + docx ingest)."""
from __future__ import annotations

import io
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 28 - Story Text Integration", version="0.1.0")

DATA_DIR = Path(os.getenv("STORY_DATA_DIR", str(Path(__file__).resolve().parent / "data"))).resolve()
PROFILES_DIR = DATA_DIR / "profiles"

CHARACTERS: Dict[str, Dict[str, Any]] = {}
CANON_CHUNKS: List[Dict[str, Any]] = []


def _load_profiles() -> None:
    CHARACTERS.clear()
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    for p in PROFILES_DIR.glob("*.yaml"):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            name = str(data.get("name") or p.stem).strip().lower()
            if name:
                CHARACTERS[name] = dict(data)
        except Exception:
            continue


_load_profiles()


class CanonSearchBody(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=8, ge=1, le=50)


class IngestTextBody(BaseModel):
    text: str = Field(..., min_length=1)
    title: Optional[str] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "agent": "28_story_integration",
        "version": "0.1.0",
        "profiles_loaded": str(len(CHARACTERS)),
    }


@app.post("/canon/search")
def canon_search(body: CanonSearchBody) -> Dict[str, Any]:
    q = body.query.lower()
    tokens = [t for t in re.split(r"\W+", q) if len(t) > 2]
    scored: List[tuple[int, Dict[str, Any]]] = []
    for ch in CANON_CHUNKS:
        text = ch["text"].lower()
        score = sum(1 for t in tokens if t in text) + (2 if q[:32] in text else 0)
        if score > 0:
            scored.append((score, ch))
    scored.sort(key=lambda x: -x[0])
    hits = [c for _, c in scored[: body.limit]]
    return {"query": body.query, "hits": hits, "count": len(hits)}


@app.get("/character/{name}")
def character_get(name: str) -> Dict[str, Any]:
    key = name.strip().lower()
    if key not in CHARACTERS:
        raise HTTPException(404, detail="unknown_character")
    return {"name": key, "profile": CHARACTERS[key]}


@app.post("/ingest")
def ingest_text(body: IngestTextBody) -> Dict[str, Any]:
    cid = str(uuid.uuid4())
    CANON_CHUNKS.append(
        {
            "id": cid,
            "title": body.title or "untitled",
            "text": body.text,
            "ingested_at": time.time(),
        }
    )
    return {"canon_id": cid, "chars": len(body.text)}


@app.post("/ingest_docx")
async def ingest_docx(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, detail="expected_docx")
    try:
        import docx  # type: ignore
    except ImportError as exc:
        raise HTTPException(501, detail="python-docx not installed") from exc
    raw = await file.read()
    d = docx.Document(io.BytesIO(raw))
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    text = "\n".join(parts)
    if not text.strip():
        raise HTTPException(400, detail="empty_docx")
    return ingest_text(IngestTextBody(text=text, title=file.filename))
