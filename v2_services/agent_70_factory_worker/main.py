"""NOVA Factory Worker (Agent 70)

Universal queue worker that can:
- auto-pick jobs from a JSON folder queue
- route tool jobs to nova_host_bridge endpoints
- call other NOVA agents via /invoke
- accept Telegram commands (polling)
- write all status/results to the output directory for review
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import sys as _sys

_sys.path.insert(0, "/nova_shared")
_sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from proof import make_and_record as _make_and_record_proof
except ImportError:  # pragma: no cover
    def _make_and_record_proof(*_a, **_k):  # type: ignore[misc]
        return {}

WORKER_NAME = "Dale"
WORKER_PEER_NAME = "Tucker"
ACTIVITY_RING_MAX = 200
ACTIVITY_LOG_NAME = "dale_activity.log"
AUTO_START_WORKER = os.getenv("NOVA_FACTORY_AUTO_START", "1").strip().lower() not in (
    "0",
    "false",
    "no",
    "off",
)


def _env_path(name: str, default: str) -> Path:
    return Path(os.getenv(name, default))


JOB_DIR = _env_path("NOVA_FACTORY_JOB_DIR", r"L:\! 2 Nova v2  OUTPUT !\Dazz\NOVA_jobs")
RENDER_DIR = _env_path("NOVA_FACTORY_RENDER_DIR", r"L:\! 2 Nova v2  OUTPUT !\Dazz\NOVA_renders")
STATE_DIR = _env_path("NOVA_FACTORY_STATE_DIR", r"L:\! 2 Nova v2  OUTPUT !\Dazz\NOVA_state")
BRIDGE_URL = os.getenv("NOVA_FACTORY_BRIDGE_URL", "http://127.0.0.1:8500").rstrip("/")
POLL_INTERVAL_S = float(os.getenv("NOVA_FACTORY_POLL_INTERVAL_S", "4"))
REQUEST_TIMEOUT_S = float(os.getenv("NOVA_FACTORY_REQUEST_TIMEOUT_S", "900"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

AGENT_REGISTRY_PATH = _env_path(
    "NOVA_FACTORY_AGENT_REGISTRY",
    r"L:\! 2 Nova v2  OUTPUT !\Dazz\NOVA_jobs\factory_agents.json",
)

# Fallback registry; override via factory_agents.json
DEFAULT_AGENT_REGISTRY: Dict[str, str] = {
    "notification_hub": "http://127.0.0.1:8161/invoke",
    "bake_orchestrator": "http://127.0.0.1:8112/invoke",
    "godot_import": "http://127.0.0.1:8126/invoke",
    "qgis_analysis": "http://127.0.0.1:8131/invoke",
    "freecad_parametric": "http://127.0.0.1:8121/invoke",
    "aseprite_processor": "http://127.0.0.1:8123/invoke",
    "blender_renderer": "http://127.0.0.1:8122/invoke",
}

TOOL_ENDPOINTS: Dict[str, str] = {
    "daz": "/daz/render",
    "blender_render": "/blender/render",
    "blender_script": "/blender/script",
    "krita_export": "/krita/export",
    "aseprite_spritesheet": "/aseprite/spritesheet",
    "aseprite_script": "/aseprite/script",
    "freecad_parametric": "/freecad/parametric",
    "qgis_run": "/qgis/run",
    "godot_validate": "/godot/validate",
    "godot_script": "/godot/script",
    "godot_ai": "/godot/ai",
    "godot_import": "/godot/import",
    "pixellab_generate": "/pixellab/generate",
    "pixellab_animate": "/pixellab/animate",
    "pixellab_inpaint": "/pixellab/inpaint",
}


def _ensure_dirs() -> None:
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _activity_log_path() -> Path:
    return STATE_DIR / ACTIVITY_LOG_NAME


def _log_activity(message: str) -> None:
    line = f"{_timestamp()} {message}"
    with STATE_LOCK:
        ACTIVITY_RING.appendleft(line)
    try:
        _ensure_dirs()
        with _activity_log_path().open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def _tail_activity_log(max_lines: int = 40) -> List[str]:
    path = _activity_log_path()
    if not path.is_file():
        with STATE_LOCK:
            return list(ACTIVITY_RING)[:max_lines]
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
    except OSError:
        with STATE_LOCK:
            return list(ACTIVITY_RING)[:max_lines]


def _job_summary(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": job.get("job_id"),
        "status": job.get("status"),
        "type": job.get("type"),
        "tool": job.get("tool"),
        "agent_name": job.get("agent_name"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "error": job.get("error"),
    }


def _list_queue_jobs() -> List[Dict[str, Any]]:
    _ensure_dirs()
    rows: List[Dict[str, Any]] = []
    for job_file in sorted(JOB_DIR.glob("*.json")):
        if job_file.name == "factory_agents.json":
            continue
        try:
            raw = _read_json(job_file)
            job = _normalize_job(raw, job_file.name)
            rows.append({**_job_summary(job), "source_file": str(job_file)})
        except Exception:
            continue
    return rows


def _list_recent_results(limit: int = 8) -> List[Dict[str, Any]]:
    _ensure_dirs()
    files = sorted(
        RENDER_DIR.glob("*.result.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]
    out: List[Dict[str, Any]] = []
    for path in files:
        try:
            data = _read_json(path)
            out.append(
                {
                    "job_id": data.get("job_id"),
                    "status": data.get("status"),
                    "started_at": data.get("started_at"),
                    "ended_at": data.get("ended_at"),
                    "elapsed_ms": data.get("elapsed_ms"),
                    "error": data.get("error"),
                    "result_file": str(path),
                }
            )
        except Exception:
            continue
    return out


def _build_status_payload() -> Dict[str, Any]:
    queue_jobs = _list_queue_jobs()
    queued = [j for j in queue_jobs if str(j.get("status", "")).lower() == "queued"]
    running_jobs = [j for j in queue_jobs if str(j.get("status", "")).lower() == "running"]
    with STATE_LOCK:
        current = dict(STATE.current_job) if STATE.current_job else None
        payload = {
            "status": "ok",
            "agent": "70_factory_worker",
            "worker_name": WORKER_NAME,
            "worker_peer_name_reserved": WORKER_PEER_NAME,
            "running": STATE.running,
            "telegram_enabled": STATE.telegram_enabled,
            "job_dir": str(JOB_DIR),
            "render_dir": str(RENDER_DIR),
            "state_dir": str(STATE_DIR),
            "activity_log": str(_activity_log_path()),
            "bridge_url": BRIDGE_URL,
            "last_tick": STATE.last_tick,
            "last_tick_age_s": round(time.time() - STATE.last_tick, 1) if STATE.last_tick else None,
            "processed_total": STATE.processed_total,
            "last_error": STATE.last_error,
            "queue_depth": len(queued),
            "running_count": len(running_jobs),
            "queue_jobs": queue_jobs[:20],
            "current_job": current or (running_jobs[0] if running_jobs else None),
            "recent_results": _list_recent_results(),
            "activity_tail": _tail_activity_log(30),
            "known_tools": sorted(TOOL_ENDPOINTS.keys()),
            "known_agents": sorted(_load_registry().keys()),
        }
    return payload


def _load_registry() -> Dict[str, str]:
    if AGENT_REGISTRY_PATH.is_file():
        try:
            data = json.loads(AGENT_REGISTRY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            pass
    return dict(DEFAULT_AGENT_REGISTRY)


def _result_path(job_id: str) -> Path:
    return RENDER_DIR / f"{job_id}.result.json"


def _archive_path(job_file: Path) -> Path:
    archive = STATE_DIR / "processed"
    archive.mkdir(parents=True, exist_ok=True)
    return archive / job_file.name


def _normalize_job(job: Dict[str, Any], filename: str) -> Dict[str, Any]:
    jid = str(job.get("job_id") or Path(filename).stem)
    return {
        "job_id": jid,
        "status": str(job.get("status") or "queued").lower(),
        "type": str(job.get("type") or "bridge_tool"),
        "tool": job.get("tool"),
        "payload": job.get("payload") or {},
        "agent_name": job.get("agent_name"),
        "agent_url": job.get("agent_url"),
        "created_at": job.get("created_at") or _timestamp(),
        "raw": job,
    }


def _bridge_call(tool: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = TOOL_ENDPOINTS.get(tool)
    if not endpoint:
        raise RuntimeError(f"unsupported_tool:{tool}")
    base = BRIDGE_URL
    if tool in ("aseprite_script", "aseprite_spritesheet"):
        base = os.getenv("NOVA_ASEPRITE_BRIDGE_URL", "http://127.0.0.1:8501").rstrip("/")
    url = f"{base}{endpoint}"
    with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
        r = client.post(url, json=payload)
        body = r.json() if r.content else {}
        if r.status_code >= 400:
            raise RuntimeError(f"bridge_error:{r.status_code}:{body}")
        return body if isinstance(body, dict) else {"value": body}


def _agent_call(job: Dict[str, Any], registry: Dict[str, str]) -> Dict[str, Any]:
    agent_url = str(job.get("agent_url") or "")
    if not agent_url:
        name = str(job.get("agent_name") or "")
        agent_url = registry.get(name, "")
    if not agent_url:
        raise RuntimeError("missing_agent_url")
    payload = job.get("payload") or {}
    with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
        r = client.post(agent_url, json=payload)
        body = r.json() if r.content else {}
        if r.status_code >= 400:
            raise RuntimeError(f"agent_error:{r.status_code}:{body}")
        return body if isinstance(body, dict) else {"value": body}


def _process_job_file(job_file: Path, registry: Dict[str, str]) -> Dict[str, Any]:
    # Another tick or manual move can remove the file between glob and open.
    if not job_file.is_file():
        return {"job_id": job_file.stem, "skipped": True, "reason": "job_file_missing"}

    raw = _read_json(job_file)
    job = _normalize_job(raw, job_file.name)
    if job["status"] != "queued":
        return {"job_id": job["job_id"], "skipped": True, "reason": "status_not_queued"}

    started = time.perf_counter()
    result: Dict[str, Any] = {
        "job_id": job["job_id"],
        "started_at": _timestamp(),
        "status": "running",
        "source_file": str(job_file),
    }

    job["raw"]["status"] = "running"
    job["raw"]["started_at"] = result["started_at"]
    _write_json(job_file, job["raw"])
    with STATE_LOCK:
        STATE.current_job = _job_summary(job)
    tool_label = str(job.get("tool") or job.get("agent_name") or job.get("type") or "?")
    _log_activity(f"START job_id={job['job_id']} tool={tool_label}")

    try:
        if job["type"] == "bridge_tool":
            tool = str(job.get("tool") or "")
            if not tool:
                raise RuntimeError("missing_tool")
            payload = job.get("payload") or {}
            result["response"] = _bridge_call(tool, payload)
        elif job["type"] == "agent_invoke":
            result["response"] = _agent_call(job, registry)
        else:
            raise RuntimeError(f"unsupported_job_type:{job['type']}")

        result["status"] = "done"
        job["raw"]["status"] = "done"
        # Fase 2 bewijs-standaard: elke afgeronde job krijgt een proof-object
        payload = job.get("payload") or {}
        out_hint = str(payload.get("output_path") or payload.get("project_dir") or "")
        proof_type = "file" if payload.get("output_path") else "job"
        result["proof"] = _make_and_record_proof(
            proof_type,
            id=str(job["job_id"]),
            path=out_hint,
            agent="70_dale",
            note=f"tool={tool_label}",
            context="dale_job_done",
        )
    except Exception as exc:  # noqa: BLE001
        result["status"] = "failed"
        result["error"] = str(exc)
        job["raw"]["status"] = "failed"
        job["raw"]["error"] = str(exc)

    result["ended_at"] = _timestamp()
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    _write_json(_result_path(job["job_id"]), result)
    _write_json(job_file, job["raw"])
    job_file.replace(_archive_path(job_file))
    with STATE_LOCK:
        if STATE.current_job and STATE.current_job.get("job_id") == job["job_id"]:
            STATE.current_job = None
    if result["status"] == "done":
        _log_activity(
            f"DONE job_id={job['job_id']} tool={tool_label} elapsed_ms={result['elapsed_ms']}"
        )
    else:
        err = str(result.get("error") or "unknown")
        _log_activity(f"FAIL job_id={job['job_id']} tool={tool_label} error={err[:240]}")
        with STATE_LOCK:
            STATE.last_error = err
    return result


def _poll_telegram_once() -> Dict[str, Any]:
    if not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "reason": "telegram_not_configured"}

    offset_file = STATE_DIR / "telegram_offset.txt"
    offset = 0
    if offset_file.is_file():
        try:
            offset = int(offset_file.read_text(encoding="utf-8").strip())
        except Exception:
            offset = 0

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 1, "offset": offset + 1}
    handled = 0
    max_update = offset

    with httpx.Client(timeout=10) as client:
        r = client.get(url, params=params)
        data = r.json()

    updates = data.get("result", []) if isinstance(data, dict) else []
    for upd in updates:
        uid = int(upd.get("update_id", 0))
        max_update = max(max_update, uid)
        msg = upd.get("message") or {}
        chat = str((msg.get("chat") or {}).get("id", ""))
        text = str(msg.get("text") or "").strip()
        if not text:
            continue
        if TELEGRAM_CHAT_ID and chat != TELEGRAM_CHAT_ID:
            continue
        # Simple command format:
        # /job {"job_id":"...","type":"bridge_tool","tool":"daz","payload":{...}}
        if text.startswith("/job "):
            payload = text[5:].strip()
            try:
                job = json.loads(payload)
                if isinstance(job, dict):
                    jid = str(job.get("job_id") or f"tg-{uid}")
                    path = JOB_DIR / f"{jid}.json"
                    job["status"] = "queued"
                    _write_json(path, job)
                    handled += 1
            except Exception:
                # ignore malformed command
                pass

    if max_update > offset:
        offset_file.write_text(str(max_update), encoding="utf-8")

    return {"ok": True, "handled": handled, "updates": len(updates), "offset": max_update}


@dataclass
class WorkerState:
    running: bool = False
    last_tick: float = 0.0
    last_error: str = ""
    processed_total: int = 0
    telegram_enabled: bool = False
    current_job: Optional[Dict[str, Any]] = None


STATE = WorkerState()
STATE_LOCK = threading.Lock()
THREAD: Optional[threading.Thread] = None
ACTIVITY_RING: Deque[str] = deque(maxlen=ACTIVITY_RING_MAX)


def _tick_once() -> Dict[str, Any]:
    _ensure_dirs()
    registry = _load_registry()
    processed: list[Dict[str, Any]] = []
    for job_file in sorted(JOB_DIR.glob("*.json")):
        if job_file.name == "factory_agents.json":
            continue
        try:
            res = _process_job_file(job_file, registry)
            if not res.get("skipped"):
                processed.append(res)
        except Exception as exc:  # noqa: BLE001
            with STATE_LOCK:
                STATE.last_error = str(exc)
    tg = _poll_telegram_once() if STATE.telegram_enabled else {"ok": False, "reason": "disabled"}
    with STATE_LOCK:
        STATE.last_tick = time.time()
        STATE.processed_total += len(processed)
    return {"processed": processed, "telegram": tg}


def _worker_loop() -> None:
    while True:
        with STATE_LOCK:
            if not STATE.running:
                break
        try:
            _tick_once()
        except Exception as exc:  # noqa: BLE001
            with STATE_LOCK:
                STATE.last_error = str(exc)
        time.sleep(POLL_INTERVAL_S)


def _start_worker(telegram: bool) -> None:
    global THREAD
    with STATE_LOCK:
        if STATE.running:
            return
        STATE.running = True
        STATE.telegram_enabled = telegram
    _log_activity(f"WORKER start telegram={'on' if telegram else 'off'}")
    THREAD = threading.Thread(target=_worker_loop, daemon=True)
    THREAD.start()


def _stop_worker() -> None:
    with STATE_LOCK:
        STATE.running = False
    _log_activity("WORKER stop")


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    _ensure_dirs()
    _log_activity("SERVICE boot")
    if AUTO_START_WORKER:
        _start_worker(telegram=False)
    yield
    _stop_worker()
    _log_activity("SERVICE shutdown")


app = FastAPI(
    title=f"NOVA v2 Agent 70 - {WORKER_NAME}",
    version="0.2.0",
    lifespan=_lifespan,
)


class InvokeRequest(BaseModel):
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    job_type: Optional[str] = None


def _execute_shell(command: str) -> Dict[str, Any]:
    job_id = f"shell_{int(time.time())}"
    timeout_s = int(os.getenv("NOVA_DALE_SHELL_TIMEOUT_S", "900"))
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        status = "done" if proc.returncode == 0 else "failed"
        _log_activity(
            f"SHELL job_id={job_id} status={status} exit={proc.returncode} cmd={command[:120]}"
        )
        out: Dict[str, Any] = {
            "ok": proc.returncode == 0,
            "job_id": job_id,
            "status": status,
            "output": output,
            "exit_code": proc.returncode,
        }
        if status == "done":
            # Fase 2 bewijs-standaard: ook shell-jobs leveren een proof-object
            out["proof"] = _make_and_record_proof(
                "job",
                id=job_id,
                agent="70_dale",
                note=f"shell exit=0 cmd={command[:120]}",
                context="dale_shell_done",
            )
        return out
    except Exception as exc:  # noqa: BLE001
        _log_activity(f"SHELL job_id={job_id} status=failed error={str(exc)[:240]}")
        return {
            "ok": False,
            "job_id": job_id,
            "status": "failed",
            "output": str(exc),
        }


@app.get("/health")
def health() -> Dict[str, Any]:
    data = _build_status_payload()
    # health blijft lichtgewicht voor probes
    return {
        "status": data["status"],
        "agent": data["agent"],
        "worker_name": data["worker_name"],
        "worker_peer_name_reserved": data["worker_peer_name_reserved"],
        "running": data["running"],
        "telegram_enabled": data["telegram_enabled"],
        "job_dir": data["job_dir"],
        "render_dir": data["render_dir"],
        "state_dir": data["state_dir"],
        "activity_log": data["activity_log"],
        "bridge_url": data["bridge_url"],
        "last_tick": data["last_tick"],
        "last_tick_age_s": data["last_tick_age_s"],
        "processed_total": data["processed_total"],
        "last_error": data["last_error"],
        "queue_depth": data["queue_depth"],
        "current_job": data["current_job"],
        "known_tools": data["known_tools"],
        "known_agents": data["known_agents"],
    }


@app.get("/status")
def status() -> Dict[str, Any]:
    return _build_status_payload()


@app.post("/invoke")
def invoke(body: InvokeRequest) -> Dict[str, Any]:
    action = body.action
    payload = body.payload or {}

    if action == "start":
        _start_worker(bool(payload.get("telegram", True)))
        return {"ok": True, "running": True, "worker_name": WORKER_NAME}
    if action == "stop":
        _stop_worker()
        return {"ok": True, "running": False, "worker_name": WORKER_NAME}
    if action == "tick":
        return {"ok": True, **_tick_once()}
    if action == "submit_job":
        job = payload.get("job")
        if not isinstance(job, dict):
            raise HTTPException(400, "payload.job must be object")
        jid = str(job.get("job_id") or f"job-{int(time.time())}")
        path = JOB_DIR / f"{jid}.json"
        job["job_id"] = jid
        job["status"] = "queued"
        _write_json(path, job)
        tool_label = str(job.get("tool") or job.get("agent_name") or job.get("type") or "?")
        _log_activity(f"QUEUE job_id={jid} tool={tool_label}")
        return {"ok": True, "job_file": str(path)}
    if action == "agent_call":
        registry = _load_registry()
        job = {
            "agent_name": payload.get("agent_name"),
            "agent_url": payload.get("agent_url"),
            "payload": payload.get("payload") or {},
        }
        return {"ok": True, "response": _agent_call(job, registry)}
    if action == "telegram_poll_once":
        return {"ok": True, **_poll_telegram_once()}
    if action == "execute":
        job_type = (body.job_type or payload.get("job_type") or "").strip().lower()
        if job_type != "shell":
            raise HTTPException(400, f"unsupported job_type: {job_type or '(missing)'}")
        command = str(payload.get("command") or "").strip()
        if not command:
            raise HTTPException(400, "payload.command required")
        return {"ok": True, **_execute_shell(command)}

    raise HTTPException(400, f"Unknown action: {action}")

