"""NOVA v2 Agent 13 — PDOK Downloader (cache keys + stub fetch; real PDOK client later)."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 13 - PDOK Downloader", version="0.1.0")

CACHE_META: Dict[str, Dict[str, Any]] = {}


class DownloadBody(BaseModel):
    postcode: str = Field(..., min_length=4, max_length=12)
    layers: List[str] = Field(default_factory=lambda: ["BAG"])


def _cache_key(pc: str, layers: List[str]) -> str:
    raw = json.dumps({"postcode": pc.upper(), "layers": sorted(layers)}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "13_pdok_downloader", "version": "0.1.0"}


@app.post("/download")
def download(body: DownloadBody) -> Dict[str, Any]:
    layers = body.layers or ["BAG"]
    key = _cache_key(body.postcode, layers)
    rec = {
        "cache_key": key,
        "minio_bucket": "nova-pdok-cache",
        "object_prefix": f"pdok/{body.postcode.upper()}/{key}/",
        "layers": layers,
        "delta_detected": False,
        "fetched_at": time.time(),
        "note": "Stub response — replace with PDOK REST + MinIO put_object.",
    }
    CACHE_META[key] = rec
    return rec


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    if body.get("postcode"):
        return download(DownloadBody.model_validate(body))
    return {"hint": "POST /download or invoke with postcode + layers", "keys": list(body.keys())}
