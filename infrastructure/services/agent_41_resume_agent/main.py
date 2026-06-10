"""NOVA v2 Agent 41 — Resume Agent (parts progress + project state)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

sys.path.insert(0, "/nova_shared")
sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from proof import make_proof, record_proof, verify_proof
except ImportError:  # pragma: no cover
    def make_proof(*_a, **_k):  # type: ignore[misc]
        return {}

    def record_proof(*_a, **_k):  # type: ignore[misc]
        return {"recorded": False, "error": "proof_module_unavailable"}

    def verify_proof(_p):  # type: ignore[misc]
        return {"ok": False, "reason": "proof_module_unavailable"}

app = FastAPI(title="Resume Agent - Agent 41", version="1.1.0")

AGENT_ID = 41
PORT = int(os.getenv("RESUME_AGENT_PORT", "8141"))
PROJECTS_FILE = Path(
    os.getenv("NOVA_PROJECTS_FILE", r"L:\!Nova V2\state\projects.json")
)


class PartUpdate(BaseModel):
    project: str
    part: str
    completed_task: str = ""
    add_task: str = ""
    label: str = ""
    proof: Optional[Dict[str, Any]] = None


def load() -> Dict[str, Any]:
    if not PROJECTS_FILE.is_file():
        return {"active_project": "", "projects": {}}
    return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))


def save(data: Dict[str, Any]) -> None:
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def calc_part_pct(part: dict) -> int:
    total = len(part.get("tasks", []))
    if total == 0:
        return 0
    done = len([t for t in part.get("done", []) if t in part.get("tasks", [])])
    return round(done / total * 100)


@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_ID, "name": "Resume Agent", "port": PORT}


@app.get("/active")
def active():
    d = load()
    return {"active_project": d.get("active_project", "")}


@app.get("/resume/{project_id}")
def resume(
    project_id: str,
    name: str = Query(""),
    domain: str = Query("shmup"),
    path: str = Query(""),
):
    """Haal projectstaat op; maak aan indien nog niet aanwezig."""
    d = load()
    if project_id not in d.setdefault("projects", {}):
        d["projects"][project_id] = {
            "name": name or project_id,
            "status": "ACTIVE",
            "domain": domain,
            "path": path,
            "parts": {},
        }
        save(d)
    return d["projects"][project_id]


@app.get("/progress/{project}")
def progress(project: str):
    d = load()
    p = d["projects"].get(project)
    if not p:
        return {"error": "project niet gevonden"}
    parts = p.get("parts", {})
    part_list = []
    for key, part in parts.items():
        pct = calc_part_pct(part)
        part_list.append(
            {
                "id": key,
                "label": part.get("label", key),
                "pct": pct,
                "done": len(part.get("done", [])),
                "total": len(part.get("tasks", [])),
                "complete": pct == 100,
            }
        )
    overall = round(sum(x["pct"] for x in part_list) / len(part_list)) if part_list else 0
    return {"project": p.get("name"), "overall_pct": overall, "parts": part_list}


@app.get("/progress-all")
def progress_all():
    d = load()
    out = []
    for key, p in d["projects"].items():
        parts = p.get("parts", {})
        if parts:
            pcts = [calc_part_pct(pt) for pt in parts.values()]
            overall = round(sum(pcts) / len(pcts)) if pcts else 0
        else:
            overall = 0
        out.append(
            {
                "id": key,
                "name": p.get("name"),
                "status": p.get("status"),
                "overall_pct": overall,
                "part_count": len(parts),
            }
        )
    return {"projects": out}


@app.post("/part-update")
def part_update(req: PartUpdate):
    verification: Dict[str, Any] = {}
    if req.completed_task:
        # Fase 2 bewijs-standaard: completed_task alleen MET geldig proof
        verification = verify_proof(req.proof)
        if not verification.get("ok"):
            # Bewust ZONDER id/path geregistreerd: deze claim faalt verificatie,
            # zodat de Monitor-steekproef hem als proof_invalid rapporteert.
            record_proof(
                {
                    "type": "report",
                    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "agent": str((req.proof or {}).get("agent") or "onbekende_agent"),
                    "invalid_claim": True,
                    "note": (
                        f"claim zonder geldig proof: {req.project}/{req.part}/"
                        f"{req.completed_task} — {verification.get('reason')}"
                    ),
                },
                context="part_update_rejected",
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "proof_required",
                    "reason": verification.get("reason", "proof ontbreekt of ongeldig"),
                    "rule": "geen proof = niet gebeurd",
                },
            )
        record_proof(dict(req.proof or {}), context=f"part_update:{req.project}/{req.part}/{req.completed_task}")
    d = load()
    p = d["projects"].get(req.project)
    if not p:
        p = d.setdefault("projects", {})[req.project] = {
            "name": req.project,
            "status": "ACTIVE",
            "domain": "shmup",
            "path": "",
            "parts": {},
        }
    part = p.setdefault("parts", {}).setdefault(
        req.part, {"label": req.part, "tasks": [], "done": []}
    )
    if req.label:
        part["label"] = req.label
    if req.add_task and req.add_task not in part["tasks"]:
        part["tasks"].append(req.add_task)
    if req.completed_task:
        if req.completed_task not in part["tasks"]:
            part["tasks"].append(req.completed_task)
        if req.completed_task not in part["done"]:
            part["done"].append(req.completed_task)
    p["last_updated"] = datetime.now(timezone.utc).isoformat()
    save(d)
    out: Dict[str, Any] = {
        "project": req.project,
        "part": req.part,
        "pct": calc_part_pct(part),
    }
    if req.completed_task:
        out["proof_verified"] = verification
        out["proof"] = make_proof(
            "file",
            path=str(PROJECTS_FILE),
            agent="41_resume_agent",
            note=f"state-update {req.project}/{req.part}/{req.completed_task}",
        )
    return out
