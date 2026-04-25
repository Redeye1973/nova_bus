"""H08: Agent Memory Service — standalone FastAPI endpoint.

Provides centralized episodic + semantic memory for all NOVA agents.
Port 8180 (internal only).
"""
from __future__ import annotations

import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Memory Service", version="0.1.0")

STORES: Dict[str, Dict[str, Any]] = {}
MAX_PER_AGENT = 1000


def _get_store(agent_id: str) -> Dict[str, Any]:
    if agent_id not in STORES:
        STORES[agent_id] = {
            "memories": deque(maxlen=MAX_PER_AGENT),
            "index": {},
        }
    return STORES[agent_id]


class StoreRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None
    importance: float = 0.5
    context: Optional[Dict[str, Any]] = None


class RecallRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    limit: int = 5
    tags: Optional[List[str]] = None
    min_importance: float = 0.0


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "memory", "version": "0.1.0"}


@app.post("/memory/store")
def memory_store(body: StoreRequest) -> Dict[str, Any]:
    store = _get_store(body.agent_id)
    mem_id = str(uuid.uuid4())
    now = time.time()
    entry = {
        "id": mem_id,
        "agent_id": body.agent_id,
        "content": body.content,
        "tags": body.tags or [],
        "importance": body.importance,
        "context": body.context or {},
        "created_at": now,
        "access_count": 0,
    }
    store["memories"].append(entry)

    words = set(body.content.lower().split())
    for tag in (body.tags or []):
        words.add(tag.lower())
    for word in words:
        store["index"].setdefault(word, []).append(mem_id)

    return {"stored": True, "id": mem_id, "agent_id": body.agent_id}


@app.post("/memory/recall")
def memory_recall(body: RecallRequest) -> Dict[str, Any]:
    store = _get_store(body.agent_id)
    query_words = set(body.query.lower().split())
    candidate_ids: Dict[str, int] = {}
    for word in query_words:
        for mid in store["index"].get(word, []):
            candidate_ids[mid] = candidate_ids.get(mid, 0) + 1
    if body.tags:
        for tag in body.tags:
            for mid in store["index"].get(tag.lower(), []):
                candidate_ids[mid] = candidate_ids.get(mid, 0) + 2

    mem_by_id = {m["id"]: m for m in store["memories"]}
    scored = []
    now = time.time()
    for mid, hits in candidate_ids.items():
        mem = mem_by_id.get(mid)
        if not mem or mem["importance"] < body.min_importance:
            continue
        recency = 1.0 / (1.0 + (now - mem["created_at"]) / 3600)
        score = hits * 2.0 + mem["importance"] + recency * 0.5
        scored.append((score, mem))
    scored.sort(key=lambda x: -x[0])

    results = []
    for score, mem in scored[:body.limit]:
        mem["access_count"] += 1
        results.append({**mem, "relevance_score": round(score, 3)})
    return {"count": len(results), "memories": results}


@app.get("/memory/agents")
def memory_agents() -> Dict[str, Any]:
    agents = []
    for agent_id, store in sorted(STORES.items()):
        agents.append({
            "agent_id": agent_id,
            "memories": len(store["memories"]),
            "index_words": len(store["index"]),
        })
    return {"agents": agents}


@app.get("/memory/{agent_id}/recent")
def memory_recent(agent_id: str, limit: int = 10) -> Dict[str, Any]:
    store = _get_store(agent_id)
    items = list(store["memories"])[-min(limit, 100):]
    return {"count": len(items), "memories": items}


@app.get("/memory/{agent_id}/summary")
def memory_summary(agent_id: str) -> Dict[str, Any]:
    store = _get_store(agent_id)
    all_tags: Dict[str, int] = {}
    for mem in store["memories"]:
        for tag in mem.get("tags", []):
            all_tags[tag] = all_tags.get(tag, 0) + 1
    return {
        "agent_id": agent_id,
        "total_memories": len(store["memories"]),
        "max_per_agent": MAX_PER_AGENT,
        "index_words": len(store["index"]),
        "top_tags": dict(sorted(all_tags.items(), key=lambda x: -x[1])[:10]),
    }


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    action = str(body.get("action", "")).lower()
    if action == "store":
        return memory_store(StoreRequest(**body.get("payload", body)))
    if action == "recall":
        return memory_recall(RecallRequest(**body.get("payload", body)))
    if action == "agents":
        return memory_agents()
    return {"error": "unknown_action", "valid": ["store", "recall", "agents"]}
