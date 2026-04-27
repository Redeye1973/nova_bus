from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..core import RateLimiter

router = APIRouter(tags=["admin"])
_limiter = RateLimiter()


class RateLimitOverrideRequest(BaseModel):
    limit_per_min: int = Field(..., ge=1, le=10000)
    reason: str | None = None


@router.put("/admin/rate_limits/{build_name}/{endpoint:path}")
async def put_rate_limit_override(
    build_name: str,
    endpoint: str,
    payload: RateLimitOverrideRequest,
    request: Request,
) -> dict:
    client_host = request.client.host if request.client else ""
    if client_host not in {"127.0.0.1", "::1", "localhost"}:
        raise HTTPException(status_code=403, detail="localhost-only endpoint")
    endpoint_path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    _limiter.set_override(build_name=build_name, endpoint=endpoint_path, limit_per_min=payload.limit_per_min)
    return {
        "ok": True,
        "build_name": build_name,
        "endpoint": endpoint_path,
        "limit_per_min": payload.limit_per_min,
        "reason": payload.reason,
    }
