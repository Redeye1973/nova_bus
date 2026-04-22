"""Tests for Agent 28."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["agent"] == "28_story_integration"


def test_character_example():
    c = TestClient(main.app)
    r = c.get("/character/example%20pilot")
    assert r.status_code == 200
    assert r.json()["profile"]["name"] == "Example Pilot"


def test_ingest_and_search():
    c = TestClient(main.app)
    r1 = c.post("/ingest", json={"text": "The black ledger mentions the megastructure.", "title": "note1"})
    assert r1.status_code == 200
    r2 = c.post("/canon/search", json={"query": "black ledger megastructure"})
    assert r2.status_code == 200
    assert r2.json()["count"] >= 1


def test_ingest_docx_roundtrip():
    try:
        import docx  # noqa: F401
    except ImportError:
        return
    from docx import Document

    d = Document()
    d.add_paragraph("Canon line about NOVA ships.")
    buf = io.BytesIO()
    d.save(buf)
    buf.seek(0)
    c = TestClient(main.app)
    r = c.post("/ingest_docx", files={"file": ("t.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert r.status_code == 200
    r2 = c.post("/canon/search", json={"query": "NOVA ships"})
    assert r2.status_code == 200
    assert r2.json()["count"] >= 1
