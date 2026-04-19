from __future__ import annotations

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json()["agent"] == "10_game_balance"


def test_stats_ok() -> None:
    r = client.post("/review/stats", json={"stat_curve": [1, 2, 3, 4]})
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_economy_ok() -> None:
    r = client.post("/review/economy", json={"income_per_hour": 100, "spend_per_hour": 40})
    assert r.status_code == 200
    assert r.json()["score"] >= 7.0


def test_difficulty_ok() -> None:
    r = client.post("/review/difficulty_curve", json={"difficulty_curve": [0.1, 0.2, 0.35, 0.5, 0.7]})
    assert r.status_code == 200
    assert "smoothness_metric" in r.json()


def test_review_aggregate() -> None:
    body = {
        "stat_curve": [1, 2, 3],
        "income_per_hour": 50,
        "spend_per_hour": 20,
        "difficulty_curve": [0.1, 0.2, 0.4, 0.8],
    }
    r = client.post("/review", json=body)
    assert r.status_code == 200
    assert "verdict" in r.json()
