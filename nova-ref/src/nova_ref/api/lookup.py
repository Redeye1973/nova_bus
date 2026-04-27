from __future__ import annotations

import time
from datetime import UTC
from fastapi import APIRouter, HTTPException
from ..core import AdapterRouter, CacheStore, EventPublisher, compute_expiry, now_utc
from ..models import Entity, LookupRequest, LookupResponse

router = APIRouter(tags=["lookup"])
_cache = CacheStore()
_router = AdapterRouter()
_events = EventPublisher()


@router.post("/lookup", response_model=LookupResponse)
async def lookup(payload: LookupRequest) -> LookupResponse:
    started = time.perf_counter()
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query cannot be empty")

    if not payload.force_refresh:
        cached = _cache.lookup_by_query(query=query, category_hint=payload.category_hint, max_age_days=payload.max_age_days)
        if cached:
            duration_ms = int((time.perf_counter() - started) * 1000)
            _cache.log_query(query, query.lower(), payload.category_hint, cached.id, 0.95, ["cache"], duration_ms)
            _events.emit_lookup_completed({
                "query": query,
                "build_name": payload.build_name,
                "category_hint": payload.category_hint,
                "entity_id": cached.id,
                "cache_hit": True,
                "adapters_tried": ["cache"],
                "duration_ms": duration_ms,
                "at": now_utc().isoformat(),
            })
            return LookupResponse(entity=cached, confidence=0.95, cache_hit=True, adapters_tried=["cache"], duration_ms=duration_ms)

    adapters = await _router.route(payload)
    tried: list[str] = []
    best: Entity | None = None
    for adapter in adapters:
        tried.append(adapter.name)
        hits = await adapter.search(query, hint={"category_hint": payload.category_hint, "build_name": payload.build_name})
        if not hits:
            continue
        raw = await adapter.fetch(hits[0]["source_id"])
        if not raw:
            continue
        raw["category"] = raw.get("category") or payload.category_hint or "general"
        ent = adapter.normalize(raw)
        ent.expires_at = compute_expiry(ent.category, payload.max_age_days)
        _cache.upsert_entity(ent)
        best = ent
        break

    duration_ms = int((time.perf_counter() - started) * 1000)
    confidence = 0.75 if best else 0.0
    _cache.log_query(query, query.lower(), payload.category_hint, best.id if best else None, confidence, tried, duration_ms)
    _events.emit_lookup_completed({
        "query": query,
        "build_name": payload.build_name,
        "category_hint": payload.category_hint,
        "entity_id": best.id if best else None,
        "cache_hit": False,
        "adapters_tried": tried,
        "duration_ms": duration_ms,
        "at": now_utc().isoformat(),
    })

    return LookupResponse(
        entity=best,
        confidence=confidence,
        cache_hit=False,
        adapters_tried=tried,
        duration_ms=duration_ms,
        suggestions=[] if best else [f"{query} specs", f"{query} dimensions"],
    )
