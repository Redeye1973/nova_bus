from __future__ import annotations

from fastapi import APIRouter

from ..core import CacheStore, EventPublisher, now_utc
from ..models import FeedbackRequest

router = APIRouter(tags=["feedback"])
_cache = CacheStore()
_events = EventPublisher()


@router.post("/feedback")
async def feedback(payload: FeedbackRequest) -> dict:
    row = payload.model_dump(mode="json")
    _cache.insert_build_run(row)
    _events.emit_feedback_received({
        **row,
        "at": now_utc().isoformat(),
    })
    return {"ok": True}
