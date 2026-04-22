from __future__ import annotations

from typing import Any

from .nova_judge import NovaJudge


def execlog_tokens(log_lines: list[str]) -> list[str]:
    return [line.lower() for line in log_lines]


def run_with_judge(core: Any, task: dict, judge: NovaJudge | None = None) -> dict:
    judge = judge or NovaJudge()
    raw = core.run(task)
    envelope = raw if isinstance(raw, dict) else {"status": "unknown"}
    logs = envelope.get("logs")
    if not isinstance(logs, list):
        logs = task.get("logs") if isinstance(task.get("logs"), list) else []
    tokens = execlog_tokens([str(x) for x in logs])
    verdict = judge.evaluate(envelope, tokens)
    task["judge"] = verdict
    return task
