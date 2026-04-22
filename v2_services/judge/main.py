from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from judge.nova_judge import NovaJudge

app = FastAPI(title="NOVA Judge", version="1.0.0")
_judge = NovaJudge()


class EvaluateRequest(BaseModel):
    task_result: Dict[str, Any]
    logs: List[str]


@app.get("/health")
def health():
    return {"status": "ok", "service": "nova-judge"}


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    return _judge.evaluate(req.task_result, req.logs)
