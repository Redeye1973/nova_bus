"""NOVA v2 Agent 12 — Bake Orchestrator + H09 Asset Lineage.

In-memory job state + asset lineage tracking.
"""
from __future__ import annotations

import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 12 - Bake Orchestrator", version="0.2.0")

JobState = Literal["queued", "pdok", "qgis", "blender", "done", "failed"]

JOBS: Dict[str, Dict[str, Any]] = {}
ASSETS: Dict[str, Dict[str, Any]] = {}
LINEAGE_EDGES: Deque[Dict[str, Any]] = deque(maxlen=5000)


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


class AssetRegister(BaseModel):
    asset_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    asset_type: str = "file"
    source: Optional[str] = None
    job_id: Optional[str] = None
    agent_id: Optional[str] = None
    parent_assets: Optional[List[str]] = None
    minio_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.post("/assets/register")
def register_asset(body: AssetRegister) -> Dict[str, Any]:
    aid = body.asset_id or str(uuid.uuid4())
    now = time.time()
    asset = {
        "asset_id": aid,
        "name": body.name,
        "asset_type": body.asset_type,
        "source": body.source,
        "job_id": body.job_id,
        "agent_id": body.agent_id,
        "minio_path": body.minio_path,
        "created_at": now,
        "metadata": body.metadata or {},
    }
    ASSETS[aid] = asset

    for parent_id in (body.parent_assets or []):
        edge = {"parent": parent_id, "child": aid, "ts": now, "agent_id": body.agent_id}
        LINEAGE_EDGES.append(edge)

    return {"asset_id": aid, "registered": True}


@app.get("/assets/{asset_id}")
def get_asset(asset_id: str) -> Dict[str, Any]:
    asset = ASSETS.get(asset_id)
    if not asset:
        raise HTTPException(404, detail="unknown_asset")
    parents = [e["parent"] for e in LINEAGE_EDGES if e["child"] == asset_id]
    children = [e["child"] for e in LINEAGE_EDGES if e["parent"] == asset_id]
    return {**asset, "parents": parents, "children": children}


@app.get("/assets/{asset_id}/lineage")
def asset_lineage(asset_id: str, depth: int = 5) -> Dict[str, Any]:
    if asset_id not in ASSETS:
        raise HTTPException(404, detail="unknown_asset")

    visited = set()
    tree: List[Dict[str, Any]] = []

    def _walk_up(aid: str, d: int) -> None:
        if aid in visited or d <= 0:
            return
        visited.add(aid)
        node = ASSETS.get(aid, {"asset_id": aid, "name": "??"})
        parents = [e["parent"] for e in LINEAGE_EDGES if e["child"] == aid]
        tree.append({"asset_id": aid, "name": node.get("name"), "depth": depth - d, "parents": parents})
        for p in parents:
            _walk_up(p, d - 1)

    _walk_up(asset_id, depth)
    return {"asset_id": asset_id, "lineage": tree}


@app.get("/assets")
def list_assets(limit: int = 50, job_id: Optional[str] = None) -> Dict[str, Any]:
    items = list(ASSETS.values())
    if job_id:
        items = [a for a in items if a.get("job_id") == job_id]
    items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return {"count": len(items), "assets": items[:limit]}


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
    if act == "register_asset":
        ar = AssetRegister.model_validate(body.get("payload") or body)
        return register_asset(ar)
    if act == "assets":
        return list_assets(int(body.get("limit", 50)), body.get("job_id"))
    if act == "lineage":
        aid = body.get("asset_id")
        if not aid:
            return {"error": "asset_id_required"}
        return asset_lineage(str(aid), int(body.get("depth", 5)))
    return {"hint": "action create|get|advance|register_asset|assets|lineage"}
