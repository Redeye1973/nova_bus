"""Shared deep health check utility for all NOVA agents."""

import shutil
from typing import Any, Dict, List, Optional

import httpx


async def deep_health_check(
    agent_name: str,
    version: str,
    db_url: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    checks: Dict[str, Any] = {
        "service": "ok",
        "agent": agent_name,
        "version": version,
        "database": "not_configured",
        "downstream": {},
        "disk_space": "unknown",
    }

    if db_url:
        try:
            import psycopg2
            conn = psycopg2.connect(db_url, connect_timeout=3)
            conn.close()
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"fail: {type(e).__name__}"

    if dependencies:
        async with httpx.AsyncClient() as client:
            for dep_url in dependencies:
                try:
                    r = await client.get(dep_url, timeout=3)
                    checks["downstream"][dep_url] = "ok" if r.status_code == 200 else f"http_{r.status_code}"
                except Exception as e:
                    checks["downstream"][dep_url] = f"unreachable: {type(e).__name__}"

    try:
        usage = shutil.disk_usage("/")
        free_gb = usage.free / 1e9
        total_gb = usage.total / 1e9
        checks["disk_space"] = f"{free_gb:.1f}GB free / {total_gb:.1f}GB total"
        if free_gb < 1:
            checks["disk_space_warn"] = True
    except Exception:
        pass

    failed = []
    if "fail" in str(checks.get("database", "")):
        failed.append("database")
    for url, status in checks.get("downstream", {}).items():
        if "ok" not in str(status):
            failed.append(url)

    if failed:
        checks["overall"] = "degraded"
        checks["failed_checks"] = failed
    else:
        checks["overall"] = "healthy"

    return checks
