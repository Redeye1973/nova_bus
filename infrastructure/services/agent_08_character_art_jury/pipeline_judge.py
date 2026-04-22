"""Optional call to Nova pipeline judge (sessie 04)."""
from __future__ import annotations

import os
from typing import Any


def call_pipeline_judge(task_result: dict[str, Any], agent_tag: str) -> dict[str, Any] | None:
    base = (os.environ.get("NOVA_JUDGE_URL") or "").strip()
    if not base:
        return None
    logs = ["entrypoint=v1", "dispatch=v2", f"agent={agent_tag}"]
    try:
        import httpx

        with httpx.Client(timeout=8.0) as client:
            r = client.post(
                f"{base.rstrip('/')}/evaluate",
                json={"task_result": task_result, "logs": logs},
            )
            r.raise_for_status()
            return r.json()
    except Exception as exc:  # noqa: BLE001
        return {
            "verdict": "reject",
            "score": 0.0,
            "errors": [f"pipeline_judge_unreachable:{type(exc).__name__}:{exc!s}"[:200]],
            "fix_prompt": "",
        }
