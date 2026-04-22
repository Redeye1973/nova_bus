"""NOVA v2 Agent 12 — Bake Orchestrator (in-memory job state; Postgres DDL in scripts/)."""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 12 - Bake Orchestrator", version="0.1.0")

JobState = Literal["queued", "pdok", "qgis", "blender", "done", "failed"]

JOBS: Dict[str, Dict[str, Any]] = {}


class CreateJob(BaseModel):
    postcode: str = Field(..., min_length=4, max_length=12)
    layers: List[str] = Field(default_factory=list)


def _advance(job: Dict[str, Any]) -> None:
    order: List[JobState] = ["queued", "pdok", "qgis", "blender", "done"]
    cur = job["state"]
    if cur == "failed" or cur == "done":
        return
    i = order.index(cur)  # type: ignore[arg-type]
    if i + 1 < len(order):
        job["state"] = order[i + 1]
        job["progress"] = min(100, (i + 1) * 25)
    job["updated_at"] = time.time()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "12_bake_orchestrator", "version": "0.1.0"}


@app.post("/bake/jobs")
def create_job(body: CreateJob) -> Dict[str, Any]:
    jid = str(uuid.uuid4())
    now = time.time()
    JOBS[jid] = {
        "job_id": jid,
        "postcode": body.postcode,
        "layers": body.layers or ["BAG"],
        "state": "queued",
        "progress": 0,
        "created_at": now,
        "updated_at": now,
        "notes": [],
    }
    return {"job_id": jid, "state": "queued"}


@app.get("/bake/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, detail="unknown_job")
    return job


@app.post("/bake/jobs/{job_id}/advance")
def advance_job(job_id: str) -> Dict[str, Any]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, detail="unknown_job")
    _advance(job)
    job.setdefault("notes", []).append(f"advanced_to:{job['state']}")
    return job


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    act = str(body.get("action", "")).lower()
    if act == "create":
        cj = CreateJob.model_validate(body.get("payload") or body)
        return create_job(cj)
    if act == "get":
        jid = body.get("job_id")
        if not jid:
            return {"error": "job_id_required"}
        return get_job(str(jid))
    if act == "advance":
        jid = body.get("job_id")
        if not jid:
            return {"error": "job_id_required"}
        return advance_job(str(jid))
    return {"hint": "action create|get|advance", "received_keys": list(body.keys())}
