"""Shared audit logger — call from any agent to log events centrally."""

from typing import Any, Dict, Optional

import httpx

MONITOR_URL = "http://nova-v2-agent-11-monitor:8111"


async def log_audit(
    actor: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    project: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    monitor_url: str = MONITOR_URL,
) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{monitor_url}/audit", json={
                "actor": actor,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "project": project,
                "metadata": metadata,
            }, timeout=5)
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return None
