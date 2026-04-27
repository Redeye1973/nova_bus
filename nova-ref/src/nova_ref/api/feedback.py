from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ..core import CacheStore, EventPublisher, RateLimiter, now_utc
from ..models import FeedbackRequest

router = APIRouter(tags=["feedback"])
_cache = CacheStore()
_events = EventPublisher()
_limiter = RateLimiter()


@router.post("/feedback")
async def feedback(payload: FeedbackRequest, response: Response) -> dict:
    result = _limiter.check(build_name=payload.build_name, endpoint="/feedback")
    if not result.allowed:
        response.headers["Retry-After"] = str(result.retry_after)
        raise HTTPException(status_code=429, detail={"error": "rate_limit_exceeded", "limit": result.limit, "window": "1min"})
    row = payload.model_dump(mode="json")
    _cache.insert_build_run(row)
    _events.emit_feedback_received({
        **row,
        "at": now_utc().isoformat(),
    })
    return {"ok": True}
