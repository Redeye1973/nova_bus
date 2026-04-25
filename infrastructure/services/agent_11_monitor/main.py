"""NOVA v2 Agent 11 — Monitor (health/status/metrics/alerts).

Scope (pragmatic POC, no Postgres/Telegram):
- Periodic and on-demand health sweep across sister agents on the
  internal Compose network.
- Prometheus-style metrics (counters + per-target latency).
- In-memory alert ledger derived from the latest sweep.

Endpoints:
- GET  /health
- GET  /status         alias of POST /invoke {"action":"sweep"}
- GET  /alerts
- GET  /metrics        plain text Prometheus exposition
- POST /feedback       user / pipeline feedback (in-memory ledger)
- GET  /feedback/recent
- GET  /pdok-weekly-delta   stub (real PDOK delta in later build)
- POST /invoke         {"action":"sweep|status|alerts|metrics"}
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional

import httpx
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("monitor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DEFAULT_TARGETS: List[Dict[str, Any]] = [
    {"name": "agent_02_code_jury",          "url": "http://agent-02-code-jury:8102/health"},
    {"name": "agent_03_audio_jury",         "url": "http://agent-03-audio-jury:8103/health"},
    {"name": "agent_04_3d_model_jury",      "url": "http://agent-04-3d-model-jury:8104/health"},
    {"name": "agent_05_gis_jury",           "url": "http://agent-05-gis-jury:8105/health"},
    {"name": "agent_06_cad_jury",           "url": "http://agent-06-cad-jury:8106/health"},
    {"name": "agent_07_narrative_jury",     "url": "http://agent-07-narrative-jury:8107/health"},
    {"name": "agent_08_character_art_jury", "url": "http://agent-08-character-art-jury:8108/health"},
    {"name": "agent_09_illustration_jury",  "url": "http://agent-09-illustration-jury:8109/health"},
    {"name": "agent_10_game_balance_jury",  "url": "http://agent-10-game-balance-jury:8110/health"},
    {"name": "agent_12_bake_orchestrator",  "url": "http://agent-12-bake-orchestrator:8112/health"},
    {"name": "agent_13_pdok_downloader",    "url": "http://agent-13-pdok-downloader:8113/health"},
    {"name": "agent_14_blender_baker",      "url": "http://agent-14-blender-baker:8114/health"},
    {"name": "agent_15_qgis_processor",     "url": "http://agent-15-qgis-processor:8115/health"},
    {"name": "agent_16_cost_guard",         "url": "http://agent-16-cost-guard:8116/health"},
    {"name": "agent_17_error_handler",      "url": "http://agent-17-error-handler:8117/health"},
    {"name": "agent_18_prompt_director",    "url": "http://agent-18-prompt-director:8118/health"},
    {"name": "agent_19_distribution",       "url": "http://agent-19-distribution:8119/health"},
    {"name": "agent_20_design_fase",        "url": "http://agent-20-design-fase:8120/health"},
    {"name": "agent_21_freecad_parametric", "url": "http://agent-21-freecad-parametric:8121/health"},
    {"name": "agent_22_blender_renderer",   "url": "http://agent-22-blender-renderer:8122/health"},
    {"name": "agent_23_aseprite_processor", "url": "http://agent-23-aseprite-processor:8123/health"},
    {"name": "agent_24_aseprite_anim_jury", "url": "http://agent-24-aseprite-anim-jury:8124/health"},
    {"name": "agent_25_pyqt_assembly",      "url": "http://agent-25-pyqt-assembly:8125/health"},
    {"name": "agent_26_godot_import",       "url": "http://agent-26-godot-import:8126/health"},
    {"name": "agent_27_storyboard",         "url": "http://agent-27-storyboard:8127/health"},
    {"name": "agent_28_story_integration",  "url": "http://agent-28-story-integration:8128/health"},
    {"name": "agent_29_elevenlabs",         "url": "http://agent-29-elevenlabs:8129/health"},
    {"name": "agent_30_audio_asset_jury",   "url": "http://agent-30-audio-asset-jury:8130/health"},
    {"name": "agent_31_qgis_analysis",      "url": "http://agent-31-qgis-analysis:8131/health"},
    {"name": "agent_32_grass_gis",          "url": "http://agent-32-grass-gis:8132/health"},
    {"name": "agent_33_blender_arch_walkthrough", "url": "http://agent-33-blender-arch-walkthrough:8133/health"},
    {"name": "agent_34_unreal_import",      "url": "http://agent-34-unreal-import:8134/health"},
    {"name": "agent_35_raster_2d",          "url": "http://agent-35-raster-2d:8135/health"},
    {"name": "sprite_jury_v2",              "url": "http://sprite-jury-v2:8101/health"},
]

LATENCY_WARN_MS = float(os.getenv("MONITOR_LATENCY_WARN_MS", "750"))
LATENCY_CRIT_MS = float(os.getenv("MONITOR_LATENCY_CRIT_MS", "2000"))
SWEEP_TIMEOUT_S = float(os.getenv("MONITOR_TIMEOUT_S", "3"))


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

    summary = {
        "timestamp": time.time(),
        "targets_checked": len(results),
        "up": up,
        "down": down,
        "alerts": alerts,
        "results": results,
    }
    STATE.last_sweep = summary
    return summary


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "11_monitor", "version": "0.2.0"}


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
