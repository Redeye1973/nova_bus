"""NOVA v2 Agent 11 — Monitor (health/status/metrics/alerts/checkpoints).

Endpoints:
- GET  /health
- GET  /status
- GET  /alerts
- GET  /metrics
- POST /feedback
- GET  /feedback/recent
- POST /pipeline/start | /pipeline/stage | /pipeline/finish
- POST /pipeline/{id}/checkpoint
- GET  /pipeline/{id}/last_checkpoint
- POST /pipeline/{id}/resume
- POST /invoke
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import sys
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import json as _json

import httpx
import psycopg2
import psycopg2.extras
import yaml
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

sys.path.insert(0, "/nova_shared")
sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from proof import read_recent_proofs, verify_proof
except ImportError:  # pragma: no cover
    def read_recent_proofs(limit: int = 50):  # type: ignore[misc]
        return []

    def verify_proof(_p):  # type: ignore[misc]
        return {"ok": False, "reason": "proof_module_unavailable"}

logger = logging.getLogger("monitor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Fase 4 agent-sanering (2026-06-10): alleen de actieve kern wordt geveegd.
# Gearchiveerde agents staan in L:\!Nova V2\_archief\ (zie nova_betrouwbaar\actieve_kern.md).
# 41/42 draaien als host-uvicorn -> via host.docker.internal.
DEFAULT_TARGETS: List[Dict[str, Any]] = [
    {"name": "sprite_jury_v2",              "url": "http://sprite-jury-v2:8101/health"},
    {"name": "agent_16_cost_guard",         "url": "http://agent-16-cost-guard:8116/health"},
    {"name": "agent_29_elevenlabs",         "url": "http://agent-29-elevenlabs:8129/health"},
    {"name": "agent_36_parallax_jury",      "url": "http://agent-36-parallax-jury:8136/health"},
    {"name": "agent_37_art_director",       "url": "http://agent-37-art-director:8137/health"},
    {"name": "agent_38_quality_inspector",  "url": "http://agent-38-quality-inspector:8138/health"},
    {"name": "agent_39_audio_director",     "url": "http://agent-39-audio-director:8139/health"},
    {"name": "agent_40_juice_inspector",    "url": "http://agent-40-juice-inspector:8140/health"},
    {"name": "agent_41_resume_agent",       "url": "http://host.docker.internal:8141/health"},
    {"name": "agent_42_parts_planner",      "url": "http://host.docker.internal:8142/health"},
    {"name": "dale_factory_worker_70",      "url": "http://host.docker.internal:8170/health"},
    {"name": "audiocraft",                  "url": "http://audiocraft:8080/health"},
]

DATABASE_URL = os.getenv("DATABASE_URL", "")
NOTIFICATION_HUB_URL = os.getenv("NOTIFICATION_HUB_URL", "http://nova-v2-notification-hub:8061")

RETRY_DELAYS = [10, 30, 90]
MAX_RETRIES = 3

GATES_CONFIG_PATH = os.getenv("GATES_CONFIG", "/config/quality_gates.yaml")
GATES: Dict[str, Any] = {}
try:
    with open(GATES_CONFIG_PATH) as f:
        GATES = yaml.safe_load(f) or {}
except FileNotFoundError:
    logger.warning("quality_gates.yaml not found, gates disabled")

LATENCY_WARN_MS = float(os.getenv("MONITOR_LATENCY_WARN_MS", "750"))
LATENCY_CRIT_MS = float(os.getenv("MONITOR_LATENCY_CRIT_MS", "2000"))
SWEEP_TIMEOUT_S = float(os.getenv("MONITOR_TIMEOUT_S", "3"))

JURY_STATS_PATH = os.getenv("NOVA_JURY_STATS_PATH", "").strip()

# Fase 2 bewijs-standaard: steekproef-verificatie van recente proofs per sweep
PROOF_SAMPLE_N = int(os.getenv("NOVA_PROOF_SAMPLE_N", "3"))
PROOF_CHECK_OUT = os.getenv("NOVA_PROOF_CHECK_PATH", "/nova_status/nova_proof_check.json").strip()


def _verify_recent_proofs() -> Dict[str, Any]:
    """Verifieer N willekeurige recente proofs (bestand bestaat, hash matcht).

    FASE 8 FIX 4 (Z3): bovenop de random steekproef worden ALLE recente job-proofs
    per sweep tegen het job-events-grootboek gecontroleerd (verify_proof doet de
    grootboek-check), zodat een gefabriceerd job-proof deterministisch binnen één
    sweep wordt geflagd in plaats van afhankelijk te zijn van steekproef-geluk."""
    recent = read_recent_proofs(limit=50)
    if not recent:
        return {"sampled": 0, "invalid": [], "available": 0}
    sample = random.sample(recent, min(PROOF_SAMPLE_N, len(recent)))
    job_proofs = [p for p in recent if p.get("type") == "job"]
    seen = {id(p) for p in sample}
    for jp in job_proofs:
        if id(jp) not in seen:
            sample.append(jp)
            seen.add(id(jp))
    invalid: List[Dict[str, Any]] = []
    checked: List[Dict[str, Any]] = []
    for proof in sample:
        verdict = verify_proof(proof)
        row = {
            "agent": proof.get("agent", "?"),
            "type": proof.get("type", "?"),
            "id": proof.get("id", ""),
            "path": proof.get("path", ""),
            "timestamp": proof.get("timestamp", ""),
            "ok": bool(verdict.get("ok")),
            "reason": verdict.get("reason", ""),
        }
        checked.append(row)
        if not verdict.get("ok"):
            invalid.append(row)
            logger.warning(
                "PROOF MISMATCH agent=%s type=%s id=%s path=%s reason=%s",
                row["agent"], row["type"], row["id"], row["path"], row["reason"],
            )
    result = {
        "sampled": len(sample),
        "available": len(recent),
        "invalid": invalid,
        "checked": checked,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if PROOF_CHECK_OUT:
        try:
            out = Path(PROOF_CHECK_OUT)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(_json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("proof check dashboard write failed")
    return result


def _default_jury_stats() -> Dict[str, Any]:
    return {
        "version": 1,
        "updated_at": None,
        "totals": {"scored_accept": 0, "scored_reject": 0, "other": 0},
        "by_jury_agent": {},
        "by_stage_type": {},
        "recent": [],
    }


def _load_jury_stats() -> Dict[str, Any]:
    if not JURY_STATS_PATH:
        return _default_jury_stats()
    p = Path(JURY_STATS_PATH)
    if not p.is_file():
        return _default_jury_stats()
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("failed to load jury stats")
        return _default_jury_stats()


def _save_jury_stats(data: Dict[str, Any]) -> None:
    if not JURY_STATS_PATH:
        return
    p = Path(JURY_STATS_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(_json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(p)


def _record_gate_verdict(
    category: str,
    stage_type: str,
    jury_agent: Optional[str],
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """Write gate / jury outcomes to host-mounted JSON for the Nova dashboard."""
    if not JURY_STATS_PATH:
        return
    try:
        data = _load_jury_stats()
        totals = data.setdefault("totals", {"scored_accept": 0, "scored_reject": 0, "other": 0})
        if category == "scored_accept":
            totals["scored_accept"] = int(totals.get("scored_accept", 0)) + 1
        elif category == "scored_reject":
            totals["scored_reject"] = int(totals.get("scored_reject", 0)) + 1
        else:
            totals["other"] = int(totals.get("other", 0)) + 1

        if jury_agent:
            bja = data.setdefault("by_jury_agent", {})
            if isinstance(bja, dict):
                key = str(jury_agent)
                cur = bja.get(key, {})
                if not isinstance(cur, dict):
                    cur = {}
                slot = "accept" if category == "scored_accept" else ("reject" if category == "scored_reject" else "other")
                cur[slot] = int(cur.get(slot, 0)) + 1
                bja[key] = cur

        bst = data.setdefault("by_stage_type", {})
        if isinstance(bst, dict):
            st = str(stage_type)
            cur2 = bst.get(st, {})
            if not isinstance(cur2, dict):
                cur2 = {}
            slot2 = "accept" if category == "scored_accept" else ("reject" if category == "scored_reject" else "other")
            cur2[slot2] = int(cur2.get(slot2, 0)) + 1
            bst[st] = cur2

        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "category": category,
            "stage_type": stage_type,
            "jury_agent": jury_agent or "",
            "detail": detail or {},
        }
        recent = data.setdefault("recent", [])
        if not isinstance(recent, list):
            recent = []
            data["recent"] = recent
        recent.insert(0, rec)
        data["recent"] = recent[:80]
        _save_jury_stats(data)
    except Exception:
        logger.exception("jury stats persistence failed")


class _State:
    def __init__(self) -> None:
        self.last_sweep: Optional[Dict[str, Any]] = None
        self.metrics: Dict[str, Any] = {
            "monitor_sweeps_total": 0,
            "monitor_target_up_total": 0,
            "monitor_target_down_total": 0,
            "per_target_last_latency_ms": {},
            "per_target_last_status": {},
        }


STATE = _State()
app = FastAPI(title="NOVA v2 Agent 11 - Monitor", version="0.2.0")

FEEDBACK: Deque[Dict[str, Any]] = deque(maxlen=500)


PIPELINE_RUNS: Dict[str, Dict[str, Any]] = {}
PIPELINE_HISTORY: Deque[Dict[str, Any]] = deque(maxlen=500)
PIPELINE_STAGE_LOG: Deque[Dict[str, Any]] = deque(maxlen=2000)


class InvokeBody(BaseModel):
    action: Optional[str] = None
    targets: Optional[List[Dict[str, Any]]] = None
    payload: Optional[Dict[str, Any]] = None


class FeedbackBody(BaseModel):
    message: str = Field(..., min_length=1)
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PipelineStart(BaseModel):
    pipeline_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    triggered_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PipelineStage(BaseModel):
    pipeline_id: str
    stage: str = Field(..., min_length=1)
    status: str = "running"
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PipelineFinish(BaseModel):
    pipeline_id: str
    status: str = "success"
    result: Optional[Dict[str, Any]] = None


async def _probe_one(client: httpx.AsyncClient, target: Dict[str, Any]) -> Dict[str, Any]:
    name = target.get("name", "unknown")
    url = target.get("url", "")
    started = time.perf_counter()
    rec: Dict[str, Any] = {"name": name, "url": url, "ok": False}
    try:
        r = await client.get(url, timeout=SWEEP_TIMEOUT_S)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        rec.update({
            "status_code": r.status_code,
            "ok": r.status_code < 500,
            "latency_ms": round(elapsed_ms, 2),
        })
        try:
            rec["body"] = r.json()
        except Exception:
            rec["body"] = r.text[:200]
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 2)
    return rec


def _classify(rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not rec.get("ok"):
        return {
            "severity": "critical",
            "service": rec["name"],
            "reason": rec.get("error") or f"http_{rec.get('status_code')}",
        }
    lat = float(rec.get("latency_ms", 0))
    if lat >= LATENCY_CRIT_MS:
        return {"severity": "warning", "service": rec["name"], "reason": f"latency_{int(lat)}ms"}
    if lat >= LATENCY_WARN_MS:
        return {"severity": "info", "service": rec["name"], "reason": f"latency_{int(lat)}ms"}
    return None


async def _sweep(targets: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    use = targets if targets else DEFAULT_TARGETS
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[_probe_one(client, t) for t in use])

    alerts: List[Dict[str, Any]] = []
    up = 0
    down = 0
    for rec in results:
        STATE.metrics["per_target_last_latency_ms"][rec["name"]] = rec.get("latency_ms")
        STATE.metrics["per_target_last_status"][rec["name"]] = rec.get("status_code")
        if rec.get("ok"):
            up += 1
        else:
            down += 1
        a = _classify(rec)
        if a is not None:
            alerts.append(a)

    STATE.metrics["monitor_sweeps_total"] += 1
    STATE.metrics["monitor_target_up_total"] += up
    STATE.metrics["monitor_target_down_total"] += down

    # Fase 2: proof-steekproef — mismatch wordt dashboard-alert + log
    proof_check = _verify_recent_proofs()
    for bad in proof_check.get("invalid", []):
        alerts.append(
            {
                "severity": "critical",
                "service": f"proof:{bad.get('agent', '?')}",
                "reason": f"proof_invalid:{bad.get('reason', '?')}"
                + (f" path={bad.get('path')}" if bad.get("path") else "")
                + (f" id={bad.get('id')}" if bad.get("id") else ""),
            }
        )

    summary = {
        "timestamp": time.time(),
        "targets_checked": len(results),
        "up": up,
        "down": down,
        "alerts": alerts,
        "results": results,
        "proof_check": proof_check,
    }
    STATE.last_sweep = summary
    return summary


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "11_monitor", "version": "0.3.0"}


@app.get("/health/deep")
async def health_deep() -> Dict[str, Any]:
    import shutil

    checks: Dict[str, Any] = {
        "service": "ok",
        "agent": "11_monitor",
        "version": "0.3.0",
        "database": "not_configured",
        "downstream": {},
        "disk_space": "unknown",
        "gates_loaded": bool(GATES.get("gates")),
    }

    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
            conn.close()
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"fail: {type(e).__name__}"

    dep_urls = [
        ("notification_hub", f"{NOTIFICATION_HUB_URL}/health"),
    ]
    async with httpx.AsyncClient() as client:
        for name, url in dep_urls:
            try:
                r = await client.get(url, timeout=3)
                checks["downstream"][name] = "ok" if r.status_code == 200 else f"http_{r.status_code}"
            except Exception as e:
                checks["downstream"][name] = f"unreachable: {type(e).__name__}"

    try:
        usage = shutil.disk_usage("/")
        free_gb = usage.free / 1e9
        checks["disk_space"] = f"{free_gb:.1f}GB free"
        if free_gb < 1:
            checks["disk_space_warn"] = True
    except Exception:
        pass

    failed = [k for k, v in checks["downstream"].items() if "ok" not in str(v)]
    if "fail" in str(checks.get("database", "")):
        failed.append("database")
    checks["overall"] = "degraded" if failed else "healthy"
    if failed:
        checks["failed_checks"] = failed

    return checks


@app.get("/status")
async def status() -> Dict[str, Any]:
    return await _sweep()


@app.get("/alerts")
async def alerts() -> Dict[str, Any]:
    if STATE.last_sweep is None:
        await _sweep()
    return {
        "timestamp": STATE.last_sweep["timestamp"],
        "alerts": STATE.last_sweep["alerts"],
    }


@app.post("/feedback")
def post_feedback(body: FeedbackBody) -> Dict[str, Any]:
    rec = {
        "ts": time.time(),
        "message": body.message,
        "source": body.source or "anonymous",
        "metadata": body.metadata or {},
    }
    FEEDBACK.append(rec)
    return {"stored": True, "queue_size": len(FEEDBACK)}


@app.get("/feedback/recent")
def feedback_recent(limit: int = 20) -> Dict[str, Any]:
    lim = max(1, min(200, limit))
    items = list(FEEDBACK)[-lim:]
    return {"count": len(items), "items": items}


@app.get("/pdok-weekly-delta")
def pdok_weekly_delta_stub() -> Dict[str, Any]:
    return {
        "status": "stub",
        "note": "Wire PDOK BAG/BGT delta endpoints + MinIO snapshot compare in a later build.",
    }


@app.post("/pipeline/start")
def pipeline_start(body: PipelineStart) -> Dict[str, Any]:
    import uuid as _uuid
    pid = body.pipeline_id or str(_uuid.uuid4())
    now = time.time()
    run = {
        "pipeline_id": pid,
        "name": body.name,
        "triggered_by": body.triggered_by,
        "started_at": now,
        "status": "running",
        "stages": [],
        "metadata": body.metadata or {},
    }
    PIPELINE_RUNS[pid] = run
    PIPELINE_HISTORY.append({"event": "start", "pipeline_id": pid, "name": body.name, "ts": now})
    return {"pipeline_id": pid, "status": "running"}


@app.post("/pipeline/stage")
def pipeline_stage(body: PipelineStage) -> Dict[str, Any]:
    run = PIPELINE_RUNS.get(body.pipeline_id)
    if not run:
        return {"error": "unknown_pipeline_id"}
    now = time.time()
    stage_rec = {
        "stage": body.stage,
        "status": body.status,
        "agent_id": body.agent_id,
        "ts": now,
        "metadata": body.metadata or {},
    }
    run["stages"].append(stage_rec)
    PIPELINE_STAGE_LOG.append({"pipeline_id": body.pipeline_id, **stage_rec})
    return {"recorded": True, "pipeline_id": body.pipeline_id, "stage": body.stage}


@app.post("/pipeline/finish")
def pipeline_finish(body: PipelineFinish) -> Dict[str, Any]:
    run = PIPELINE_RUNS.get(body.pipeline_id)
    if not run:
        return {"error": "unknown_pipeline_id"}
    now = time.time()
    run["status"] = body.status
    run["finished_at"] = now
    run["duration_s"] = round(now - run["started_at"], 2)
    run["result"] = body.result
    PIPELINE_HISTORY.append({
        "event": "finish", "pipeline_id": body.pipeline_id,
        "name": run["name"], "status": body.status,
        "duration_s": run["duration_s"], "ts": now,
    })
    return {"pipeline_id": body.pipeline_id, "status": body.status, "duration_s": run["duration_s"]}


@app.get("/pipeline/active")
def pipeline_active() -> Dict[str, Any]:
    active = [r for r in PIPELINE_RUNS.values() if r.get("status") == "running"]
    return {"count": len(active), "pipelines": active}


@app.get("/pipeline/{pipeline_id}")
def pipeline_detail(pipeline_id: str) -> Dict[str, Any]:
    run = PIPELINE_RUNS.get(pipeline_id)
    if not run:
        return {"error": "unknown_pipeline_id"}
    return run


@app.get("/pipeline/history")
def pipeline_history_list(limit: int = 20) -> Dict[str, Any]:
    items = list(PIPELINE_HISTORY)[-min(limit, 200):]
    return {"count": len(items), "events": items}


def _get_db():
    if not DATABASE_URL:
        return None
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception:
        return None


class CheckpointBody(BaseModel):
    stage_name: str
    stage_index: int = 0
    stage_state: Optional[Dict[str, Any]] = None
    output_refs: Optional[Dict[str, Any]] = None


class ResumeBody(BaseModel):
    triggered_by: Optional[str] = None


@app.post("/pipeline/{pipeline_id}/checkpoint")
def save_checkpoint(pipeline_id: str, body: CheckpointBody) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"error": "database_unavailable"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO pipeline_checkpoints
                   (pipeline_run_id, stage_name, stage_index, stage_state, output_refs)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id, completed_at""",
                (pipeline_id, body.stage_name, body.stage_index,
                 psycopg2.extras.Json(body.stage_state or {}),
                 psycopg2.extras.Json(body.output_refs or {})),
            )
            row = cur.fetchone()
            conn.commit()
            return {"checkpoint_id": str(row["id"]), "pipeline_id": pipeline_id,
                    "stage": body.stage_name, "index": body.stage_index,
                    "saved_at": str(row["completed_at"])}
    finally:
        conn.close()


@app.get("/pipeline/{pipeline_id}/last_checkpoint")
def last_checkpoint(pipeline_id: str) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"error": "database_unavailable"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM pipeline_checkpoints
                   WHERE pipeline_run_id = %s AND can_resume = TRUE
                   ORDER BY stage_index DESC LIMIT 1""",
                (pipeline_id,),
            )
            row = cur.fetchone()
            if not row:
                return {"pipeline_id": pipeline_id, "checkpoint": None}
            return {"pipeline_id": pipeline_id, "checkpoint": {
                "id": str(row["id"]),
                "stage_name": row["stage_name"],
                "stage_index": row["stage_index"],
                "stage_state": row["stage_state"],
                "output_refs": row["output_refs"],
                "completed_at": str(row["completed_at"]),
            }}
    finally:
        conn.close()


@app.get("/pipeline/{pipeline_id}/checkpoints")
def list_checkpoints(pipeline_id: str) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"error": "database_unavailable"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM pipeline_checkpoints
                   WHERE pipeline_run_id = %s ORDER BY stage_index""",
                (pipeline_id,),
            )
            rows = cur.fetchall()
            return {"pipeline_id": pipeline_id, "checkpoints": [
                {"id": str(r["id"]), "stage_name": r["stage_name"],
                 "stage_index": r["stage_index"], "completed_at": str(r["completed_at"]),
                 "can_resume": r["can_resume"]}
                for r in rows
            ]}
    finally:
        conn.close()


@app.post("/pipeline/{pipeline_id}/resume")
async def resume_pipeline(pipeline_id: str, body: ResumeBody) -> Dict[str, Any]:
    cp = last_checkpoint(pipeline_id)
    if cp.get("error"):
        return cp
    if not cp.get("checkpoint"):
        return {"error": "no_checkpoint_found", "pipeline_id": pipeline_id}

    run = PIPELINE_RUNS.get(pipeline_id)
    if run:
        run["status"] = "resuming"
        run["resume_from"] = cp["checkpoint"]["stage_name"]
        run["resume_index"] = cp["checkpoint"]["stage_index"]

    PIPELINE_HISTORY.append({
        "event": "resume", "pipeline_id": pipeline_id,
        "from_stage": cp["checkpoint"]["stage_name"],
        "from_index": cp["checkpoint"]["stage_index"],
        "ts": time.time(),
    })

    return {
        "pipeline_id": pipeline_id,
        "status": "resuming",
        "from_checkpoint": cp["checkpoint"],
    }


async def _notify_failure(pipeline_id: str, stage: str, error: str, attempt: int):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{NOTIFICATION_HUB_URL}/notify", json={
                "severity": "error" if attempt < MAX_RETRIES else "critical",
                "title": f"Pipeline {stage} failed (attempt {attempt}/{MAX_RETRIES})",
                "detail": f"Pipeline: {pipeline_id}\nError: {error}",
                "source": "agent_11_monitor",
            }, timeout=5)
    except Exception:
        pass


class AuditBody(BaseModel):
    actor: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    project: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.post("/audit")
def post_audit(body: AuditBody) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"error": "database_unavailable"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO audit_log (actor, action, resource_type, resource_id, project, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, timestamp""",
                (body.actor, body.action, body.resource_type, body.resource_id,
                 body.project, psycopg2.extras.Json(body.metadata or {})),
            )
            row = cur.fetchone()
            conn.commit()
            return {"audit_id": str(row["id"]), "timestamp": str(row["timestamp"])}
    finally:
        conn.close()


@app.get("/audit")
def query_audit(actor: Optional[str] = None, resource_type: Optional[str] = None,
                since: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    conn = _get_db()
    if not conn:
        return {"error": "database_unavailable"}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            conditions = []
            params: list = []
            if actor:
                conditions.append("actor = %s")
                params.append(actor)
            if resource_type:
                conditions.append("resource_type = %s")
                params.append(resource_type)
            if since:
                conditions.append("timestamp >= %s")
                params.append(since)
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cur.execute(
                f"SELECT * FROM audit_log {where} ORDER BY timestamp DESC LIMIT %s",
                params + [min(limit, 200)],
            )
            rows = cur.fetchall()
            return {"count": len(rows), "events": [
                {**r, "id": str(r["id"]), "timestamp": str(r["timestamp"]),
                 "metadata": r.get("metadata", {})}
                for r in rows
            ]}
    finally:
        conn.close()


@app.get("/audit/recent")
def audit_recent(limit: int = 50) -> Dict[str, Any]:
    return query_audit(limit=limit)


class GateCheckBody(BaseModel):
    stage_type: str
    asset_ref: Optional[str] = None
    pipeline_id: Optional[str] = None
    profile: str = "development"
    bypass: bool = False
    metadata: Optional[Dict[str, Any]] = None


@app.get("/gates")
def list_gates() -> Dict[str, Any]:
    gates_cfg = GATES.get("gates", {})
    profiles = GATES.get("profiles", {})
    return {"gates": list(gates_cfg.keys()), "profiles": list(profiles.keys()), "loaded": bool(gates_cfg)}


@app.post("/gates/check")
async def gate_check(body: GateCheckBody) -> Dict[str, Any]:
    gates_cfg = GATES.get("gates", {})
    profiles = GATES.get("profiles", {})

    gate = gates_cfg.get(body.stage_type)
    if not gate:
        _record_gate_verdict("no_gate", body.stage_type, None, {"reason": "no_gate_configured"})
        return {"verdict": "pass", "reason": "no_gate_configured", "stage_type": body.stage_type}

    profile = profiles.get(body.profile, {})
    if profile.get("bypass_all") or body.bypass:
        _record_gate_verdict("bypass", body.stage_type, gate.get("jury_agent"), {"reason": "bypass"})
        return {"verdict": "pass", "reason": "bypass", "stage_type": body.stage_type, "profile": body.profile}

    base_threshold = gate.get("threshold", 0.7)
    modifier = profile.get("threshold_modifier", 0)
    threshold = max(0.0, min(1.0, base_threshold + modifier))

    jury_url = gate.get("jury_url", "")
    if not jury_url:
        _record_gate_verdict("no_jury_url", body.stage_type, None, {"reason": "no_jury_url"})
        return {"verdict": "pass", "reason": "no_jury_url", "stage_type": body.stage_type}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(jury_url, json={
                "action": "evaluate",
                "asset_ref": body.asset_ref,
                "pipeline_id": body.pipeline_id,
                "metadata": body.metadata or {},
            }, timeout=30)

            if r.status_code != 200:
                _record_gate_verdict(
                    "jury_http_fallback",
                    body.stage_type,
                    gate.get("jury_agent"),
                    {"http": r.status_code},
                )
                return {"verdict": "pass", "reason": f"jury_http_{r.status_code}", "stage_type": body.stage_type,
                        "fallback": True}

            result = r.json()
            score = float(result.get("score", result.get("quality_score", 0)))
            accepted = score >= threshold

            verdict_result = {
                "verdict": "accept" if accepted else "reject",
                "score": score,
                "threshold": threshold,
                "profile": body.profile,
                "stage_type": body.stage_type,
                "jury_agent": gate.get("jury_agent"),
                "jury_response": result,
            }

            if accepted:
                _record_gate_verdict(
                    "scored_accept",
                    body.stage_type,
                    gate.get("jury_agent"),
                    {"score": score, "threshold": threshold},
                )
            else:
                _record_gate_verdict(
                    "scored_reject",
                    body.stage_type,
                    gate.get("jury_agent"),
                    {"score": score, "threshold": threshold},
                )

            if not accepted and body.pipeline_id:
                await _notify_failure(body.pipeline_id, body.stage_type,
                                      f"Quality gate rejected (score={score:.2f}, threshold={threshold:.2f})", 1)

            return verdict_result

    except Exception as e:
        logger.error(f"Gate check failed for {body.stage_type}: {e}")
        bypass_on_error = gate.get("bypass_allowed", True) and profile.get("bypass_allowed", True)
        if bypass_on_error:
            _record_gate_verdict(
                "jury_error_pass",
                body.stage_type,
                gate.get("jury_agent"),
                {"error": type(e).__name__},
            )
        else:
            _record_gate_verdict(
                "jury_error_reject",
                body.stage_type,
                gate.get("jury_agent"),
                {"error": type(e).__name__},
            )
        return {
            "verdict": "pass" if bypass_on_error else "reject",
            "reason": f"jury_error: {type(e).__name__}",
            "stage_type": body.stage_type,
            "fallback": bypass_on_error,
        }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    if STATE.last_sweep is None:
        await _sweep()
    lines: List[str] = []
    lines.append("# HELP monitor_sweeps_total Total number of sweeps performed")
    lines.append("# TYPE monitor_sweeps_total counter")
    lines.append(f"monitor_sweeps_total {STATE.metrics['monitor_sweeps_total']}")
    lines.append("# HELP monitor_target_up_total Cumulative count of targets reporting up")
    lines.append("# TYPE monitor_target_up_total counter")
    lines.append(f"monitor_target_up_total {STATE.metrics['monitor_target_up_total']}")
    lines.append("# HELP monitor_target_down_total Cumulative count of targets reporting down")
    lines.append("# TYPE monitor_target_down_total counter")
    lines.append(f"monitor_target_down_total {STATE.metrics['monitor_target_down_total']}")
    lines.append("# HELP monitor_target_latency_ms Last observed latency per target")
    lines.append("# TYPE monitor_target_latency_ms gauge")
    for name, lat in STATE.metrics["per_target_last_latency_ms"].items():
        if lat is None:
            continue
        safe = name.replace('"', '\\"')
        lines.append(f'monitor_target_latency_ms{{target="{safe}"}} {lat}')
    return "\n".join(lines) + "\n"


@app.post("/invoke")
async def invoke(body: InvokeBody) -> Dict[str, Any]:
    action = (body.action or "sweep").lower()
    if action in ("sweep", "status"):
        return await _sweep(body.targets)
    if action == "alerts":
        return await alerts()
    if action == "metrics":
        return {"metrics": STATE.metrics, "last_sweep": STATE.last_sweep}
    if action == "pipeline_active":
        return pipeline_active()
    if action == "pipeline_history":
        return pipeline_history_list(int((body.payload or {}).get("limit", 20)))
    return {"error": f"unknown_action: {action}",
            "valid": ["sweep", "status", "alerts", "metrics", "pipeline_active", "pipeline_history"]}
