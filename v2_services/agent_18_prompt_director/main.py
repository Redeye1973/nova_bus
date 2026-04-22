"""NOVA v2 Agent 18 — Prompt Director (versioned in-memory templates)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="NOVA v2 Agent 18 - Prompt Director", version="0.1.0")

TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "build_v2_agent": [
        {
            "version": 1,
            "approved": True,
            "body": "You are NOVA. Implement the agent spec as FastAPI + Dockerfile + tests.",
        },
        {
            "version": 2,
            "approved": True,
            "body": "You are NOVA. Implement the agent spec; include self-heal hooks and judge wiring.",
        },
    ],
    "jury_review": [
        {"version": 1, "approved": True, "body": "Score the artifact using the rubric; return JSON verdict."},
    ],
}


class TemplateUpsert(BaseModel):
    name: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    approved: bool = False


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "18_prompt_director", "version": "0.1.0"}


@app.get("/templates/{name}")
def get_template(name: str, version: Optional[int] = None) -> Dict[str, Any]:
    versions = TEMPLATES.get(name)
    if not versions:
        raise HTTPException(404, detail=f"unknown_template:{name}")
    if version is None:
        approved = [v for v in versions if v.get("approved")]
        pick = approved[-1] if approved else versions[-1]
        return {"name": name, "latest": pick, "all_versions": len(versions)}
    for v in versions:
        if int(v.get("version", 0)) == int(version):
            return {"name": name, "template": v}
    raise HTTPException(404, detail=f"unknown_version:{version}")


@app.post("/templates")
def upsert_template(body: TemplateUpsert) -> Dict[str, Any]:
    lst = TEMPLATES.setdefault(body.name, [])
    nv = max((int(x.get("version", 0)) for x in lst), default=0) + 1
    rec = {"version": nv, "approved": body.approved, "body": body.body}
    lst.append(rec)
    return {"name": body.name, "version": nv, "approved": body.approved}


@app.post("/invoke")
def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}
    if body.get("action") == "get":
        return get_template(str(body.get("name", "")), body.get("version"))
    return {"hint": "GET /templates/{name} or invoke action get", "keys": list(body.keys())}
