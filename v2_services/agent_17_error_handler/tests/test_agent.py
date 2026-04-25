"""Unit tests for Agent 17 Error Handler."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "17_error_handler"
    assert body["pattern_count"] >= 5


def test_report_known_pattern_ollama():
    c = TestClient(main.app)
    r = c.post("/error/report", json={
        "service": "ollama_client",
        "message": "ConnectionError to ollama on 11434",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["classification"]["category"] == "ollama_connection_refused"
    assert body["classification"]["retry_able"] is True
    assert body["retry"]["attempt"] == 1


def test_report_unknown_then_resolve_and_history():
    c = TestClient(main.app)
    r = c.post("/error/report", json={
        "service": "weird_service",
        "severity": "low",
        "message": "totally novel error nobody has seen before zzzz",
    })
    body = r.json()
    eid = body["error_id"]
    assert body["classification"]["category"] == "unknown"

    r2 = c.post("/error/resolve", json={
        "error_id": eid,
        "action": "manual_restart",
        "success": True,
        "notes": "operator reset",
    })
    assert r2.status_code == 200
    assert r2.json()["resolved"] is True

    r3 = c.get("/repair/history", params={"service": "weird_service"})
    assert r3.status_code == 200
    items = r3.json()["items"]
    kinds = [i["kind"] for i in items]
    assert "report" in kinds and "resolve" in kinds


def test_invoke_dispatch_history_after_action():
    c = TestClient(main.app)
    c.post("/invoke", json={
        "action": "report",
        "payload": {"service": "blender", "message": "MemoryError in bpy.ops"},
    })
    r = c.post("/invoke", json={"action": "history", "service": "blender"})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1


def test_invoke_unknown_action():
    c = TestClient(main.app)
    r = c.post("/invoke", json={"action": "no_such_thing"})
    assert r.status_code == 200
    assert "error" in r.json()


# ---------------------------------------------------------------------------
# NEW: GET /errors/trends
# ---------------------------------------------------------------------------


def _reset_h11_state():
    """Clear H11 state between tests for isolation."""
    main.RECENT_MESSAGES.clear()
    main.LEARNED_PATTERNS.clear()
    main.ESCALATIONS.clear()
    main.ERRORS.clear()
    main.HISTORY.clear()


def test_error_trends_empty():
    _reset_h11_state()
    c = TestClient(main.app)
    r = c.get("/errors/trends")
    assert r.status_code == 200
    body = r.json()
    assert body["total_errors"] == 0
    assert body["by_service"] == {}
    assert body["by_category"] == {}


def test_error_trends_counts_by_service_and_category():
    _reset_h11_state()
    c = TestClient(main.app)

    c.post("/error/report", json={"service": "svc_alpha", "message": "totally novel aaa"})
    c.post("/error/report", json={"service": "svc_alpha", "message": "totally novel bbb"})
    c.post("/error/report", json={"service": "svc_beta", "message": "totally novel ccc"})

    r = c.get("/errors/trends", params={"minutes": 60})
    assert r.status_code == 200
    body = r.json()
    assert body["total_errors"] == 3
    assert body["by_service"]["svc_alpha"] == 2
    assert body["by_service"]["svc_beta"] == 1


def test_error_trends_window_minutes_filters():
    _reset_h11_state()
    c = TestClient(main.app)
    c.post("/error/report", json={"service": "x", "message": "novel msg xyz"})

    r_wide = c.get("/errors/trends", params={"minutes": 9999})
    assert r_wide.json()["total_errors"] >= 1

    r_zero = c.get("/errors/trends", params={"minutes": 0})
    assert r_zero.json()["total_errors"] == 0


# ---------------------------------------------------------------------------
# NEW: GET /errors/learned (auto-learn after 3 same messages)
# ---------------------------------------------------------------------------


def test_auto_learn_after_3_identical_messages():
    _reset_h11_state()
    c = TestClient(main.app)

    msg = "OutOfMemoryError: CUDA allocation failed on device 0"
    for i in range(3):
        r = c.post("/error/report", json={"service": "gpu_worker", "message": msg})

    third = r.json()
    assert "auto_learned_pattern" in third
    learned = third["auto_learned_pattern"]
    assert learned["occurrences"] == 3

    r2 = c.get("/errors/learned")
    assert r2.status_code == 200
    body = r2.json()
    assert body["count"] >= 1
    fps = [lp["fingerprint"] for lp in body["learned_patterns"]]
    assert any(lp["count"] >= 3 for lp in body["learned_patterns"])


def test_no_auto_learn_before_3_messages():
    _reset_h11_state()
    c = TestClient(main.app)

    msg = "UniqueError that only happens twice 12345"
    r1 = c.post("/error/report", json={"service": "svc", "message": msg})
    assert "auto_learned_pattern" not in r1.json()
    r2 = c.post("/error/report", json={"service": "svc", "message": msg})
    assert "auto_learned_pattern" not in r2.json()

    learned = c.get("/errors/learned").json()
    for lp in learned["learned_patterns"]:
        if lp["count"] < 3:
            continue
        assert lp["fingerprint"] != main._normalize_message(msg)


def test_learned_patterns_list_shows_services():
    _reset_h11_state()
    c = TestClient(main.app)

    msg = "ConnectionTimeout to remote server abc"
    c.post("/error/report", json={"service": "web", "message": msg})
    c.post("/error/report", json={"service": "api", "message": msg})
    c.post("/error/report", json={"service": "worker", "message": msg})

    body = c.get("/errors/learned").json()
    pattern = next(
        lp for lp in body["learned_patterns"]
        if lp["count"] >= 3
    )
    assert set(pattern["services"]) == {"web", "api", "worker"}


# ---------------------------------------------------------------------------
# NEW: GET /errors/escalations (5+ same errors triggers escalation)
# ---------------------------------------------------------------------------


def test_escalation_triggers_after_threshold():
    _reset_h11_state()
    c = TestClient(main.app)

    for i in range(main.ESCALATION_THRESHOLD + 1):
        r = c.post("/error/report", json={
            "service": "critical_svc",
            "message": f"unique escalation error {i} qqq",
        })

    last = r.json()
    assert "escalation" in last
    assert last["escalation"]["service"] == "critical_svc"
    assert last["escalation"]["count_in_window"] >= main.ESCALATION_THRESHOLD

    esc_r = c.get("/errors/escalations")
    assert esc_r.status_code == 200
    body = esc_r.json()
    assert body["count"] >= 1
    assert any(e["service"] == "critical_svc" for e in body["escalations"])


def test_no_escalation_below_threshold():
    _reset_h11_state()
    c = TestClient(main.app)

    for i in range(main.ESCALATION_THRESHOLD - 1):
        r = c.post("/error/report", json={
            "service": "safe_svc",
            "message": f"repeated error below threshold {i} rrr",
        })
        assert "escalation" not in r.json()

    esc_r = c.get("/errors/escalations")
    assert esc_r.json()["count"] == 0


def test_escalation_list_empty_initially():
    _reset_h11_state()
    c = TestClient(main.app)
    r = c.get("/errors/escalations")
    assert r.status_code == 200
    assert r.json() == {"count": 0, "escalations": []}


# ---------------------------------------------------------------------------
# NEW: integration — report 5+ ➜ trends + learned + escalation
# ---------------------------------------------------------------------------


def test_h11_full_integration():
    _reset_h11_state()
    c = TestClient(main.app)

    msg = "Database connection pool exhausted"
    for _ in range(6):
        c.post("/error/report", json={"service": "db_pool", "message": msg})

    trends = c.get("/errors/trends").json()
    assert trends["total_errors"] >= 6
    assert "db_pool" in trends["by_service"]

    learned = c.get("/errors/learned").json()
    assert learned["count"] >= 1

    escalations = c.get("/errors/escalations").json()
    assert escalations["count"] >= 1
    assert any(e["service"] == "db_pool" for e in escalations["escalations"])
