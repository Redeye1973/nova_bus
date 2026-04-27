from fastapi import APIRouter, Header, HTTPException, Response
from ..core import CacheStore, RateLimiter
from ..models import Entity

router = APIRouter(tags=["search"])
_cache = CacheStore()
_limiter = RateLimiter()


@router.post("/search")
async def search(payload: dict, response: Response, x_build_name: str | None = Header(default=None)) -> dict:
    build_name = str(payload.get("build_name") or x_build_name or "unknown")
    result = _limiter.check(build_name=build_name, endpoint="/search")
    if not result.allowed:
        response.headers["Retry-After"] = str(result.retry_after)
        raise HTTPException(status_code=429, detail={"error": "rate_limit_exceeded", "limit": result.limit, "window": "1min"})
    query = str(payload.get("query", "")).strip()
    category_hint = payload.get("category_hint")
    if not query:
        return {"candidates": []}
    hit = _cache.lookup_by_query(query, category_hint=category_hint, max_age_days=3650)
    return {"candidates": [hit.model_dump(mode="json")] if hit else []}
