from fastapi import APIRouter, Header, HTTPException, Response
from ..core import CacheStore, RateLimiter, compute_expiry
from ..models import Entity

router = APIRouter(tags=["ingest"])
_cache = CacheStore()
_limiter = RateLimiter()


@router.post("/ingest")
async def ingest(entity_payload: dict, response: Response, x_build_name: str | None = Header(default=None)) -> dict:
    build_name = str(entity_payload.get("build_name") or x_build_name or "unknown")
    result = _limiter.check(build_name=build_name, endpoint="/ingest")
    if not result.allowed:
        response.headers["Retry-After"] = str(result.retry_after)
        raise HTTPException(status_code=429, detail={"error": "rate_limit_exceeded", "limit": result.limit, "window": "1min"})
    entity = Entity.model_validate(entity_payload)
    if entity.expires_at <= entity.fetched_at:
        entity.expires_at = compute_expiry(entity.category, 30)
    _cache.upsert_entity(entity)
    return {"ok": True, "id": entity.id}
