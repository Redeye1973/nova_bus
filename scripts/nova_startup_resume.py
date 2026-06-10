"""NOVA gesloten startup-keten (fase 5).

Wacht tot de kernservices gezond zijn, vraagt Resume Agent 41 om het actieve
project en hervat onafgemaakte parts via de EERLIJKE orchestrator (/chat):
het antwoord komt altijd uit het job-resultaat (dale_job_id) of is een eerlijke
no_dispatch-melding — nooit een vrije LLM-claim.

Hetzner command-queue: wordt ALLEEN gepolld als de bestaande poller/webhook al
geconfigureerd is (env NOVA_HETZNER_QUEUE_URL of legacy C:\\NOVA\\nova_poller.py).
Anders: logmelding en overslaan — er wordt hier bewust NIETS nieuws gebouwd.

Gebruik: aangeroepen vanuit L:\\Nova\\start_nova.bat na het starten van de stack.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ORCHESTRATOR = os.getenv("NOVA_ORCHESTRATOR_URL", "http://127.0.0.1:8000").rstrip("/")
RESUME_AGENT = os.getenv("RESUME_AGENT_URL", "http://127.0.0.1:8141").rstrip("/")
DALE = os.getenv("NOVA_DALE_URL", "http://127.0.0.1:8170").rstrip("/")
BRIDGE = os.getenv("NOVA_FACTORY_BRIDGE_URL", "http://127.0.0.1:8500").rstrip("/")
HETZNER_QUEUE_URL = os.getenv("NOVA_HETZNER_QUEUE_URL", "").strip()
LEGACY_POLLER = Path(r"C:\NOVA\nova_poller.py")

LOG_FILE = Path(os.getenv("NOVA_STARTUP_RESUME_LOG", r"L:\!Nova V2\status\nova_startup_resume.log"))
WAIT_TOTAL_S = int(os.getenv("NOVA_STARTUP_WAIT_S", "180"))
MAX_PARTS_PER_START = int(os.getenv("NOVA_STARTUP_MAX_PARTS", "3"))


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def wait_for(name: str, url: str, deadline: float, required: bool = True) -> bool:
    while time.monotonic() < deadline:
        try:
            r = httpx.get(url, timeout=4)
            if r.status_code == 200:
                log(f"OK    {name} bereikbaar ({url})")
                return True
        except httpx.HTTPError:
            pass
        time.sleep(3)
    level = "FOUT " if required else "WAARSCHUWING"
    log(f"{level} {name} niet bereikbaar binnen wachttijd ({url})")
    return False


def open_tasks_for_part(project: str, part_id: str) -> list[str]:
    try:
        r = httpx.get(f"{RESUME_AGENT}/resume/{project}", timeout=8)
        part = (r.json().get("parts") or {}).get(part_id) or {}
        tasks = part.get("tasks") or []
        done = set(part.get("done") or [])
        return [t for t in tasks if t not in done]
    except (httpx.HTTPError, ValueError):
        return []


MAX_TASKS_PER_PART = int(os.getenv("NOVA_STARTUP_MAX_TASKS_PER_PART", "3"))


def _dispatch_chat(message: str) -> dict:
    try:
        r = httpx.post(
            f"{ORCHESTRATOR}/chat",
            json={"message": message, "agent": "dale", "stream": False},
            timeout=300,
        )
        data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "dale_status": data.get("dale_status"),
        "dale_job_id": data.get("dale_job_id") or (data.get("dale") or {}).get("job_id"),
        "reply": str(data.get("llm_response") or data.get("reply") or "")[:300],
    }


def resume_part(project: str, part: dict) -> dict:
    """Dispatch open taken van een part via de eerlijke orchestrator.

    De taaktekst zelf gaat als bericht naar /chat zodat de jobs-first routes
    en command-extractie hem kunnen oppakken; bij no_dispatch volgt een eerlijk
    antwoord zonder claim. Stopt na de eerste echte job (dale_job_id).
    """
    open_tasks = open_tasks_for_part(project, part["id"]) or [part.get("label", part["id"])]
    attempts = []
    for task in open_tasks[:MAX_TASKS_PER_PART]:
        res = _dispatch_chat(task)
        res["task"] = task
        attempts.append(res)
        log(
            f"    taak '{task[:60]}' -> status={res.get('dale_status')} "
            f"job_id={res.get('dale_job_id')}"
        )
        if res.get("dale_job_id"):
            break
    dispatched = [a for a in attempts if a.get("dale_job_id")]
    return {
        "part": part["id"],
        "ok": all(a.get("ok") for a in attempts),
        "dale_status": (dispatched[0] if dispatched else attempts[-1]).get("dale_status"),
        "dale_job_id": dispatched[0].get("dale_job_id") if dispatched else None,
        "attempts": attempts,
    }


def poll_hetzner_queue() -> None:
    if HETZNER_QUEUE_URL:
        try:
            r = httpx.get(HETZNER_QUEUE_URL, timeout=10)
            log(f"Hetzner command-queue gepolld: HTTP {r.status_code}")
        except httpx.HTTPError as exc:
            log(f"WAARSCHUWING Hetzner command-queue poll faalde: {exc}")
        return
    if LEGACY_POLLER.is_file():
        log(f"Hetzner poller aanwezig ({LEGACY_POLLER}) — wordt door start_nova.bat zelf gestart.")
        return
    log("Hetzner command-queue webhook niet geconfigureerd — overgeslagen (bewust niet gebouwd).")


def main() -> int:
    log("=== NOVA startup-resume gestart ===")
    deadline = time.monotonic() + WAIT_TOTAL_S
    ok_resume = wait_for("Resume Agent 41", f"{RESUME_AGENT}/health", deadline)
    ok_orch = wait_for("Orchestrator", f"{ORCHESTRATOR}/status", deadline)
    wait_for("Dale 70", f"{DALE}/health", deadline, required=False)
    wait_for("Host Bridge", f"{BRIDGE}/health", deadline, required=False)
    if not (ok_resume and ok_orch):
        log("GEBLOKKEERD: kernservices niet op tijd gezond — geen resume uitgevoerd.")
        return 1

    try:
        active = httpx.get(f"{RESUME_AGENT}/active", timeout=8).json().get("active_project", "")
    except (httpx.HTTPError, ValueError) as exc:
        log(f"FOUT /active onbereikbaar: {exc}")
        return 1
    if not active:
        log("Geen actief project — niets te hervatten.")
        poll_hetzner_queue()
        return 0

    try:
        progress = httpx.get(f"{RESUME_AGENT}/progress/{active}", timeout=8).json()
    except (httpx.HTTPError, ValueError) as exc:
        log(f"FOUT /progress onbereikbaar: {exc}")
        return 1
    unfinished = [p for p in progress.get("parts", []) if not p.get("complete")]
    log(f"Actief project: {active} — {len(unfinished)} onafgemaakte part(s).")

    results = []
    for part in unfinished[:MAX_PARTS_PER_START]:
        log(f"Hervatten part '{part['id']}' via eerlijke orchestrator...")
        res = resume_part(active, part)
        results.append(res)
        log(
            f"  -> status={res.get('dale_status')} job_id={res.get('dale_job_id')} "
            f"ok={res.get('ok')}"
        )
    if len(unfinished) > MAX_PARTS_PER_START:
        log(f"  ({len(unfinished) - MAX_PARTS_PER_START} part(s) wachten op volgende ronde)")

    poll_hetzner_queue()
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": active,
        "unfinished_parts": len(unfinished),
        "resumed": results,
    }
    try:
        with open(LOG_FILE.with_suffix(".jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    except OSError:
        pass
    log("=== NOVA startup-resume klaar ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
