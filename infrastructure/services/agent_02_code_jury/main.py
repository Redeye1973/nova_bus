"""NOVA v2 Agent 02 — Code Jury (Python + GDScript POC)."""
from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from complexity_analyzer import analyze_gdscript, analyze_python
from judge import verdict_from_scores
from security_scanner import scan_gdscript, scan_python
from style_conformance import check_gdscript_style, check_python_style
from syntax_validator import validate_gdscript, validate_python

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("code_jury")

app = FastAPI(title="NOVA v2 Code Jury", version="0.1.0")


class CodePayload(BaseModel):
    code: str
    base64_encoded: bool = False


class BatchItem(BaseModel):
    language: Literal["python", "gdscript"]
    code: str
    path: Optional[str] = None
    base64_encoded: bool = False


class BatchPayload(BaseModel):
    files: List[BatchItem] = Field(default_factory=list)


def _decode_code(code: str, b64: bool) -> str:
    if b64:
        try:
            return base64.b64decode(code).decode("utf-8")
        except Exception as e:
            raise HTTPException(400, detail=f"base64_decode_failed:{e}") from e
    return code


def _review_python(code: str) -> Dict[str, Any]:
    syn = validate_python(code)
    comp = analyze_python(code)
    sty = check_python_style(code)
    sec = scan_python(code)
    v, fb, avg = verdict_from_scores(syn, comp, sty, sec)
    return {
        "language": "python",
        "jury": {
            "syntax": syn,
            "complexity": comp,
            "style": sty,
            "security": sec,
        },
        "verdict": v,
        "average_score": avg,
        "feedback": fb,
    }


def _review_gdscript(code: str) -> Dict[str, Any]:
    syn = validate_gdscript(code)
    comp = analyze_gdscript(code)
    sty = check_gdscript_style(code)
    sec = scan_gdscript(code)
    v, fb, avg = verdict_from_scores(syn, comp, sty, sec)
    return {
        "language": "gdscript",
        "jury": {
            "syntax": syn,
            "complexity": comp,
            "style": sty,
            "security": sec,
        },
        "verdict": v,
        "average_score": avg,
        "feedback": fb,
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "02_code_jury", "version": "0.1.0"}


@app.post("/review/python")
def review_python(payload: CodePayload) -> Dict[str, Any]:
    code = _decode_code(payload.code, payload.base64_encoded)
    return _review_python(code)


@app.post("/review/gdscript")
def review_gdscript(payload: CodePayload) -> Dict[str, Any]:
    code = _decode_code(payload.code, payload.base64_encoded)
    return _review_gdscript(code)


@app.post("/review/batch")
def review_batch(payload: BatchPayload) -> Dict[str, Any]:
    if not payload.files:
        raise HTTPException(400, detail="files_empty")
    out: List[Dict[str, Any]] = []
    for item in payload.files:
        code = _decode_code(item.code, item.base64_encoded)
        if item.language == "python":
            r = _review_python(code)
        else:
            r = _review_gdscript(code)
        if item.path:
            r["path"] = item.path
        out.append(r)
    return {"results": out, "count": len(out)}


class UnifiedReview(BaseModel):
    language: Literal["python", "gdscript"]
    code: str
    base64_encoded: bool = False


@app.post("/review")
def review_unified(body: UnifiedReview) -> Dict[str, Any]:
    code = _decode_code(body.code, body.base64_encoded)
    if body.language == "python":
        return _review_python(code)
    return _review_gdscript(code)
