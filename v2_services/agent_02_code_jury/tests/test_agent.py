from __future__ import annotations

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["agent"] == "02_code_jury"


def test_python_review_valid() -> None:
    code = "def hello():\n    print('world')\n"
    r = client.post("/review/python", json={"code": code})
    assert r.status_code == 200
    body = r.json()
    assert body["language"] == "python"
    assert "verdict" in body
    assert "jury" in body


def test_python_review_invalid_syntax() -> None:
    code = "def broken(\n"
    r = client.post("/review/python", json={"code": code})
    assert r.status_code == 200
    assert r.json()["jury"]["syntax"]["valid"] is False


def test_gdscript_review() -> None:
    code = 'extends Node\nfunc _ready():\n    print("test")\n'
    r = client.post("/review/gdscript", json={"code": code})
    assert r.status_code == 200
    body = r.json()
    assert body["language"] == "gdscript"
    assert body["verdict"] in ("accept", "revise", "reject")


def test_security_detects_eval_python() -> None:
    code = "eval('1+1')\n"
    r = client.post("/review/python", json={"code": code})
    assert r.status_code == 200
    sec = r.json()["jury"]["security"]
    assert sec.get("high_severity", 0) >= 0


def test_batch_review() -> None:
    payload = {
        "files": [
            {"language": "python", "code": "x = 1\n"},
            {"language": "gdscript", "code": "extends Node\nfunc _ready():\n    pass\n"},
        ]
    }
    r = client.post("/review/batch", json=payload)
    assert r.status_code == 200
    assert r.json()["count"] == 2
