from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_get_template():
    r = TestClient(app).get("/templates/build_v2_agent")
    assert r.status_code == 200
    assert "latest" in r.json()


def test_upsert_and_version():
    c = TestClient(app)
    c.post("/templates", json={"name": "custom", "body": "hello", "approved": True})
    r = c.get("/templates/custom")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# NEW: GET /templates (list all)
# ---------------------------------------------------------------------------


def test_list_templates_returns_all():
    c = TestClient(app)
    r = c.get("/templates")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 2  # at least built-in build_v2_agent + jury_review
    names = [t["name"] for t in body["templates"]]
    assert "build_v2_agent" in names
    assert "jury_review" in names


def test_list_templates_contains_expected_fields():
    c = TestClient(app)
    r = c.get("/templates")
    body = r.json()
    tmpl = body["templates"][0]
    for key in ("name", "versions", "latest_version", "approved", "runs", "success_rate"):
        assert key in tmpl, f"missing key: {key}"


# ---------------------------------------------------------------------------
# NEW: GET /prompts/search
# ---------------------------------------------------------------------------


def test_search_by_q_name_match():
    c = TestClient(app)
    r = c.get("/prompts/search", params={"q": "jury"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any("jury" in res["name"].lower() for res in body["results"])


def test_search_by_q_body_match():
    c = TestClient(app)
    r = c.get("/prompts/search", params={"q": "rubric"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any("jury_review" == res["name"] for res in body["results"])


def test_search_by_q_no_match():
    c = TestClient(app)
    r = c.get("/prompts/search", params={"q": "zzz_nonexistent_term_xyz"})
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_search_by_tag(monkeypatch):
    import main as m
    orig_templates = dict(m.TEMPLATES)
    c = TestClient(app)
    c.post("/templates", json={
        "name": "tagged_prompt",
        "body": "test body",
        "approved": True,
        "tags": ["quality", "review"],
    })
    r = c.get("/prompts/search", params={"tag": "quality"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any(res["name"] == "tagged_prompt" for res in body["results"])

    r2 = c.get("/prompts/search", params={"tag": "nonexistent_tag"})
    assert r2.json()["count"] == 0


def test_search_combined_q_and_tag():
    c = TestClient(app)
    c.post("/templates", json={
        "name": "combined_search_test",
        "body": "specialized content",
        "tags": ["alpha"],
    })
    r = c.get("/prompts/search", params={"q": "combined_search", "tag": "alpha"})
    assert r.status_code == 200
    assert r.json()["count"] >= 1

    r2 = c.get("/prompts/search", params={"q": "combined_search", "tag": "wrong_tag"})
    assert r2.json()["count"] == 0


# ---------------------------------------------------------------------------
# NEW: POST /prompts/feedback
# ---------------------------------------------------------------------------


def test_prompt_feedback_records_run():
    c = TestClient(app)
    r = c.post("/prompts/feedback", json={
        "prompt_name": "build_v2_agent",
        "version": 2,
        "success": True,
        "latency_ms": 150,
        "cost_usd": 0.003,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["recorded"] is True
    assert "run_id" in body


def test_prompt_feedback_updates_stats(monkeypatch):
    import main as m
    from collections import defaultdict, deque as dq

    monkeypatch.setattr(m, "PROMPT_RUNS", dq(maxlen=1000))
    monkeypatch.setattr(m, "PROMPT_STATS", defaultdict(
        lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0}
    ))
    c = TestClient(app)

    c.post("/prompts/feedback", json={"prompt_name": "stat_test", "success": True, "latency_ms": 100})
    c.post("/prompts/feedback", json={"prompt_name": "stat_test", "success": True, "latency_ms": 200})
    c.post("/prompts/feedback", json={"prompt_name": "stat_test", "success": False, "latency_ms": 50})

    stats = m.PROMPT_STATS["stat_test"]
    assert stats["runs"] == 3
    assert stats["successes"] == 2
    assert stats["total_latency_ms"] == 350


# ---------------------------------------------------------------------------
# NEW: GET /prompts/leaderboard
# ---------------------------------------------------------------------------


def test_prompt_leaderboard_ranking(monkeypatch):
    import main as m
    from collections import defaultdict, deque as dq

    monkeypatch.setattr(m, "PROMPT_RUNS", dq(maxlen=1000))
    monkeypatch.setattr(m, "PROMPT_STATS", defaultdict(
        lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0}
    ))
    c = TestClient(app)

    for _ in range(5):
        c.post("/prompts/feedback", json={"prompt_name": "good_prompt", "success": True, "latency_ms": 100})
    for i in range(5):
        c.post("/prompts/feedback", json={"prompt_name": "bad_prompt", "success": i < 1, "latency_ms": 300})

    r = c.get("/prompts/leaderboard")
    assert r.status_code == 200
    board = r.json()["leaderboard"]
    assert len(board) >= 2

    names = [e["name"] for e in board]
    assert names.index("good_prompt") < names.index("bad_prompt")
    assert board[0]["success_rate"] == 1.0


def test_prompt_leaderboard_limit_param(monkeypatch):
    import main as m
    from collections import defaultdict, deque as dq

    monkeypatch.setattr(m, "PROMPT_RUNS", dq(maxlen=1000))
    monkeypatch.setattr(m, "PROMPT_STATS", defaultdict(
        lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0}
    ))
    c = TestClient(app)

    for i in range(5):
        c.post("/prompts/feedback", json={"prompt_name": f"p_{i}", "success": True})

    r = c.get("/prompts/leaderboard", params={"limit": 2})
    assert len(r.json()["leaderboard"]) == 2


def test_prompt_leaderboard_empty(monkeypatch):
    import main as m
    from collections import defaultdict, deque as dq

    monkeypatch.setattr(m, "PROMPT_RUNS", dq(maxlen=1000))
    monkeypatch.setattr(m, "PROMPT_STATS", defaultdict(
        lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0}
    ))
    c = TestClient(app)
    r = c.get("/prompts/leaderboard")
    assert r.status_code == 200
    assert r.json()["leaderboard"] == []


# ---------------------------------------------------------------------------
# NEW: GET /prompts/recent
# ---------------------------------------------------------------------------


def test_prompt_recent_returns_latest_runs(monkeypatch):
    import main as m
    from collections import defaultdict, deque as dq

    monkeypatch.setattr(m, "PROMPT_RUNS", dq(maxlen=1000))
    monkeypatch.setattr(m, "PROMPT_STATS", defaultdict(
        lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0}
    ))
    c = TestClient(app)

    c.post("/prompts/feedback", json={"prompt_name": "a", "success": True})
    c.post("/prompts/feedback", json={"prompt_name": "b", "success": False})
    c.post("/prompts/feedback", json={"prompt_name": "c", "success": True})

    r = c.get("/prompts/recent")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert body["runs"][-1]["prompt_name"] == "c"


def test_prompt_recent_respects_limit(monkeypatch):
    import main as m
    from collections import defaultdict, deque as dq

    monkeypatch.setattr(m, "PROMPT_RUNS", dq(maxlen=1000))
    monkeypatch.setattr(m, "PROMPT_STATS", defaultdict(
        lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0}
    ))
    c = TestClient(app)

    for i in range(10):
        c.post("/prompts/feedback", json={"prompt_name": f"p{i}", "success": True})

    r = c.get("/prompts/recent", params={"limit": 3})
    assert r.json()["count"] == 3


# ---------------------------------------------------------------------------
# NEW: integration — feedback ➜ leaderboard ➜ recent roundtrip
# ---------------------------------------------------------------------------


def test_feedback_leaderboard_recent_integration(monkeypatch):
    import main as m
    from collections import defaultdict, deque as dq

    monkeypatch.setattr(m, "PROMPT_RUNS", dq(maxlen=1000))
    monkeypatch.setattr(m, "PROMPT_STATS", defaultdict(
        lambda: {"runs": 0, "successes": 0, "total_latency_ms": 0}
    ))
    c = TestClient(app)

    for _ in range(4):
        c.post("/prompts/feedback", json={"prompt_name": "hero", "success": True, "latency_ms": 80})
    c.post("/prompts/feedback", json={"prompt_name": "hero", "success": False, "latency_ms": 500})

    board = c.get("/prompts/leaderboard").json()["leaderboard"]
    hero = next(e for e in board if e["name"] == "hero")
    assert hero["runs"] == 5
    assert hero["success_rate"] == 0.8
    assert hero["avg_latency_ms"] == round((80 * 4 + 500) / 5)

    recent = c.get("/prompts/recent").json()
    assert recent["count"] == 5
    assert recent["runs"][-1]["success"] is False
