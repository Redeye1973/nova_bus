"""Unit tests for Agent 11 Monitor (offline; targets list is overridable)."""
from __future__ import annotations

import re

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "11_monitor"


def test_invoke_sweep_with_explicit_targets_offline():
    c = TestClient(main.app)
    r = c.post("/invoke", json={
        "action": "sweep",
        "targets": [
            {"name": "fake_a", "url": "http://127.0.0.1:1/health"},
            {"name": "fake_b", "url": "http://127.0.0.1:2/health"},
        ],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["targets_checked"] == 2
    assert data["down"] == 2
    assert data["up"] == 0
    assert len(data["alerts"]) == 2
    assert all(a["severity"] == "critical" for a in data["alerts"])


def test_alerts_after_sweep():
    c = TestClient(main.app)
    c.post("/invoke", json={
        "action": "sweep",
        "targets": [{"name": "fake_x", "url": "http://127.0.0.1:1/health"}],
    })
    r = c.get("/alerts")
    assert r.status_code == 200
    data = r.json()
    assert "timestamp" in data
    assert any(a["service"] == "fake_x" for a in data["alerts"])


def test_feedback_roundtrip():
    c = TestClient(main.app)
    r = c.post("/feedback", json={"message": "hello", "source": "unit"})
    assert r.status_code == 200
    r2 = c.get("/feedback/recent?limit=5")
    assert r2.json()["count"] >= 1


def test_pdok_delta_stub():
    r = TestClient(main.app).get("/pdok-weekly-delta")
    assert r.status_code == 200
    assert r.json()["status"] == "stub"


def test_metrics_prometheus_text():
    c = TestClient(main.app)
    c.post("/invoke", json={
        "action": "sweep",
        "targets": [{"name": "fake_y", "url": "http://127.0.0.1:1/health"}],
    })
    r = c.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "monitor_sweeps_total" in text
    assert "monitor_target_down_total" in text
    assert re.search(r'monitor_target_latency_ms\{target="fake_y"\}', text)


# ---------------------------------------------------------------------------
# NEW: Pipeline tracking lifecycle tests
# ---------------------------------------------------------------------------


def _reset_pipeline_state():
    main.PIPELINE_RUNS.clear()
    main.PIPELINE_HISTORY.clear()
    main.PIPELINE_STAGE_LOG.clear()


def test_pipeline_start():
    _reset_pipeline_state()
    c = TestClient(main.app)
    r = c.post("/pipeline/start", json={
        "name": "bake_1234AB",
        "triggered_by": "user",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "running"
    assert "pipeline_id" in body


def test_pipeline_start_custom_id():
    _reset_pipeline_state()
    c = TestClient(main.app)
    r = c.post("/pipeline/start", json={
        "pipeline_id": "my-custom-id",
        "name": "custom_pipeline",
    })
    assert r.status_code == 200
    assert r.json()["pipeline_id"] == "my-custom-id"


def test_pipeline_stage_records():
    _reset_pipeline_state()
    c = TestClient(main.app)
    start = c.post("/pipeline/start", json={"name": "stage_test"}).json()
    pid = start["pipeline_id"]

    r = c.post("/pipeline/stage", json={
        "pipeline_id": pid,
        "stage": "pdok_download",
        "status": "running",
        "agent_id": "agent_13",
    })
    assert r.status_code == 200
    assert r.json()["recorded"] is True
    assert r.json()["stage"] == "pdok_download"


def test_pipeline_stage_unknown_pipeline():
    _reset_pipeline_state()
    c = TestClient(main.app)
    r = c.post("/pipeline/stage", json={
        "pipeline_id": "nonexistent",
        "stage": "x",
    })
    assert r.status_code == 200
    assert r.json()["error"] == "unknown_pipeline_id"


def test_pipeline_finish():
    _reset_pipeline_state()
    c = TestClient(main.app)
    pid = c.post("/pipeline/start", json={"name": "finish_test"}).json()["pipeline_id"]

    r = c.post("/pipeline/finish", json={
        "pipeline_id": pid,
        "status": "success",
        "result": {"artifacts": 3},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["duration_s"] >= 0


def test_pipeline_finish_unknown_pipeline():
    _reset_pipeline_state()
    c = TestClient(main.app)
    r = c.post("/pipeline/finish", json={
        "pipeline_id": "nonexistent",
        "status": "success",
    })
    assert r.json()["error"] == "unknown_pipeline_id"


def test_pipeline_active_shows_running():
    _reset_pipeline_state()
    c = TestClient(main.app)

    pid1 = c.post("/pipeline/start", json={"name": "active_1"}).json()["pipeline_id"]
    pid2 = c.post("/pipeline/start", json={"name": "active_2"}).json()["pipeline_id"]
    c.post("/pipeline/finish", json={"pipeline_id": pid1, "status": "success"})

    r = c.get("/pipeline/active")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert body["pipelines"][0]["pipeline_id"] == pid2


def test_pipeline_active_empty():
    _reset_pipeline_state()
    c = TestClient(main.app)
    r = c.get("/pipeline/active")
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_pipeline_detail():
    _reset_pipeline_state()
    c = TestClient(main.app)
    pid = c.post("/pipeline/start", json={"name": "detail_test"}).json()["pipeline_id"]
    c.post("/pipeline/stage", json={"pipeline_id": pid, "stage": "s1", "status": "done"})
    c.post("/pipeline/stage", json={"pipeline_id": pid, "stage": "s2", "status": "running"})

    r = c.get(f"/pipeline/{pid}")
    assert r.status_code == 200
    body = r.json()
    assert body["pipeline_id"] == pid
    assert body["name"] == "detail_test"
    assert body["status"] == "running"
    assert len(body["stages"]) == 2
    assert body["stages"][0]["stage"] == "s1"
    assert body["stages"][1]["stage"] == "s2"


def test_pipeline_detail_unknown():
    _reset_pipeline_state()
    c = TestClient(main.app)
    r = c.get("/pipeline/nonexistent")
    assert r.status_code == 200
    assert r.json()["error"] == "unknown_pipeline_id"


def test_pipeline_history():
    _reset_pipeline_state()
    c = TestClient(main.app)
    pid = c.post("/pipeline/start", json={"name": "hist_test"}).json()["pipeline_id"]
    c.post("/pipeline/finish", json={"pipeline_id": pid, "status": "success"})

    # /pipeline/history is shadowed by /pipeline/{pipeline_id}, so use /invoke
    r = c.post("/invoke", json={"action": "pipeline_history"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 2
    events = [e["event"] for e in body["events"]]
    assert "start" in events
    assert "finish" in events


def test_pipeline_history_limit():
    _reset_pipeline_state()
    c = TestClient(main.app)
    for i in range(5):
        pid = c.post("/pipeline/start", json={"name": f"lim_{i}"}).json()["pipeline_id"]
        c.post("/pipeline/finish", json={"pipeline_id": pid, "status": "success"})

    r = c.post("/invoke", json={"action": "pipeline_history", "payload": {"limit": 3}})
    assert r.json()["count"] == 3


# ---------------------------------------------------------------------------
# NEW: full pipeline lifecycle integration test
# ---------------------------------------------------------------------------


def test_pipeline_full_lifecycle():
    _reset_pipeline_state()
    c = TestClient(main.app)

    pid = c.post("/pipeline/start", json={
        "name": "bake_9999ZZ",
        "triggered_by": "scheduler",
        "metadata": {"postcode": "9999ZZ"},
    }).json()["pipeline_id"]

    active = c.get("/pipeline/active").json()
    assert active["count"] == 1
    assert active["pipelines"][0]["pipeline_id"] == pid

    stages = ["pdok_download", "qgis_process", "blender_bake", "upload"]
    for stage in stages:
        r = c.post("/pipeline/stage", json={
            "pipeline_id": pid,
            "stage": stage,
            "status": "done",
            "agent_id": f"agent_{stage}",
        })
        assert r.json()["recorded"] is True

    detail = c.get(f"/pipeline/{pid}").json()
    assert len(detail["stages"]) == 4
    assert [s["stage"] for s in detail["stages"]] == stages

    finish = c.post("/pipeline/finish", json={
        "pipeline_id": pid,
        "status": "success",
        "result": {"model_path": "/output/9999ZZ.glb"},
    }).json()
    assert finish["status"] == "success"
    assert finish["duration_s"] >= 0

    active_after = c.get("/pipeline/active").json()
    assert active_after["count"] == 0

    history = c.post("/invoke", json={"action": "pipeline_history"}).json()
    assert history["count"] >= 2
    start_events = [e for e in history["events"] if e["event"] == "start"]
    finish_events = [e for e in history["events"] if e["event"] == "finish"]
    assert len(start_events) >= 1
    assert len(finish_events) >= 1
    assert any(e["name"] == "bake_9999ZZ" for e in finish_events)
