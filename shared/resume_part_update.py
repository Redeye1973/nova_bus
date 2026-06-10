"""Notify Resume Agent (8141) when an agent completes a part task."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

RESUME_URL = os.getenv("RESUME_AGENT_URL", "http://127.0.0.1:8141").rstrip("/")
TIMEOUT = float(os.getenv("RESUME_PART_UPDATE_TIMEOUT", "5"))


def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT)


def get_active_project() -> str:
    with _client() as client:
        r = client.get(f"{RESUME_URL}/active")
        r.raise_for_status()
        return str(r.json().get("active_project", "") or "")


async def get_active_project_async() -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{RESUME_URL}/active")
        r.raise_for_status()
        return str(r.json().get("active_project", "") or "")


def notify_part_completed(
    *,
    part: str,
    completed_task: str,
    project: str = "",
    label: str = "",
    proof: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if completed_task and not proof:
        # Fase 2 bewijs-standaard: geen proof = geen "klaar"-claim
        return {"ok": False, "skipped": True, "reason": "proof_required"}
    project = (project or "").strip() or get_active_project()
    if not project:
        return {"ok": False, "skipped": True, "reason": "no_active_project"}
    payload: Dict[str, Any] = {
        "project": project,
        "part": part,
        "completed_task": completed_task,
    }
    if label:
        payload["label"] = label
    if proof:
        payload["proof"] = proof
    try:
        with _client() as client:
            r = client.post(f"{RESUME_URL}/part-update", json=payload)
        body: Any
        try:
            body = r.json()
        except Exception:
            body = r.text
        return {
            "ok": r.status_code == 200,
            "status_code": r.status_code,
            "payload": payload,
            "response": body,
        }
    except Exception as exc:
        return {"ok": False, "payload": payload, "error": str(exc)}


async def notify_part_completed_async(
    *,
    part: str,
    completed_task: str,
    project: str = "",
    label: str = "",
    proof: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if completed_task and not proof:
        # Fase 2 bewijs-standaard: geen proof = geen "klaar"-claim
        return {"ok": False, "skipped": True, "reason": "proof_required"}
    project = (project or "").strip()
    if not project:
        project = await get_active_project_async()
    if not project:
        return {"ok": False, "skipped": True, "reason": "no_active_project"}
    payload: Dict[str, Any] = {
        "project": project,
        "part": part,
        "completed_task": completed_task,
    }
    if label:
        payload["label"] = label
    if proof:
        payload["proof"] = proof
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(f"{RESUME_URL}/part-update", json=payload)
        body: Any
        try:
            body = r.json()
        except Exception:
            body = r.text
        return {
            "ok": r.status_code == 200,
            "status_code": r.status_code,
            "payload": payload,
            "response": body,
        }
    except Exception as exc:
        return {"ok": False, "payload": payload, "error": str(exc)}
