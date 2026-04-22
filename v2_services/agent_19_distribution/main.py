"""NOVA v2 Agent 19 — Distribution (MinIO-oriented stub)."""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 19 - Distribution", version="0.1.0")

PUBLISHED: Dict[str, Dict[str, Any]] = {}


class PublishBody(BaseModel):
    asset_id: str = Field(..., min_length=1)
    consumer_id: str = Field(..., min_length=1)
    changelog: Optional[str] = None


def _publish_core(body: PublishBody, consumer_key: str) -> Dict[str, Any]:
    if not consumer_key:
        raise HTTPException(401, detail="missing_consumer_key")
    rid = str(uuid.uuid4())
    rec = {
        "release_id": rid,
        "asset_id": body.asset_id,
        "consumer_id": body.consumer_id,
        "bucket": "nova-distribution",
        "object_key": f"{body.consumer_id}/{body.asset_id}/{rid}.json",
        "published_at": time.time(),
        "changelog": body.changelog or "",
        "consumer_key_suffix": consumer_key[-4:] if len(consumer_key) >= 4 else "****",
    }
    PUBLISHED[rid] = rec
    return rec


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "19_distribution", "version": "0.1.0"}


@app.post("/publish")
def publish(
    body: PublishBody,
    x_consumer_key: Optional[str] = Header(default=None, alias="X-Consumer-Key"),
) -> Dict[str, Any]:
    return _publish_core(body, x_consumer_key or "")


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    key = str(body.get("X-Consumer-Key") or body.get("consumer_key") or "")
    if body.get("asset_id") and body.get("consumer_id") and key:
        return _publish_core(PublishBody.model_validate(body), key)
    return {"hint": "POST /publish with asset_id, consumer_id, X-Consumer-Key", "keys": list(body.keys())}
