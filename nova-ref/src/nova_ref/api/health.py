from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from ..core import AdapterRouter, query_pg_stat_activity

router = APIRouter(tags=["health"])
_router = AdapterRouter()

_g_active = Gauge("nova_ref_db_pool_active", "Active DB connections", ["service"])
_g_idle = Gauge("nova_ref_db_pool_idle", "Idle DB connections", ["service"])
_g_max = Gauge("nova_ref_db_pool_size_max", "Configured DB pool max", ["service"])


def _collect_db_stats() -> dict:
    stats = query_pg_stat_activity()
    _g_active.labels(service="nova_ref").set(stats.active)
    _g_idle.labels(service="nova_ref").set(stats.idle)
    _g_max.labels(service="nova_ref").set(stats.max_size)
    return {
        "db_connections_active": stats.active,
        "db_connections_idle": stats.idle,
        "db_pool_max": stats.max_size,
        "db_pool_utilization_percent": stats.utilization_percent,
    }


@router.get("/health")
async def health() -> dict:
    healthy = await _router.get_healthy_adapters()
    db = _collect_db_stats()
    return {"ok": len(healthy) > 0, "healthy_adapters": [a.name for a in healthy], **db}


@router.get("/ready")
async def ready() -> dict:
    db = _collect_db_stats()
    if db["db_pool_utilization_percent"] > 95.0:
        raise HTTPException(status_code=503, detail={"ok": False, **db})
    return {"ok": True, **db}


@router.get("/metrics")
async def metrics() -> Response:
    _collect_db_stats()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
