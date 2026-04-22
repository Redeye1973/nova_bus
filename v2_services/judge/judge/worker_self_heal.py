from __future__ import annotations

from typing import Any

from .judge_hook import run_with_judge


def worker_loop_with_self_heal(core: Any, task: dict) -> dict:
    result = run_with_judge(core, task)

    if result.get("judge", {}).get("verdict") == "reject":
        retries = result.get("retry_count", 0) + 1
        result["retry_count"] = retries

        if retries > 2:
            result["status"] = "failed"
            return result

        if "pipeline" in result and len(result["pipeline"]) > 0:
            result["pipeline"][0].setdefault("input", {})["variation"] = "adjusted"

        return run_with_judge(core, result)

    return result
